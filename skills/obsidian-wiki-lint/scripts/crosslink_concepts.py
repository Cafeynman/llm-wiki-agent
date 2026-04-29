#!/usr/bin/env python3
"""Add conservative cross-links between Obsidian concept notes."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


TITLE_RE = re.compile(r"^title:\s*(.+)$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^(---\s*\n[\s\S]*?\n---\s*\n)([\s\S]*)$")


@dataclass(frozen=True)
class Concept:
    name: str
    target: str


def to_posix(path: Path) -> str:
    return path.as_posix()


def read_title(content: str, fallback: str) -> str:
    match = TITLE_RE.search(content)
    if not match:
        return fallback
    return match.group(1).strip().strip("'\"")


def load_aliases(alias_file: Path | None) -> dict[str, str]:
    if not alias_file:
        return {}
    data = json.loads(alias_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Alias file must be a JSON object: alias -> concept title or target path.")
    return {str(key): str(value) for key, value in data.items()}


def build_concepts(vault: Path, concepts_dir: Path, aliases: dict[str, str]) -> list[Concept]:
    concepts_abs = (vault / concepts_dir).resolve()
    by_title: dict[str, str] = {}
    by_target: set[str] = set()

    for file_path in sorted(concepts_abs.glob("*.md")):
        rel_no_suffix = to_posix((concepts_dir / file_path.stem))
        title = read_title(file_path.read_text(encoding="utf-8"), file_path.stem)
        by_title[title] = rel_no_suffix
        by_target.add(rel_no_suffix)

    concepts = [Concept(name=title, target=target) for title, target in by_title.items()]
    for alias, destination in aliases.items():
        target = by_title.get(destination, destination)
        if target in by_target:
            concepts.append(Concept(name=alias, target=target))
        else:
            print(f"Alias skipped; target not found: {alias} -> {destination}")

    return sorted(concepts, key=lambda item: len(item.name), reverse=True)


def protected_spans(line: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for pattern in (r"\[\[[^\]]+\]\]", r"\[[^\]]+\]\([^)]+\)", r"`[^`]*`", r"https?://\S+"):
        spans.extend((m.start(), m.end()) for m in re.finditer(pattern, line))
    return spans


def in_span(index: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in spans)


def link_line(line: str, concept: Concept, max_count: int) -> tuple[str, int]:
    if "|" in line and re.match(r"^\s*\|", line):
        return line, 0

    escaped = re.escape(concept.name)
    pattern = re.compile(rf"(?<![\w\[/#])({escaped})(?![\w\]])")
    spans = protected_spans(line)
    pieces: list[str] = []
    last = 0
    count = 0

    for match in pattern.finditer(line):
        if count >= max_count or in_span(match.start(), spans):
            continue
        pieces.append(line[last : match.start()])
        pieces.append(f"[[{concept.target}|{match.group(1)}]]")
        last = match.end()
        count += 1

    if count == 0:
        return line, 0
    pieces.append(line[last:])
    return "".join(pieces), count


def crosslink_file(file_path: Path, concepts: list[Concept], max_per_concept: int) -> tuple[str, int]:
    content = file_path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        return content, 0

    frontmatter, body = match.groups()
    current_title = read_title(frontmatter, file_path.stem)
    current_target_name = file_path.stem
    total = 0
    lines = body.splitlines(keepends=True)

    for concept in concepts:
        if concept.name in {current_title, current_target_name} or Path(concept.target).name == current_target_name:
            continue
        remaining = max_per_concept
        in_code_block = False
        for index, line in enumerate(lines):
            if remaining <= 0:
                break
            if line.lstrip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            updated, count = link_line(line, concept, remaining)
            if count:
                lines[index] = updated
                remaining -= count
                total += count

    return frontmatter + "".join(lines), total


def crosslink(vault: Path, concepts_dir: Path, alias_file: Path | None, max_per_concept: int, write: bool) -> int:
    aliases = load_aliases(alias_file)
    concepts = build_concepts(vault, concepts_dir, aliases)
    concepts_abs = (vault / concepts_dir).resolve()
    total = 0
    changed_files = 0

    for file_path in sorted(concepts_abs.glob("*.md")):
        updated, count = crosslink_file(file_path, concepts, max_per_concept)
        if not count:
            continue
        changed_files += 1
        total += count
        rel = to_posix(file_path.relative_to(vault))
        print(f"{rel}: {count} link(s)")
        if write:
            file_path.write_text(updated, encoding="utf-8")

    if write:
        print(f"Wrote {total} link(s) across {changed_files} file(s).")
    else:
        print(f"Dry run: {total} link(s) across {changed_files} file(s). Add --write to apply.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Add conservative concept cross-links.")
    parser.add_argument("--vault", default=".", help="Vault or package root.")
    parser.add_argument("--concepts-dir", default="wiki/concepts", type=Path)
    parser.add_argument("--alias-file", type=Path, help="JSON object mapping alias to concept title or target path.")
    parser.add_argument("--max-per-concept", default=2, type=int)
    parser.add_argument("--write", action="store_true", help="Write changes. Defaults to dry-run.")
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    alias_file = args.alias_file.resolve() if args.alias_file else None
    return crosslink(vault, args.concepts_dir, alias_file, args.max_per_concept, args.write)


if __name__ == "__main__":
    raise SystemExit(main())
