#!/usr/bin/env python3
"""Lint Obsidian wiki links without modifying files."""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)
TRACEABILITY_PATH_RE = re.compile(
    r"(?<![\w/.\-])"
    r"((?:artifacts|intake|logs|questions|raw|reviews|wiki)/[^\s\]\)<>'\"`|]+)"
)
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


def normalize_link_path(target: str) -> str:
    target = unquote(target.strip()).replace("\\", "/")
    while target.startswith("./"):
        target = target[2:]
    return target.lstrip("/")


def is_explicit_directory_target(target: str) -> bool:
    return target.strip().endswith(("/", "\\"))


def is_intake_target(target: str) -> bool:
    return normalize_link_path(target).startswith("intake/")


def normalize_target(target: str) -> str:
    target = normalize_link_path(target)
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


def strip_yaml_comment(value: str) -> str:
    value = value.strip()
    if is_quoted_yaml_scalar(value):
        return value
    return value.split(" #", 1)[0].strip()


def iter_markdown_body_lines(content: str) -> list[tuple[int, str]]:
    frontmatter_match = FRONTMATTER_RE.match(content)
    frontmatter_lines = len(frontmatter_match.group(0).splitlines()) if frontmatter_match else 0
    lines: list[tuple[int, str]] = []
    in_fence = False
    fence_marker: str | None = None

    for line_no, line in enumerate(content.splitlines(), start=1):
        if line_no <= frontmatter_lines:
            continue

        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = None
            continue

        if in_fence:
            continue

        lines.append((line_no, line))

    return lines


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


def has_unescaped_pipe(value: str) -> bool:
    escaped = False
    for char in value:
        if char == "\\" and not escaped:
            escaped = True
            continue
        if char == "|" and not escaped:
            return True
        escaped = False
    return False


def mask_inline_code(line: str) -> str:
    chars = list(line)
    index = 0

    while index < len(chars):
        if chars[index] != "`":
            index += 1
            continue

        run_start = index
        while index < len(chars) and chars[index] == "`":
            index += 1
        marker = "`" * (index - run_start)
        closing = line.find(marker, index)
        if closing == -1:
            continue

        for mask_index in range(run_start, closing + len(marker)):
            chars[mask_index] = " "
        index = closing + len(marker)

    return "".join(chars)


def is_table_separator_line(line: str) -> bool:
    stripped = line.strip()
    if "|" not in stripped:
        return False

    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return len(cells) >= 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def is_table_row_line(line: str) -> bool:
    return "|" in line and bool(line.strip())


def table_line_numbers(lines: list[tuple[int, str]]) -> set[int]:
    table_lines: set[int] = set()
    for index, (line_no, line) in enumerate(lines):
        if not is_table_separator_line(line):
            continue

        if index > 0 and is_table_row_line(lines[index - 1][1]):
            table_lines.add(lines[index - 1][0])
        table_lines.add(line_no)

        next_index = index + 1
        while next_index < len(lines) and is_table_row_line(lines[next_index][1]):
            table_lines.add(lines[next_index][0])
            next_index += 1

    return table_lines


def mask_inline_exclusions(line: str) -> str:
    masked = mask_inline_code(line)
    masked = WIKILINK_RE.sub(" ", masked)
    return MD_LINK_RE.sub(" ", masked)


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


def lint_tag_entry(raw_value: str, rel: str, line_no: int) -> list[str]:
    raw_value = strip_yaml_comment(raw_value)
    if not raw_value or raw_value.startswith("#"):
        return []

    value = strip_yaml_quotes(raw_value)
    normalized = value[1:] if value.startswith("#") else value
    if any(char.isspace() for char in normalized):
        return [f"{rel}:{line_no}: tags entry must not contain whitespace: {raw_value}"]
    return []


def lint_tags_value(raw_value: str, rel: str, line_no: int) -> list[str]:
    raw_value = strip_yaml_comment(raw_value)
    flow_items = split_flow_list(raw_value)
    if flow_items is None:
        return lint_tag_entry(raw_value, rel, line_no)

    errors: list[str] = []
    for item in flow_items:
        errors.extend(lint_tag_entry(item, rel, line_no))
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


def add_intake_source_link_spans(line: str, offset: int, spans: set[tuple[int, int]]) -> None:
    for match in WIKILINK_RE.finditer(line):
        raw_target = split_wikilink(match.group(1))
        if is_intake_target(raw_target):
            spans.add((offset + match.start(), offset + match.end()))


def frontmatter_intake_source_link_spans(content: str) -> set[tuple[int, int]]:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return set()

    frontmatter = match.group(1)
    offset = match.start(1)
    spans: set[tuple[int, int]] = set()
    in_sources = False
    sources_indent = 0

    for line in frontmatter.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            offset += len(line)
            continue

        indent = len(line) - len(line.lstrip())
        if not in_sources:
            sources_match = re.match(r"^sources\s*:\s*(.*)$", stripped)
            if sources_match:
                inline_value = sources_match.group(1).strip()
                if inline_value and not inline_value.startswith("#"):
                    add_intake_source_link_spans(line, offset, spans)
                else:
                    in_sources = True
                    sources_indent = indent
            offset += len(line)
            continue

        if indent <= sources_indent and not stripped.startswith("-"):
            break
        if stripped.startswith("-"):
            add_intake_source_link_spans(line, offset, spans)
        offset += len(line)

    return spans


def lint_frontmatter_tags(content: str, rel: str) -> list[str]:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return []

    frontmatter = match.group(1)
    errors: list[str] = []
    in_tags = False
    tags_indent = 0

    for line_no, line in enumerate(frontmatter.splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        if not in_tags:
            tags_match = re.match(r"^tags\s*:\s*(.*)$", stripped)
            if tags_match:
                inline_value = tags_match.group(1).strip()
                if inline_value and not inline_value.startswith("#"):
                    errors.extend(lint_tags_value(inline_value, rel, line_no))
                    continue
                in_tags = True
                tags_indent = indent
            continue

        if indent <= tags_indent and not stripped.startswith("-"):
            break
        if not stripped.startswith("-"):
            continue

        errors.extend(lint_tag_entry(stripped[1:].strip(), rel, line_no))

    return errors


def lint_table_wikilink_aliases(content: str, rel: str) -> list[str]:
    lines = iter_markdown_body_lines(content)
    table_lines = table_line_numbers(lines)
    errors: list[str] = []

    for line_no, line in lines:
        if line_no not in table_lines:
            continue

        masked = mask_inline_code(line)
        for match in WIKILINK_RE.finditer(masked):
            inner = match.group(1)
            if has_unescaped_pipe(inner):
                errors.append(
                    f"{rel}:{line_no}: wikilink alias separator must be escaped in Markdown tables: {match.group(0)}"
                )

    return errors


def lint_bare_traceability_paths(content: str, rel: str) -> list[str]:
    errors: list[str] = []

    for line_no, line in iter_markdown_body_lines(content):
        masked = mask_inline_exclusions(line)
        for match in TRACEABILITY_PATH_RE.finditer(masked):
            path = match.group(1).rstrip(".,;:!?")
            if path:
                errors.append(f"{rel}:{line_no}: internal traceability path must use a wikilink: {path}")

    return errors


def build_lookup(markdown_files: list[Path], vault: Path) -> tuple[set[str], dict[str, list[str]]]:
    all_files: set[str] = set()
    by_stem: dict[str, list[str]] = defaultdict(list)
    for file_path in markdown_files:
        rel = to_posix(file_path.relative_to(vault))
        all_files.add(rel)
        by_stem[file_path.stem].append(rel)
    return all_files, by_stem


def resolve_target(vault: Path, target: str, all_files: set[str], by_stem: dict[str, list[str]]) -> tuple[str, bool] | None:
    explicit_directory = is_explicit_directory_target(target)
    target = normalize_link_path(target)
    if not target:
        return None

    if explicit_directory:
        if not target.endswith("/"):
            target += "/"
        return target, True

    if (vault / target).exists() and not (vault / target).is_dir():
        # If it directly exists (e.g. an attachment)
        return target, False

    normalized = normalize_target(target)
    if not normalized:
        return None
    if normalized in all_files:
        return normalized, False
    if "/" not in normalized:
        matches = by_stem.get(Path(normalized).stem, [])
        if len(matches) == 1:
            return matches[0], False
    return normalized, False


def lint(vault: Path, scope: str) -> int:
    markdown_files = iter_markdown_files(vault)
    all_files, by_stem = build_lookup(markdown_files, vault)
    scoped_files = sorted(f for f in all_files if f == scope or f.startswith(scope.rstrip("/") + "/"))

    incoming: dict[str, list[str]] = defaultdict(list)
    broken: dict[str, list[str]] = defaultdict(list)
    frontmatter_source_errors: list[str] = []
    frontmatter_tag_errors: list[str] = []
    table_wikilink_errors: list[str] = []
    traceability_path_errors: list[str] = []

    for rel in scoped_files:
        content = (vault / rel).read_text(encoding="utf-8")
        ignored_frontmatter_intake_links = frontmatter_intake_source_link_spans(content)
        frontmatter_source_errors.extend(lint_frontmatter_sources(content, rel))
        frontmatter_tag_errors.extend(lint_frontmatter_tags(content, rel))
        table_wikilink_errors.extend(lint_table_wikilink_aliases(content, rel))
        traceability_path_errors.extend(lint_bare_traceability_paths(content, rel))
        for match in WIKILINK_RE.finditer(content):
            if match.span() in ignored_frontmatter_intake_links:
                continue
            raw_target = split_wikilink(match.group(1))
            if not raw_target or raw_target.startswith(("http://", "https://", "mailto:")):
                continue
            resolution = resolve_target(vault, raw_target, all_files, by_stem)
            if not resolution:
                continue
            resolved, is_directory = resolution
            if is_directory:
                if not (vault / resolved.rstrip("/")).is_dir():
                    broken[resolved].append(rel)
                continue
            incoming[resolved].append(rel)
            if resolved not in all_files and not (vault / resolved).exists():
                broken[resolved].append(rel)

        for match in MD_LINK_RE.finditer(content):
            raw_target = match.group(1).split("#", 1)[0].strip()
            if not raw_target or raw_target.startswith(("http://", "https://", "mailto:")):
                continue
            resolution = resolve_target(vault, raw_target, all_files, by_stem)
            if not resolution:
                continue
            resolved, is_directory = resolution
            if is_directory:
                if not (vault / resolved.rstrip("/")).is_dir():
                    broken[resolved].append(rel)
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
    print("=== Frontmatter tags ===")
    if not frontmatter_tag_errors:
        print("None")
    else:
        for error in frontmatter_tag_errors:
            print(f"Invalid: {error}")

    print()
    print("=== Markdown tables ===")
    if not table_wikilink_errors:
        print("None")
    else:
        for error in table_wikilink_errors:
            print(f"Invalid: {error}")

    print()
    print("=== Traceability paths ===")
    if not traceability_path_errors:
        print("None")
    else:
        for error in traceability_path_errors:
            print(f"Invalid: {error}")

    print()
    print("=== Stats ===")
    print(f"Markdown pages: {len(all_files)}")
    print(f"Scoped pages: {len(scoped_files)}")
    print(f"Broken links: {len(broken)}")
    print(f"Orphan pages: {len(orphans)}")
    print(f"Frontmatter source errors: {len(frontmatter_source_errors)}")
    print(f"Frontmatter tag errors: {len(frontmatter_tag_errors)}")
    print(f"Markdown table errors: {len(table_wikilink_errors)}")
    print(f"Traceability path errors: {len(traceability_path_errors)}")
    return 1 if (
        broken
        or frontmatter_source_errors
        or frontmatter_tag_errors
        or table_wikilink_errors
        or traceability_path_errors
    ) else 0


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
