import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from audit_intake_file import DEFAULT_LARGE_SOURCE_THRESHOLD, content_units, extract_headings


SCHEMA_VERSION = 1
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
NUMBERED_CHILD_RE = re.compile(r"(?<!\d)(\d+)\.(\d+(?:\.\d+)*)")
NUMBERED_PARENT_RE = re.compile(r"(?<!\d)(\d+)(?![\d.])")
EXTERNAL_TARGET_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


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


def index_records_oversized_reason(index_path: Path, leaf_path: Path) -> bool:
    text = index_path.read_text(encoding="utf-8").lower()
    if "oversized" not in text and "oversize" not in text:
        return False
    return leaf_path.name.lower() in text or leaf_path.stem.lower() in text


def local_heading_text(path: Path) -> str:
    try:
        headings = extract_headings(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return ""
    return " ".join(headings + [path.stem])


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
                    f"numbered child heading or filename '{child}' has no matching parent '{parent}' in chunk headings",
                )
            )
    return warnings


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


def inspect_chunks(root: Path, threshold: int) -> dict:
    chunks_dir = root / "chunks"
    errors: list[dict] = []
    warnings: list[dict] = []
    index_targets: dict[Path, set[Path]] = {}

    if not chunks_dir.is_dir():
        errors.append(issue("missing_chunks_dir", chunks_dir, root, "chunked intake folder has no chunks directory"))
    else:
        root_index = chunks_dir / "index.md"
        if not root_index.is_file():
            errors.append(issue("missing_chunks_index", root_index, root, "chunks/index.md is required"))
        for index_path in chunks_dir.rglob("index.md"):
            targets = local_link_targets(index_path, MARKDOWN_LINK_RE)
            index_targets[index_path.resolve()] = {resolved for _, resolved in targets}
            for target, resolved in targets:
                if not is_within(resolved, chunks_dir):
                    errors.append(
                        issue(
                            "index_target_outside_chunks",
                            index_path,
                            root,
                            f"index target points outside chunks: {target}",
                        )
                    )
                    continue
                if not resolved.exists():
                    errors.append(
                        issue("missing_index_target", index_path, root, f"index target does not exist: {target}")
                    )

        for directory in [path for path in chunks_dir.rglob("*") if path.is_dir()]:
            if directory == chunks_dir:
                continue
            has_local_children = any(child.name != "index.md" for child in directory.iterdir())
            if has_local_children and not (directory / "index.md").is_file():
                errors.append(
                    issue(
                        "missing_nested_index",
                        directory,
                        root,
                        "nested chunk directories with child chunks or directories need a local index.md",
                    )
                )

        leaf_files = [path for path in chunks_dir.rglob("*.md") if path.name != "index.md"]
        for leaf in leaf_files:
            index_path = nearest_index_for(leaf, chunks_dir)
            if index_path is not None and leaf.resolve() not in index_targets.get(index_path.resolve(), set()):
                errors.append(
                    issue(
                        "leaf_not_listed_in_nearest_index",
                        leaf,
                        root,
                        "leaf chunk is not listed by the nearest index.md",
                    )
                )

            text = leaf.read_text(encoding="utf-8")
            units = content_units(text)
            if units > threshold:
                if index_path is None or not index_records_oversized_reason(index_path, leaf):
                    errors.append(
                        issue(
                            "oversized_chunk_without_reason",
                            leaf,
                            root,
                            f"leaf chunk has {units} content units and no oversized reason in the nearest index.md",
                        )
                    )

            for target, resolved in local_link_targets(leaf, MARKDOWN_IMAGE_RE):
                if Path(target).is_absolute():
                    continue
                if not resolved.exists():
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

    status = "fail" if errors else "warn" if warnings else "pass"
    return {
        "schema": SCHEMA_VERSION,
        "path": root.as_posix(),
        "content_unit_threshold": threshold,
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


def print_human(stats: dict) -> None:
    if stats["status"] == "pass":
        return
    for label in ("errors", "warnings"):
        for item in stats[label]:
            print(f"{label[:-1]}: {item['code']}: {item['path']}: {item['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit one chunked intake folder.")
    parser.add_argument("path", help="Path to a chunked intake folder containing chunks/.")
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_LARGE_SOURCE_THRESHOLD,
        help="Leaf chunk oversized threshold in content units.",
    )
    parser.add_argument("--json", action="store_true", help="Print audit JSON.")
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.is_dir():
        print(f"missing directory: {root}", file=sys.stderr)
        return 2

    stats = inspect_chunks(root, args.threshold)
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print_human(stats)
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
