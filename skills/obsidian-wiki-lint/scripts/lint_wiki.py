#!/usr/bin/env python3
"""Lint Obsidian wiki links without modifying files."""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SKIP_DIRS = {
    ".git",
    ".obsidian",
    ".venv",
    "__pycache__",
    "node_modules",
    "tmp",
}


def to_posix(path: Path) -> str:
    return path.as_posix()


def iter_markdown_files(vault: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, names in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for name in names:
            if name.endswith(".md"):
                files.append(root_path / name)
    return sorted(files)


def split_wikilink(inner: str) -> str:
    normalized = inner.replace(r"\|", "|")
    target = normalized.split("|", 1)[0].strip()
    if "#" in target:
        target = target.split("#", 1)[0].strip()
    return target


def normalize_target(target: str) -> str:
    target = target.strip().replace("\\", "/")
    if not target:
        return target
    if not target.endswith(".md"):
        target += ".md"
    return target


def build_lookup(markdown_files: list[Path], vault: Path) -> tuple[set[str], dict[str, list[str]]]:
    all_files: set[str] = set()
    by_stem: dict[str, list[str]] = defaultdict(list)
    for file_path in markdown_files:
        rel = to_posix(file_path.relative_to(vault))
        all_files.add(rel)
        by_stem[file_path.stem].append(rel)
    return all_files, by_stem


def resolve_target(target: str, all_files: set[str], by_stem: dict[str, list[str]]) -> str | None:
    normalized = normalize_target(target)
    if not normalized:
        return None
    if normalized in all_files:
        return normalized
    if "/" not in normalized:
        matches = by_stem.get(Path(normalized).stem, [])
        if len(matches) == 1:
            return matches[0]
    return normalized


def lint(vault: Path, scope: str) -> int:
    markdown_files = iter_markdown_files(vault)
    all_files, by_stem = build_lookup(markdown_files, vault)
    scoped_files = sorted(f for f in all_files if f == scope or f.startswith(scope.rstrip("/") + "/"))

    incoming: dict[str, list[str]] = defaultdict(list)
    broken: dict[str, list[str]] = defaultdict(list)

    for rel in scoped_files:
        content = (vault / rel).read_text(encoding="utf-8")
        for match in WIKILINK_RE.finditer(content):
            raw_target = split_wikilink(match.group(1))
            if not raw_target or raw_target.startswith(("http://", "https://")):
                continue
            resolved = resolve_target(raw_target, all_files, by_stem)
            if not resolved:
                continue
            incoming[resolved].append(rel)
            if resolved not in all_files:
                broken[resolved].append(rel)

    orphans = [rel for rel in scoped_files if rel not in incoming]

    print("=== Broken wikilinks ===")
    if not broken:
        print("None")
    else:
        for target, sources in sorted(broken.items()):
            print(f"Broken: {target}")
            print(f"  Sources: {', '.join(sorted(set(sources)))}")

    print()
    print(f"=== Orphan pages under {scope} ===")
    if not orphans:
        print("None")
    else:
        for rel in orphans:
            print(f"Orphan: {rel}")

    print()
    print("=== Stats ===")
    print(f"Markdown pages: {len(all_files)}")
    print(f"Scoped pages: {len(scoped_files)}")
    print(f"Broken links: {len(broken)}")
    print(f"Orphan pages: {len(orphans)}")
    return 1 if broken else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint Obsidian wikilinks.")
    parser.add_argument("--vault", default=".", help="Vault or package root.")
    parser.add_argument("--scope", default="wiki", help="Relative path scope to lint.")
    args = parser.parse_args()

    vault = Path(args.vault).resolve()
    if not vault.exists():
        raise SystemExit(f"Vault does not exist: {vault}")
    return lint(vault, args.scope.strip("/"))


if __name__ == "__main__":
    raise SystemExit(main())
