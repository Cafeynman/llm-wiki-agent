#!/usr/bin/env python3
"""Lint Obsidian wiki links without modifying files."""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)
INTERNAL_SOURCE_PREFIXES = (
    "artifacts/",
    "intake/",
    "logs/",
    "questions/",
    "raw/",
    "reviews/",
    "wiki/",
)
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


def strip_yaml_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def is_quoted_yaml_scalar(value: str) -> bool:
    value = value.strip()
    return len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}


def is_external_source(value: str) -> bool:
    return value.startswith(("http://", "https://", "mailto:"))


def is_internal_source_path(value: str) -> bool:
    normalized = value.replace("\\", "/").lstrip("./")
    return normalized.startswith(INTERNAL_SOURCE_PREFIXES)


def split_flow_list(value: str) -> list[str] | None:
    stripped = value.strip()
    if not stripped.startswith("[") or not stripped.endswith("]"):
        return None

    inner = stripped[1:-1].strip()
    if not inner:
        return []

    items: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False

    for char in inner:
        if quote:
            current.append(char)
            if quote == '"' and char == "\\" and not escaped:
                escaped = True
                continue
            if char == quote and not escaped:
                quote = None
            escaped = False
            continue

        if char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char == ",":
            items.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    items.append("".join(current).strip())
    return items


def lint_source_entry(raw_value: str, rel: str, line_no: int) -> list[str]:
    raw_value = raw_value.strip()
    if not raw_value:
        return []

    quoted = is_quoted_yaml_scalar(raw_value)
    value = strip_yaml_quotes(raw_value)
    errors: list[str] = []

    if value.startswith("[["):
        if not quoted:
            errors.append(f"{rel}:{line_no}: sources entry must be a quoted wikilink: {raw_value}")
        return errors

    if is_external_source(value):
        if not quoted:
            errors.append(f"{rel}:{line_no}: sources entry must be a quoted URL: {raw_value}")
        return errors

    if is_internal_source_path(value):
        errors.append(f"{rel}:{line_no}: sources entry must be a quoted wikilink: {value}")

    return errors


def lint_sources_value(raw_value: str, rel: str, line_no: int) -> list[str]:
    stripped = raw_value.strip()
    if stripped.startswith("[[") and stripped.endswith("]]"):
        return lint_source_entry(stripped, rel, line_no)

    flow_items = split_flow_list(raw_value)
    if flow_items is None:
        return lint_source_entry(raw_value, rel, line_no)

    errors: list[str] = []
    for item in flow_items:
        errors.extend(lint_source_entry(item, rel, line_no))
    return errors


def lint_frontmatter_sources(content: str, rel: str) -> list[str]:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return []

    frontmatter = match.group(1)
    errors: list[str] = []
    in_sources = False
    sources_indent = 0

    for line_no, line in enumerate(frontmatter.splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        if not in_sources:
            sources_match = re.match(r"^sources\s*:\s*(.*)$", stripped)
            if sources_match:
                inline_value = sources_match.group(1).strip()
                if inline_value and not inline_value.startswith("#"):
                    errors.extend(lint_sources_value(inline_value, rel, line_no))
                    continue
                in_sources = True
                sources_indent = indent
            continue

        if indent <= sources_indent and not stripped.startswith("-"):
            break
        if not stripped.startswith("-"):
            continue

        errors.extend(lint_source_entry(stripped[1:].strip(), rel, line_no))

    return errors


def build_lookup(markdown_files: list[Path], vault: Path) -> tuple[set[str], dict[str, list[str]]]:
    all_files: set[str] = set()
    by_stem: dict[str, list[str]] = defaultdict(list)
    for file_path in markdown_files:
        rel = to_posix(file_path.relative_to(vault))
        all_files.add(rel)
        by_stem[file_path.stem].append(rel)
    return all_files, by_stem


def resolve_target(vault: Path, target: str, all_files: set[str], by_stem: dict[str, list[str]]) -> str | None:
    target = target.strip().replace("\\", "/")
    if not target:
        return None
    if (vault / target).exists() and not (vault / target).is_dir():
        # If it directly exists (e.g. an attachment)
        return target

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
    frontmatter_source_errors: list[str] = []

    for rel in scoped_files:
        content = (vault / rel).read_text(encoding="utf-8")
        frontmatter_source_errors.extend(lint_frontmatter_sources(content, rel))
        for match in WIKILINK_RE.finditer(content):
            raw_target = split_wikilink(match.group(1))
            if not raw_target or raw_target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = resolve_target(vault, raw_target, all_files, by_stem)
            if not resolved:
                continue
            incoming[resolved].append(rel)
            if resolved not in all_files and not (vault / resolved).exists():
                broken[resolved].append(rel)

        for match in MD_LINK_RE.finditer(content):
            raw_target = match.group(1).split("#", 1)[0].strip().replace("%20", " ")
            if not raw_target or raw_target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = resolve_target(vault, raw_target, all_files, by_stem)
            if not resolved:
                continue
            incoming[resolved].append(rel)
            if resolved not in all_files and not (vault / resolved).exists():
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
    print("=== Frontmatter sources ===")
    if not frontmatter_source_errors:
        print("None")
    else:
        for error in frontmatter_source_errors:
            print(f"Invalid: {error}")

    print()
    print("=== Stats ===")
    print(f"Markdown pages: {len(all_files)}")
    print(f"Scoped pages: {len(scoped_files)}")
    print(f"Broken links: {len(broken)}")
    print(f"Orphan pages: {len(orphans)}")
    print(f"Frontmatter source errors: {len(frontmatter_source_errors)}")
    return 1 if broken or frontmatter_source_errors else 0


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
