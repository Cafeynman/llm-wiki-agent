from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

from audit_intake_file import (
    UNITS_ALGO,
    is_closing_fence,
    normalize_markdown_text,
    opening_fence,
)


INDEX_COLUMNS = ("块", "标题与覆盖范围", "内容说明", "规模与尺寸裁决", "内容评审")
INDEX_LINK_RE = re.compile(r"^\[([^]]+)\]\(([^)]+)\)$")
SIZE_DECISION_RE = re.compile(
    r"^(\d+) · (normal|undersized|oversized|accepted-under|accepted-over)"
    r"(?: — (.+))?$"
)
GROUP_DECISION_RE = re.compile(r"^— · group$")
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
REGISTRY_RE = re.compile(
    r"<!--\s*chunk-size-exceptions\s*\n(.*?)\n\s*-->",
    re.DOTALL,
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REGISTRY_SCHEMA = 1
DEFAULT_SMALL_CHUNK_THRESHOLD = 2000
LEGACY_INDEX_LINK_RE = re.compile(r"(?m)^\s*(?:[-*]\s+)?\[[^]]+\]\([^)]+\)")


@dataclass(frozen=True)
class ParseProblem:
    code: str
    line: int
    message: str


@dataclass(frozen=True)
class IndexRow:
    line: int
    target: str
    label: str
    title: str
    description: str
    units: int | None
    size_status: str
    reason: str
    review_status: str


def split_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in stripped[1:-1]:
        if char == "|" and not escaped:
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(char)
        if char == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    cells.append("".join(current).strip())
    return cells


def parse_index_text(text: str) -> tuple[list[IndexRow], list[ParseProblem]]:
    lines = normalize_markdown_text(text).splitlines()
    header_locations: list[int] = []
    for index, line in enumerate(lines):
        cells = split_table_row(line)
        if cells == list(INDEX_COLUMNS):
            header_locations.append(index)

    if not header_locations:
        code = "legacy_chunk_index_format" if LEGACY_INDEX_LINK_RE.search(text) else "invalid_chunk_index_table"
        return [], [
            ParseProblem(
                code,
                1,
                "index.md must migrate to the canonical five-column chunk table; free-text size reasons are not accepted",
            )
        ]
    if len(header_locations) > 1:
        return [], [
            ParseProblem(
                "duplicate_chunk_index_table",
                header_locations[1] + 1,
                "index.md contains more than one canonical chunk table",
            )
        ]

    header_index = header_locations[0]
    if header_index + 1 >= len(lines):
        return [], [
            ParseProblem(
                "invalid_chunk_index_table",
                header_index + 1,
                "canonical chunk table is missing its separator row",
            )
        ]
    separators = split_table_row(lines[header_index + 1])
    if separators is None or len(separators) != len(INDEX_COLUMNS) or not all(
        TABLE_SEPARATOR_RE.fullmatch(cell) for cell in separators
    ):
        return [], [
            ParseProblem(
                "invalid_chunk_index_table",
                header_index + 2,
                "canonical chunk table has an invalid separator row",
            )
        ]

    rows: list[IndexRow] = []
    problems: list[ParseProblem] = []
    for index in range(header_index + 2, len(lines)):
        cells = split_table_row(lines[index])
        if cells is None:
            if not lines[index].strip():
                break
            continue
        line_no = index + 1
        if len(cells) != len(INDEX_COLUMNS):
            problems.append(
                ParseProblem(
                    "malformed_chunk_index_row",
                    line_no,
                    f"chunk table row has {len(cells)} cells; expected {len(INDEX_COLUMNS)}",
                )
            )
            continue
        link_match = INDEX_LINK_RE.fullmatch(cells[0])
        if not link_match:
            problems.append(
                ParseProblem(
                    "malformed_chunk_index_row",
                    line_no,
                    "first cell must be one Markdown link to a local chunk target",
                )
            )
            continue
        label, target = link_match.groups()
        if not cells[1] or cells[1] == "—":
            problems.append(
                ParseProblem(
                    "malformed_chunk_index_row",
                    line_no,
                    "title and coverage cell must identify the chunk content",
                )
            )
            continue

        if GROUP_DECISION_RE.fullmatch(cells[3]):
            units = None
            size_status = "group"
            reason = ""
        else:
            size_match = SIZE_DECISION_RE.fullmatch(cells[3])
            if not size_match:
                problems.append(
                    ParseProblem(
                        "invalid_chunk_size_decision",
                        line_no,
                        "size decision must use '<units> · <status>' or '— · group'",
                    )
                )
                continue
            units = int(size_match.group(1))
            size_status = size_match.group(2)
            reason = (size_match.group(3) or "").strip()
            accepted = size_status in {"accepted-under", "accepted-over"}
            if accepted != bool(reason):
                problems.append(
                    ParseProblem(
                        "invalid_chunk_size_decision",
                        line_no,
                        "accepted decisions require one single-line reason after ' — '; other decisions cannot carry a reason",
                    )
                )
                continue

        if cells[4] not in {"pending", "reviewed"}:
            problems.append(
                ParseProblem(
                    "invalid_chunk_review_status",
                    line_no,
                    "content review status must be pending or reviewed",
                )
            )
            continue
        rows.append(
            IndexRow(
                line=line_no,
                target=target.strip(),
                label=label.strip(),
                title=cells[1],
                description=cells[2],
                units=units,
                size_status=size_status,
                reason=reason,
                review_status=cells[4],
            )
        )
    return rows, problems


def registry_blocks(text: str) -> list[re.Match[str]]:
    normalized = normalize_markdown_text(text)
    fenced_spans = fenced_code_spans(normalized)
    return [
        match
        for match in REGISTRY_RE.finditer(normalized)
        if not any(match.start() < end and match.end() > start for start, end in fenced_spans)
    ]


def fenced_code_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    fence_start: int | None = None
    fence_char: str | None = None
    fence_length = 0
    offset = 0
    for line in text.splitlines(keepends=True):
        opening = opening_fence(line) if fence_char is None else None
        if opening is not None:
            fence_start = offset
            fence_char, fence_length = opening
        elif fence_char is not None and is_closing_fence(line, fence_char, fence_length):
            spans.append((fence_start if fence_start is not None else offset, offset + len(line)))
            fence_start = None
            fence_char = None
            fence_length = 0
        offset += len(line)
    if fence_char is not None:
        spans.append((fence_start if fence_start is not None else offset, len(text)))
    return spans


def _valid_relative_chunk_path(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/"):
        return False
    pure = PurePosixPath(value)
    return pure.suffix == ".md" and pure.name != "index.md" and ".." not in pure.parts


def valid_review_ref(value: str) -> bool:
    if not value or value != value.strip() or "\\" in value or "\n" in value or "\r" in value:
        return False
    path_text, separator, fragment = value.partition("#")
    path = PurePosixPath(path_text)
    return bool(
        path.parts
        and path.parts[0] == "reviews"
        and not path.is_absolute()
        and ".." not in path.parts
        and path.suffix == ".md"
        and (not separator or bool(fragment))
    )


def parse_registry_text(text: str) -> tuple[dict | None, list[ParseProblem]]:
    matches = registry_blocks(text)
    if not matches:
        return None, []
    if len(matches) > 1:
        return None, [
            ParseProblem(
                "duplicate_chunk_exception",
                1,
                "root chunks/index.md contains more than one chunk-size-exceptions registry",
            )
        ]
    raw = matches[0].group(1)
    try:
        registry = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [
            ParseProblem(
                "malformed_chunk_exception",
                normalize_markdown_text(text)[: matches[0].start()].count("\n") + 1,
                f"chunk exception registry is not valid JSON: {exc.msg}",
            )
        ]

    if not isinstance(registry, dict) or set(registry) != {"schema", "policy", "items"}:
        return None, [
            ParseProblem(
                "malformed_chunk_exception",
                1,
                "registry must contain exactly schema, policy, and items",
            )
        ]
    policy = registry.get("policy")
    items = registry.get("items")
    if registry.get("schema") != REGISTRY_SCHEMA or not isinstance(policy, dict) or not isinstance(items, list):
        return None, [
            ParseProblem(
                "malformed_chunk_exception",
                1,
                "registry schema, policy, or items has the wrong type or version",
            )
        ]
    if set(policy) != {"min", "max", "units_algo"} or not isinstance(policy.get("min"), int) or not isinstance(
        policy.get("max"), int
    ) or not isinstance(policy.get("units_algo"), str):
        return None, [
            ParseProblem(
                "malformed_chunk_exception",
                1,
                "registry policy must contain integer min/max and string units_algo",
            )
        ]
    if policy["min"] < 1 or policy["max"] <= policy["min"]:
        return None, [
            ParseProblem(
                "malformed_chunk_exception",
                1,
                "registry policy must satisfy 0 < min < max",
            )
        ]

    problems: list[ParseProblem] = []
    seen: set[str] = set()
    for position, item in enumerate(items, start=1):
        if not isinstance(item, dict) or set(item) != {
            "path",
            "kind",
            "content_sha256",
            "reason_sha256",
            "review_ref",
        }:
            problems.append(
                ParseProblem(
                    "malformed_chunk_exception",
                    1,
                    f"registry item {position} has invalid fields",
                )
            )
            continue
        path = item.get("path")
        if not isinstance(path, str) or not _valid_relative_chunk_path(path):
            problems.append(
                ParseProblem(
                    "malformed_chunk_exception",
                    1,
                    f"registry item {position} has an invalid relative chunk path",
                )
            )
            continue
        if path in seen:
            problems.append(
                ParseProblem(
                    "duplicate_chunk_exception",
                    1,
                    f"registry has duplicate entries for {path}",
                )
            )
            continue
        seen.add(path)
        if item.get("kind") not in {"under", "over"}:
            problems.append(ParseProblem("malformed_chunk_exception", 1, f"registry item {path} has invalid kind"))
        if not isinstance(item.get("content_sha256"), str) or not SHA256_RE.fullmatch(item["content_sha256"]):
            problems.append(
                ParseProblem("malformed_chunk_exception", 1, f"registry item {path} has invalid content_sha256")
            )
        if not isinstance(item.get("reason_sha256"), str) or not SHA256_RE.fullmatch(item["reason_sha256"]):
            problems.append(
                ParseProblem("malformed_chunk_exception", 1, f"registry item {path} has invalid reason_sha256")
            )
        review_ref = item.get("review_ref")
        if not isinstance(review_ref, str) or not valid_review_ref(review_ref):
            problems.append(
                ParseProblem(
                    "malformed_chunk_exception",
                    1,
                    f"registry item {path} review_ref must be a vault-root-relative reviews/*.md reference",
                )
            )
    if problems:
        return None, problems
    return registry, []


def sha256_text(text: str) -> str:
    return hashlib.sha256(normalize_markdown_text(text).encode("utf-8")).hexdigest()


def render_registry(registry: dict) -> str:
    return "<!-- chunk-size-exceptions\n" + json.dumps(
        registry,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n-->"


def replace_registry(text: str, registry: dict | None) -> str:
    had_bom = text.startswith("\ufeff")
    newline = "\r\n" if "\r\n" in text else "\r" if "\r" in text else "\n"
    normalized = normalize_markdown_text(text)
    matches = registry_blocks(normalized)
    if len(matches) > 1:
        raise ValueError("cannot update duplicate chunk exception registries")
    replacement = render_registry(registry) if registry is not None else ""
    if matches:
        updated = normalized[: matches[0].start()] + replacement + normalized[matches[0].end() :]
    elif replacement:
        updated = normalized.rstrip() + "\n\n" + replacement + "\n"
    else:
        updated = normalized
    rendered = updated.rstrip() + "\n"
    if newline != "\n":
        rendered = rendered.replace("\n", newline)
    return ("\ufeff" if had_bom else "") + rendered


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
