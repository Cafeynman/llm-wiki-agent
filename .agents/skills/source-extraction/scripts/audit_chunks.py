from collections import Counter
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from audit_intake_file import (
    AuditArgumentError,
    AuditArgumentParser,
    DEFAULT_LARGE_SOURCE_THRESHOLD,
    UNITS_ALGO,
    content_units,
    extract_headings,
    inspect_markdown,
    normalize_markdown_text,
    read_markdown,
    reviewable_payload_characters,
)
from chunk_contract import (
    DEFAULT_SMALL_CHUNK_THRESHOLD,
    IndexRow,
    parse_index_text,
    parse_registry_text,
    registry_blocks,
    sha256_text,
)


SCHEMA_VERSION = 2
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
NUMBERED_CHILD_RE = re.compile(r"(?<!\d)(\d+)\.(\d+(?:\.\d+)*)")
NUMBERED_PARENT_RE = re.compile(r"(?<!\d)(\d+)(?![\d.])")
EXTERNAL_TARGET_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
CHUNK_PATH_COMPONENT_RE = re.compile(r"^\d{2,}$")
GENERIC_HEADING_RE = re.compile(
    r"^(?:(?:chunk|part|section|块|分块)\s*)?\d+(?:[._-]\d+)*$|^(?:续|continued)\s*\d+$",
    re.IGNORECASE,
)


def content_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def issue(code: str, path: Path, root: Path, message: str) -> dict:
    return {
        "code": code,
        "path": content_path(path, root),
        "message": message,
    }


def link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " " in target:
        target = target.split(" ", 1)[0]
    return unquote(target.strip())


def is_external_or_anchor(target: str) -> bool:
    return (
        not target
        or target.startswith("#")
        or target.startswith("data:")
        or target.startswith("mailto:")
        or target.startswith("[[")
        or EXTERNAL_TARGET_RE.match(target) is not None
    )


def local_link_targets(markdown_path: Path, pattern: re.Pattern) -> list[tuple[str, Path]]:
    text = markdown_path.read_text(encoding="utf-8")
    targets: list[tuple[str, Path]] = []
    for match in pattern.finditer(text):
        target = link_target(match.group(1))
        if is_external_or_anchor(target):
            continue
        targets.append((target, markdown_path.parent.joinpath(target).resolve()))
    return targets


def is_within(path: Path, root: Path) -> bool:
    resolved = path.resolve()
    root_resolved = root.resolve()
    return resolved == root_resolved or root_resolved in resolved.parents


def nearest_index_for(path: Path, chunks_dir: Path) -> Path | None:
    current = path.parent
    while current.resolve() == chunks_dir.resolve() or chunks_dir.resolve() in current.resolve().parents:
        candidate = current / "index.md"
        if candidate.is_file():
            return candidate
        if current.resolve() == chunks_dir.resolve():
            break
        current = current.parent
    return None


def local_heading_text(path: Path) -> str:
    try:
        headings = extract_headings(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return ""
    return " ".join(headings)


def numbered_parent_tokens(markdown_files: list[Path]) -> set[str]:
    parents: set[str] = set()
    for path in markdown_files:
        text = local_heading_text(path)
        for match in NUMBERED_PARENT_RE.finditer(text):
            parents.add(match.group(1))
    return parents


def numbered_child_warnings(markdown_files: list[Path], root: Path) -> list[dict]:
    parents = numbered_parent_tokens(markdown_files)
    warnings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for path in markdown_files:
        text = local_heading_text(path)
        for match in NUMBERED_CHILD_RE.finditer(text):
            parent = match.group(1)
            child = match.group(0)
            key = (path.as_posix(), child)
            if parent in parents or key in seen:
                continue
            seen.add(key)
            warnings.append(
                issue(
                    "possible_missing_numbered_parent",
                    path,
                    root,
                    f"numbered child heading '{child}' has no matching parent '{parent}' in chunk headings",
                )
            )
    return warnings


def chunk_child_name(path: Path) -> str:
    if path.is_file() and path.suffix.lower() == ".md":
        return path.stem
    return path.name


def content_children(directory: Path) -> list[Path]:
    children: list[Path] = []
    for child in directory.iterdir():
        if child.name == "index.md":
            continue
        if child.is_file() and child.suffix.lower() == ".md":
            children.append(child)
        elif child.is_dir():
            has_chunk_content = (child / "index.md").is_file() or any(
                descendant.is_file() and descendant.suffix.lower() == ".md"
                for descendant in child.rglob("*")
            )
            if has_chunk_content:
                children.append(child)
    return sorted(children, key=lambda path: path.name.lower())


def chunk_path_group_errors(directory: Path, root: Path) -> list[dict]:
    children = content_children(directory)
    if not children:
        return []

    noncanonical_suffixes = [
        child.name
        for child in children
        if child.is_file() and child.suffix.lower() == ".md" and child.suffix != ".md"
    ]
    if noncanonical_suffixes:
        return [
            issue(
                "invalid_chunk_markdown_suffix",
                directory,
                root,
                "chunk leaf filenames must use the exact lowercase .md suffix: "
                + ", ".join(noncanonical_suffixes[:5]),
            )
        ]

    names = [chunk_child_name(child) for child in children]
    invalid_names = [
        name
        for name in names
        if CHUNK_PATH_COMPONENT_RE.fullmatch(name) is None
        or int(name) < 1
        or name != f"{int(name):02d}"
    ]
    if invalid_names:
        return [
            issue(
                "invalid_chunk_path_component",
                directory,
                root,
                "direct chunk files and directories must use canonical numeric path components: "
                + ", ".join(invalid_names[:5]),
            )
        ]

    ordinals = sorted(int(name) for name in names)
    expected = list(range(1, len(names) + 1))
    if ordinals != expected:
        return [
            issue(
                "non_sequential_chunk_path_components",
                directory,
                root,
                "direct chunk files and directories must form one sequence starting at 01; found: "
                + ", ".join(names[:5]),
            )
        ]

    return []


def chunk_path_errors(chunks_dir: Path, root: Path) -> list[dict]:
    errors: list[dict] = []
    for directory in [chunks_dir, *[path for path in chunks_dir.rglob("*") if path.is_dir()]]:
        errors.extend(chunk_path_group_errors(directory, root))
    return errors


def repeated_source_heading_warnings(root: Path) -> list[dict]:
    source_path = root / "source.md"
    if not source_path.is_file():
        return []
    headings = extract_headings(source_path.read_text(encoding="utf-8"))
    counts = Counter(headings)
    repeated = [heading for heading, count in counts.items() if count > 1]
    if not repeated:
        return []
    return [
        issue(
            "possible_repeated_source_heading",
            source_path,
            root,
            "source.md has repeated headings that may include table-of-contents or index duplicates: "
            + " | ".join(repeated[:5]),
        )
    ]


def is_descriptive_heading(value: str) -> bool:
    normalized = re.sub(r"\s+", " ", value).strip().strip("#").strip()
    return bool(normalized) and GENERIC_HEADING_RE.fullmatch(normalized) is None


def parse_problem_issue(problem, index_path: Path, root: Path) -> dict:
    return issue(
        problem.code,
        index_path,
        root,
        f"line {problem.line}: {problem.message}",
    )


def size_kind(units: int, minimum: int, maximum: int) -> str:
    if units < minimum:
        return "under"
    if units > maximum:
        return "over"
    return "normal"


def expected_table_status(kind: str) -> set[str]:
    if kind == "under":
        return {"undersized", "accepted-under"}
    if kind == "over":
        return {"oversized", "accepted-over"}
    return {"normal"}


def threshold_issue(
    kind: str,
    code: str,
    leaf: Path,
    root: Path,
    message: str,
    errors: list[dict],
    warnings: list[dict],
) -> None:
    target = errors if kind == "over" else warnings
    target.append(issue(code, leaf, root, message))


def input_result(root: Path, minimum: int, maximum: int, code: str, message: str) -> dict:
    error = issue(code, root, root, message)
    return {
        "schema": SCHEMA_VERSION,
        "path": root.as_posix(),
        "thresholds": {"min": minimum, "max": maximum, "units_algo": UNITS_ALGO},
        "status": "fail",
        "errors": [error],
        "warnings": [],
        "accepted_exceptions": [],
        "summary": {
            "leaf_chunks": 0,
            "errors": 1,
            "warnings": 0,
            "accepted_exceptions": 0,
            "accepted_under": 0,
            "accepted_over": 0,
            "accepted_ratio": 0.0,
        },
    }


def inspect_chunks(root: Path, minimum: int, maximum: int) -> dict:
    chunks_dir = root / "chunks"
    errors: list[dict] = []
    warnings: list[dict] = []
    accepted_exceptions: list[dict] = []
    leaf_files: list[Path] = []

    source_path = root / "source.md"
    if not source_path.is_file():
        errors.append(issue("missing_source", source_path, root, "chunked intake folder has no canonical source.md"))
    else:
        source_stats = inspect_markdown(source_path, maximum)
        errors.extend(
            issue(item["code"], source_path, root, item["message"])
            for item in source_stats["errors"]
        )

    if not chunks_dir.is_dir():
        errors.append(issue("missing_chunks_dir", chunks_dir, root, "chunked intake folder has no chunks directory"))
    else:
        root_index = chunks_dir / "index.md"
        if not root_index.is_file():
            errors.append(issue("missing_chunks_index", root_index, root, "chunks/index.md is required"))
        else:
            leaf_files = sorted(path for path in chunks_dir.rglob("*.md") if path.name != "index.md")
            if not leaf_files:
                errors.append(
                    issue(
                        "empty_chunk_tree",
                        chunks_dir,
                        root,
                        "chunks contains no leaf Markdown chunks",
                    )
                )
            else:
                index_targets: dict[Path, list[Path]] = {}
                row_by_target: dict[tuple[Path, Path], IndexRow] = {}
                index_has_parse_error: set[Path] = set()

                for index_path in sorted(chunks_dir.rglob("index.md")):
                    index_text = read_markdown(index_path)
                    if index_path == root_index and not index_text.strip():
                        errors.append(issue("empty_root_index", index_path, root, "chunks/index.md is empty"))
                        index_has_parse_error.add(index_path.resolve())
                        continue
                    rows, problems = parse_index_text(index_text)
                    if index_path != root_index and registry_blocks(index_text):
                        errors.append(
                            issue(
                                "stray_chunk_exception_registry",
                                index_path,
                                root,
                                "chunk-size-exceptions registry is allowed only in the root chunks/index.md",
                            )
                        )
                    if problems:
                        index_has_parse_error.add(index_path.resolve())
                        errors.extend(parse_problem_issue(problem, index_path, root) for problem in problems)
                    resolved_targets: list[Path] = []
                    target_counts: Counter[Path] = Counter()
                    for row in rows:
                        target = link_target(row.target)
                        resolved = index_path.parent.joinpath(target).resolve()
                        resolved_targets.append(resolved)
                        target_counts[resolved] += 1
                        row_by_target.setdefault((index_path.resolve(), resolved), row)
                        target_is_nested_index = resolved.name == "index.md"
                        target_is_direct_child_index = (
                            target_is_nested_index
                            and resolved != index_path.resolve()
                            and resolved.parent.parent.resolve() == index_path.parent.resolve()
                        )
                        if row.size_status == "group" and not target_is_direct_child_index:
                            errors.append(
                                issue(
                                    "invalid_chunk_group_decision",
                                    index_path,
                                    root,
                                    f"group row must link to a direct child directory's index.md: {row.target}",
                                )
                            )
                        elif row.size_status != "group" and target_is_nested_index:
                            errors.append(
                                issue(
                                    "invalid_chunk_group_decision",
                                    index_path,
                                    root,
                                    f"row linking a nested index.md must use '— · group': {row.target}",
                                )
                            )
                        if not is_within(resolved, chunks_dir):
                            errors.append(
                                issue(
                                    "index_target_outside_chunks",
                                    index_path,
                                    root,
                                    f"index target points outside chunks: {row.target}",
                                )
                            )
                        elif not resolved.exists():
                            errors.append(
                                issue(
                                    "missing_index_target",
                                    index_path,
                                    root,
                                    f"index target does not exist: {row.target}",
                                )
                            )
                    for resolved, count in target_counts.items():
                        if count > 1:
                            errors.append(
                                issue(
                                    "duplicate_index_target",
                                    index_path,
                                    root,
                                    f"index target is listed {count} times: {content_path(resolved, chunks_dir)}",
                                )
                            )
                    index_targets[index_path.resolve()] = resolved_targets

                if (
                    root_index.resolve() not in index_has_parse_error
                    and not index_targets.get(root_index.resolve())
                ):
                    errors.append(
                        issue(
                            "root_index_without_chunk_targets",
                            root_index,
                            root,
                            "root chunks/index.md has no valid chunk targets",
                        )
                    )

                for directory in sorted(path for path in chunks_dir.rglob("*") if path.is_dir()):
                    if content_children(directory) and not (directory / "index.md").is_file():
                        errors.append(
                            issue(
                                "missing_nested_index",
                                directory,
                                root,
                                "nested chunk directories with child chunks or directories need a local index.md",
                            )
                        )

                errors.extend(chunk_path_errors(chunks_dir, root))

                for nested_index in sorted(chunks_dir.rglob("index.md")):
                    if nested_index == root_index:
                        continue
                    parent_index = nested_index.parent.parent / "index.md"
                    if parent_index.is_file() and nested_index.resolve() not in index_targets.get(
                        parent_index.resolve(), []
                    ):
                        errors.append(
                            issue(
                                "nested_index_not_listed_in_parent_index",
                                nested_index,
                                root,
                                "nested index.md is not listed by its parent index.md",
                            )
                        )

                root_text = read_markdown(root_index)
                registry, registry_problems = parse_registry_text(root_text)
                if registry_problems:
                    errors.extend(parse_problem_issue(problem, root_index, root) for problem in registry_problems)
                registry_items = {
                    item["path"]: item for item in registry["items"]
                } if registry is not None else {}
                leaf_by_relative = {
                    leaf.relative_to(chunks_dir).as_posix(): leaf for leaf in leaf_files
                }
                for registered_path in sorted(set(registry_items) - set(leaf_by_relative)):
                    errors.append(
                        issue(
                            "orphan_chunk_exception",
                            root_index,
                            root,
                            f"registry entry has no matching leaf chunk: {registered_path}",
                        )
                    )

                for leaf in leaf_files:
                    relative_leaf = leaf.relative_to(chunks_dir).as_posix()
                    index_path = nearest_index_for(leaf, chunks_dir)
                    row = None
                    if index_path is not None:
                        row = row_by_target.get((index_path.resolve(), leaf.resolve()))
                        if row is None:
                            errors.append(
                                issue(
                                    "leaf_not_listed_in_nearest_index",
                                    leaf,
                                    root,
                                    "leaf chunk is not listed by the nearest index.md",
                                )
                            )

                    text = read_markdown(leaf)
                    if not text.strip():
                        errors.append(issue("empty_leaf_chunk", leaf, root, "leaf chunk is empty or whitespace-only"))
                        continue
                    if reviewable_payload_characters(text) == 0:
                        errors.append(
                            issue(
                                "no_reviewable_leaf_content",
                                leaf,
                                root,
                                "leaf chunk has no reviewable text beyond headings or image markup",
                            )
                        )
                        continue

                    headings = extract_headings(text)
                    if not headings or not is_descriptive_heading(headings[0]):
                        errors.append(
                            issue(
                                "chunk_without_descriptive_heading",
                                leaf,
                                root,
                                "leaf chunk needs a descriptive first Markdown heading; numeric keys and continuation labels are insufficient",
                            )
                        )
                    if row is not None:
                        if not is_descriptive_heading(row.title):
                            errors.append(
                                issue(
                                    "index_without_descriptive_title",
                                    index_path,
                                    root,
                                    f"index row for {relative_leaf} has a non-descriptive title and coverage cell",
                                )
                            )
                        if len(headings) > 1 and row.description in {"", "—"}:
                            errors.append(
                                issue(
                                    "missing_chunk_content_description",
                                    index_path,
                                    root,
                                    f"index row for {relative_leaf} needs a content description because the chunk has multiple headings",
                                )
                            )

                    units = content_units(text)
                    kind = size_kind(units, minimum, maximum)
                    registry_item = registry_items.get(relative_leaf)

                    if row is not None:
                        if row.units is None:
                            errors.append(
                                issue(
                                    "invalid_chunk_size_decision",
                                    index_path,
                                    root,
                                    f"leaf row for {relative_leaf} cannot use the group size decision",
                                )
                            )
                        elif row.units != units:
                            warnings.append(
                                issue(
                                    "index_size_mismatch",
                                    index_path,
                                    root,
                                    f"index records {row.units} units for {relative_leaf}; audit measured {units}",
                                )
                            )
                        if row.size_status not in expected_table_status(kind):
                            threshold_issue(
                                kind,
                                "index_size_status_mismatch",
                                leaf,
                                root,
                                f"index status {row.size_status!r} does not match current {kind} size state",
                                errors,
                                warnings,
                            )

                    if kind == "normal":
                        if registry_item is not None:
                            warnings.append(
                                issue(
                                    "obsolete_chunk_exception",
                                    leaf,
                                    root,
                                    "chunk is now within thresholds but still has a registered size exception",
                                )
                            )
                    else:
                        expected_accepted = f"accepted-{kind}"
                        visible_acceptance = (
                            row is not None
                            and row.size_status == expected_accepted
                            and bool(row.reason)
                            and row.review_status == "reviewed"
                        )
                        if visible_acceptance and registry_item is None:
                            threshold_issue(
                                kind,
                                "acceptance_without_registry",
                                leaf,
                                root,
                                "visible accepted size reason has no matching machine registry entry",
                                errors,
                                warnings,
                            )
                        elif registry_item is not None and not visible_acceptance:
                            errors.append(
                                issue(
                                    "registry_table_status_mismatch",
                                    leaf,
                                    root,
                                    "registry entry exists but the nearest index row is not the matching accepted status with a reason",
                                )
                            )
                        elif visible_acceptance and registry_item is not None and registry is not None:
                            expected_policy = {"min": minimum, "max": maximum, "units_algo": UNITS_ALGO}
                            valid = (
                                registry["policy"] == expected_policy
                                and registry_item["kind"] == kind
                                and registry_item["content_sha256"] == sha256_text(text)
                                and registry_item["reason_sha256"] == sha256_text(row.reason.strip())
                            )
                            if valid:
                                accepted_exceptions.append(
                                    {
                                        "path": relative_leaf,
                                        "kind": kind,
                                        "content_units": units,
                                        "review_ref": registry_item["review_ref"],
                                    }
                                )
                            else:
                                threshold_issue(
                                    kind,
                                    "stale_chunk_exception",
                                    leaf,
                                    root,
                                    "registered exception no longer matches policy, kind, normalized content, or visible reason",
                                    errors,
                                    warnings,
                                )
                        elif registry_item is None:
                            code = (
                                "undersized_chunk_without_exception"
                                if kind == "under"
                                else "oversized_chunk_without_exception"
                            )
                            threshold_issue(
                                kind,
                                code,
                                leaf,
                                root,
                                f"leaf chunk has {units} content units and no accepted {kind} size exception",
                                errors,
                                warnings,
                            )

                    for target, resolved in local_link_targets(leaf, MARKDOWN_IMAGE_RE):
                        if not Path(target).is_absolute() and not resolved.exists():
                            warnings.append(
                                issue(
                                    "unresolved_local_image",
                                    leaf,
                                    root,
                                    f"local image reference does not resolve from this chunk: {target}",
                                )
                            )

                warnings.extend(numbered_child_warnings(leaf_files, root))

    warnings.extend(repeated_source_heading_warnings(root))

    final_metadata = [root / "summary.md", root / "manifest.md"]
    if errors and any(path.exists() for path in final_metadata):
        errors.append(
            issue(
                "final_metadata_before_chunk_audit_passed",
                root,
                root,
                "final summary.md or manifest.md exists while chunk audit has hard failures",
            )
        )

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    warnings.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    accepted_exceptions.sort(key=lambda item: (item["path"], item["kind"]))
    accepted_under = sum(item["kind"] == "under" for item in accepted_exceptions)
    accepted_over = sum(item["kind"] == "over" for item in accepted_exceptions)
    status = "fail" if errors else "warn" if warnings else "pass"
    return {
        "schema": SCHEMA_VERSION,
        "path": root.as_posix(),
        "thresholds": {"min": minimum, "max": maximum, "units_algo": UNITS_ALGO},
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "accepted_exceptions": accepted_exceptions,
        "summary": {
            "leaf_chunks": len(leaf_files),
            "errors": len(errors),
            "warnings": len(warnings),
            "accepted_exceptions": len(accepted_exceptions),
            "accepted_under": accepted_under,
            "accepted_over": accepted_over,
            "accepted_ratio": round(len(accepted_exceptions) / len(leaf_files), 6) if leaf_files else 0.0,
        },
    }


def print_human(stats: dict) -> None:
    for label in ("errors", "warnings"):
        for item in stats[label]:
            print(f"{label[:-1]}: {item['code']}: {item['path']}: {item['message']}")
    for item in stats["accepted_exceptions"]:
        print(
            f"accepted: {item['kind']}: {item['path']}: "
            f"{item['content_units']} content units; review {item['review_ref']}"
        )


def main(argv: list[str] | None = None) -> int:
    raw_args = sys.argv[1:] if argv is None else argv
    json_requested = "--json" in raw_args
    parser = AuditArgumentParser(description="Audit one chunked intake folder.")
    parser.add_argument("path", help="Path to a chunked intake folder containing chunks/.")
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_LARGE_SOURCE_THRESHOLD,
        help="Leaf chunk hard maximum in normalized content units.",
    )
    parser.add_argument(
        "--min-threshold",
        type=int,
        default=DEFAULT_SMALL_CHUNK_THRESHOLD,
        help="Leaf chunk soft minimum in normalized content units.",
    )
    parser.add_argument("--json", action="store_true", help="Print audit JSON.")
    try:
        args = parser.parse_args(raw_args)
    except AuditArgumentError as exc:
        stats = input_result(
            Path("."),
            DEFAULT_SMALL_CHUNK_THRESHOLD,
            DEFAULT_LARGE_SOURCE_THRESHOLD,
            "invalid_arguments",
            f"invalid command arguments: {exc}",
        )
        if json_requested:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print(f"invalid arguments: {exc}", file=sys.stderr)
        return 2

    root = Path(args.path)
    if args.min_threshold < 1 or args.threshold <= args.min_threshold:
        stats = input_result(
            root,
            args.min_threshold,
            args.threshold,
            "invalid_thresholds",
            "thresholds must satisfy 0 < min-threshold < threshold",
        )
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("invalid thresholds: require 0 < min-threshold < threshold", file=sys.stderr)
        return 2
    if not root.is_dir():
        stats = input_result(
            root,
            args.min_threshold,
            args.threshold,
            "missing_input",
            "input chunked intake folder does not exist",
        )
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print(f"missing directory: {root}", file=sys.stderr)
        return 2

    try:
        stats = inspect_chunks(root, args.min_threshold, args.threshold)
    except (UnicodeDecodeError, OSError) as exc:
        stats = input_result(
            root,
            args.min_threshold,
            args.threshold,
            "unreadable_input",
            f"cannot read UTF-8 chunk input: {exc}",
        )
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print(f"unreadable chunk input: {root}: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print_human(stats)
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
