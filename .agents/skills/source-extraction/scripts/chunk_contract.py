from __future__ import annotations

from dataclasses import dataclass
import re

from audit_intake_file import normalize_markdown_text


INDEX_COLUMNS = ("块", "标题与覆盖范围", "内容说明", "规模与尺寸裁决", "内容评审")
INDEX_LINK_RE = re.compile(r"^\[([^]]+)\]\(([^)]+)\)$")
SIZE_DECISION_RE = re.compile(
    r"^(\d+) · (normal|undersized|oversized|accepted-under|accepted-over)"
    r"(?: — (.+))?$"
)
GROUP_DECISION_RE = re.compile(r"^— · group$")
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
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
