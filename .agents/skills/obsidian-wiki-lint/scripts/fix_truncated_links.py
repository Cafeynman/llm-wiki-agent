#!/usr/bin/env python3
"""Expand uniquely truncated Obsidian wikilinks."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass(frozen=True)
class Change:
    old: str
    new: str


def to_posix(path: Path) -> str:
    return path.as_posix()


def split_inner(inner: str) -> tuple[str, str, bool]:
    escaped = r"\|" in inner
    normalized = inner.replace(r"\|", "|")
    parts = normalized.split("|")
    target = parts[0].strip()
    alias = "|".join(parts[1:]).strip() if len(parts) > 1 else ""
    return target, alias, escaped


def build_inner(target: str, alias: str, escaped: bool) -> str:
    inner = f"{target}|{alias}" if alias else target
    return inner.replace("|", r"\|") if escaped else inner


def collect_markdown_names(target_dir: Path) -> set[str]:
    return {path.stem for path in target_dir.iterdir() if path.is_file() and path.suffix == ".md"}


def fix_links(vault: Path, source_file: Path, target_dir: Path, write: bool) -> int:
    source_abs = (vault / source_file).resolve()
    target_abs = (vault / target_dir).resolve()
    names = collect_markdown_names(target_abs)
    target_prefix = to_posix(target_dir)

    content = source_abs.read_text(encoding="utf-8")
    changes: list[Change] = []

    def replace(match: re.Match[str]) -> str:
        inner = match.group(1)
        link_target, alias, escaped = split_inner(inner)
        if not link_target.startswith(target_prefix + "/"):
            return match.group(0)

        filename = Path(link_target).name
        if filename in names:
            return match.group(0)

        candidates = sorted(name for name in names if name.startswith(filename))
        if len(candidates) != 1:
            if len(candidates) > 1:
                print(f"Ambiguous: {filename} -> {', '.join(candidates)}")
            else:
                print(f"No match: {filename}")
            return match.group(0)

        new_target = f"{target_prefix}/{candidates[0]}"
        new_inner = build_inner(new_target, alias, escaped)
        new_link = f"[[{new_inner}]]"
        changes.append(Change(match.group(0), new_link))
        return new_link

    updated = WIKILINK_RE.sub(replace, content)

    if not changes:
        print("No changes.")
        return 0

    for change in changes:
        print(f"{change.old} -> {change.new}")

    if write:
        source_abs.write_text(updated, encoding="utf-8")
        print(f"Wrote {len(changes)} change(s): {to_posix(source_file)}")
    else:
        print(f"Dry run: {len(changes)} change(s). Add --write to apply.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix uniquely truncated wikilinks.")
    parser.add_argument("--vault", default=".", help="Vault or package root.")
    parser.add_argument("--source-file", required=True, type=Path, help="Markdown file to update.")
    parser.add_argument("--target-dir", required=True, type=Path, help="Directory containing real Markdown targets.")
    parser.add_argument("--write", action="store_true", help="Write changes. Defaults to dry-run.")
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    return fix_links(vault, args.source_file, args.target_dir, args.write)


if __name__ == "__main__":
    raise SystemExit(main())
