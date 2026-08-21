from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
LINT_SCRIPTS = REPOSITORY_ROOT / ".agents/skills/obsidian-wiki-lint/scripts"
sys.path.insert(0, str(LINT_SCRIPTS))

from lint_wiki import (  # noqa: E402
    WIKILINK_RE,
    build_lookup,
    iter_markdown_files,
    mask_markdown_code,
    resolve_target,
    split_wikilink,
)


CANONICAL_NAME_RE = re.compile(r"^(?P<sequence>[0-9]{3})-(?P<topic>.+)\.md$")
LEGACY_NAME_RES = (
    re.compile(r"^错题(?P<sequence>[0-9]{3})\s*-\s*(?P<topic>.+)\.md$"),
    re.compile(r"^(?:[A-Za-z]+-)+(?P<sequence>[0-9]{3})-(?P<topic>.+)\.md$"),
)


def relative_path(path: Path, vault: Path) -> str:
    return path.relative_to(vault).as_posix()


def parse_name(name: str) -> tuple[str, str | None, str | None]:
    match = CANONICAL_NAME_RE.fullmatch(name)
    if match:
        topic = match["topic"].strip()
        if topic:
            return "canonical", match["sequence"], topic

    for pattern in LEGACY_NAME_RES:
        match = pattern.fullmatch(name)
        if match:
            topic = match["topic"].strip()
            if topic:
                return "legacy", match["sequence"], topic

    return "unresolved", None, None


def link_kind(source_path: str, index_path: str) -> str:
    if source_path == index_path:
        return "index"
    if source_path == "logs/wiki.md":
        return "historical_log"
    return "page"


def scan_links(
    vault: Path,
    markdown_files: list[Path],
    record_paths: set[str],
    index_path: str,
) -> tuple[dict[str, list[dict[str, object]]], list[dict[str, object]]]:
    all_files, by_stem = build_lookup(markdown_files, vault)
    inbound: dict[str, list[dict[str, object]]] = defaultdict(list)
    index_unresolved: list[dict[str, object]] = []

    for source in markdown_files:
        source_path = relative_path(source, vault)
        content = source.read_text(encoding="utf-8")
        masked = mask_markdown_code(content)
        for line_number, line in enumerate(masked.splitlines(), start=1):
            for match in WIKILINK_RE.finditer(line):
                target = split_wikilink(match.group(1))
                resolution = resolve_target(vault, target, all_files, by_stem)
                resolved = resolution[0] if resolution else None
                if resolved in record_paths:
                    inbound[resolved].append(
                        {
                            "path": source_path,
                            "line": line_number,
                            "kind": link_kind(source_path, index_path),
                        }
                    )
                elif source_path == index_path:
                    index_unresolved.append(
                        {
                            "target": target,
                            "resolved_path": resolved,
                            "line": line_number,
                        }
                    )

    for links in inbound.values():
        links.sort(key=lambda item: (str(item["path"]), int(item["line"]), str(item["kind"])))
    index_unresolved.sort(
        key=lambda item: (int(item["line"]), str(item["target"]), str(item["resolved_path"]))
    )
    return inbound, index_unresolved


def build_report(vault: Path, subject: str) -> dict[str, object]:
    vault = vault.resolve()
    syntheses_root = (vault / "wiki/syntheses").resolve()
    subject_root = (syntheses_root / subject).resolve()
    if not subject_root.is_relative_to(syntheses_root):
        raise ValueError(f"Subject path escapes wiki/syntheses: {subject}")
    if not subject_root.is_dir():
        raise FileNotFoundError(f"Subject directory not found: {subject_root}")

    wrong_root = subject_root / "wrong-questions"
    if wrong_root.exists() and not wrong_root.is_dir():
        raise NotADirectoryError(f"Wrong-question path is not a directory: {wrong_root}")

    index_file = subject_root / "wrong-question-index.md"
    index_path = relative_path(index_file, vault)
    index_file_missing = not index_file.is_file()
    wrong_files = (
        sorted(path for path in wrong_root.iterdir() if path.is_file() and path.suffix == ".md")
        if wrong_root.is_dir()
        else []
    )

    records: list[dict[str, object]] = []
    sequence_paths: dict[str, list[str]] = defaultdict(list)
    target_paths: dict[str, list[str]] = defaultdict(list)

    for path in wrong_files:
        current_path = relative_path(path, vault)
        status, sequence, topic = parse_name(path.name)
        suggested_target = None
        if sequence and topic:
            suggested_target = relative_path(wrong_root / f"{sequence}-{topic}.md", vault)
            sequence_paths[sequence].append(current_path)
            target_paths[suggested_target].append(current_path)
        records.append(
            {
                "current_path": current_path,
                "status": status,
                "sequence": sequence,
                "topic": topic,
                "suggested_target": suggested_target,
                "index_entries": [],
                "inbound_links": [],
            }
        )

    markdown_files = iter_markdown_files(vault)
    record_paths = {str(record["current_path"]) for record in records}
    inbound, index_unresolved = scan_links(vault, markdown_files, record_paths, index_path)

    index_missing: list[str] = []
    index_duplicates: list[dict[str, object]] = []
    for record in records:
        current_path = str(record["current_path"])
        links = inbound.get(current_path, [])
        index_entries = [link for link in links if link["kind"] == "index"]
        record["index_entries"] = index_entries
        record["inbound_links"] = [link for link in links if link["kind"] != "index"]
        if not index_entries:
            index_missing.append(current_path)
        elif len(index_entries) > 1:
            index_duplicates.append(
                {
                    "current_path": current_path,
                    "count": len(index_entries),
                    "lines": [entry["line"] for entry in index_entries],
                }
            )

    duplicate_sequences = [
        {"sequence": sequence, "paths": sorted(paths)}
        for sequence, paths in sorted(sequence_paths.items())
        if len(paths) > 1
    ]
    target_collisions = [
        {"target_path": target, "paths": sorted(paths)}
        for target, paths in sorted(target_paths.items())
        if len(paths) > 1
    ]

    records.sort(key=lambda item: str(item["current_path"]))
    index_missing.sort()
    index_duplicates.sort(key=lambda item: str(item["current_path"]))
    has_findings = any(
        (
            any(record["status"] != "canonical" for record in records),
            duplicate_sequences,
            target_collisions,
            index_missing,
            index_duplicates,
            index_unresolved,
            index_file_missing,
        )
    )

    return {
        "schema": 1,
        "status": "findings" if has_findings else "clean",
        "vault": str(vault),
        "subject": subject,
        "wrong_question_directory": relative_path(wrong_root, vault),
        "index_path": index_path,
        "index_file_missing": index_file_missing,
        "records": records,
        "duplicate_sequences": duplicate_sequences,
        "target_collisions": target_collisions,
        "index_missing": index_missing,
        "index_duplicates": index_duplicates,
        "index_unresolved": index_unresolved,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit one exam subject's wrong-question structure.")
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.vault, args.subject)
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
        if args.output:
            output = args.output.resolve()
            if output.exists() and not output.is_file():
                raise ValueError(f"Output path is not a regular file: {output}")
            if not output.parent.is_dir():
                raise FileNotFoundError(f"Output parent directory not found: {output.parent}")
            output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (OSError, UnicodeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2
    return 0 if report["status"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
