#!/usr/bin/env python3
"""Expand uniquely truncated Obsidian wikilinks."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from markdown_code import mask_markdown_code
from obsidian_links import WIKILINK_RE, build_wikilink_inner, parse_wikilink_inner


@dataclass(frozen=True)
class Change:
    old: str
    new: str


def collect_markdown_names(target_dir: Path) -> set[str]:
    return {path.stem for path in target_dir.iterdir() if path.is_file() and path.suffix == ".md"}


def require_within_vault(path: Path, vault: Path, label: str) -> None:
    if path != vault and vault not in path.parents:
        raise ValueError(f"{label} must resolve inside the declared vault: {path}")


def atomic_write_text(path: Path, text: str) -> None:
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def read_text_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def fix_links(vault: Path, source_file: Path, target_dir: Path, write: bool) -> int:
    vault_abs = vault.resolve()
    source_abs = (vault_abs / source_file).resolve()
    target_abs = (vault_abs / target_dir).resolve()
    require_within_vault(source_abs, vault_abs, "source file")
    require_within_vault(target_abs, vault_abs, "target directory")
    if not source_abs.is_file():
        raise ValueError(f"source file is not a file: {source_abs}")
    if target_abs == vault_abs or not target_abs.is_dir():
        raise ValueError(f"target directory must be an existing vault subdirectory: {target_abs}")
    names = collect_markdown_names(target_abs)
    target_prefix = target_abs.relative_to(vault_abs).as_posix()

    content = read_text_exact(source_abs)
    changes: list[Change] = []

    def replace(match) -> str:
        original_link = content[match.start() : match.end()]
        inner = content[match.start(1) : match.end(1)]
        parts = parse_wikilink_inner(inner)
        link_target = parts.target
        if not link_target.startswith(target_prefix + "/"):
            return original_link

        remainder = link_target[len(target_prefix) + 1 :]
        if not remainder or "/" in remainder or "\\" in remainder:
            return original_link
        filename = remainder
        explicit_suffix = filename.lower().endswith(".md")
        lookup_name = Path(filename).stem if explicit_suffix else filename
        if lookup_name in names:
            return original_link

        candidates = sorted(name for name in names if name.startswith(lookup_name))
        if len(candidates) != 1:
            if len(candidates) > 1:
                print(f"Ambiguous: {lookup_name} -> {', '.join(candidates)}")
            else:
                print(f"No match: {lookup_name}")
            return original_link

        suffix = ".md" if explicit_suffix else ""
        new_target = f"{target_prefix}/{candidates[0]}{suffix}"
        new_inner = build_wikilink_inner(parts, target=new_target)
        new_link = f"[[{new_inner}]]"
        changes.append(Change(original_link, new_link))
        return new_link

    masked = mask_markdown_code(content)
    pieces: list[str] = []
    last = 0
    for match in WIKILINK_RE.finditer(masked):
        pieces.append(content[last : match.start()])
        pieces.append(replace(match))
        last = match.end()
    pieces.append(content[last:])
    updated = "".join(pieces)

    if not changes:
        print("No changes.")
        return 0

    for change in changes:
        print(f"{change.old} -> {change.new}")

    if write:
        atomic_write_text(source_abs, updated)
        print(f"Wrote {len(changes)} change(s): {source_abs.relative_to(vault_abs).as_posix()}")
    else:
        print(f"Dry run: {len(changes)} change(s). Add --write to apply.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fix uniquely truncated wikilinks.")
    parser.add_argument("--vault", default=".", help="Vault or package root.")
    parser.add_argument("--source-file", required=True, type=Path, help="Markdown file to update.")
    parser.add_argument("--target-dir", required=True, type=Path, help="Directory containing real Markdown targets.")
    parser.add_argument("--write", action="store_true", help="Write changes. Defaults to dry-run.")
    args = parser.parse_args(argv)

    vault = Path(args.vault).resolve()
    try:
        return fix_links(vault, args.source_file, args.target_dir, args.write)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"link fix failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
