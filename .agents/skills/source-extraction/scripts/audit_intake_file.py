import argparse
import json
import math
import re
import sys
from pathlib import Path


SCHEMA_VERSION = 2
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SETEXT_RE = re.compile(r"^(=+|-+)\s*$")
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---(?:\n|\Z)", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
WIKI_EMBED_RE = re.compile(r"!\[\[.*?\]\]", re.DOTALL)
REFERENCE_IMAGE_RE = re.compile(r"!\[([^\]\r\n]*)\](?:\[([^\]\r\n]*)\])?")
REFERENCE_DEFINITION_RE = re.compile(r"(?m)^[ \t]{0,3}\[([^\]\r\n]+)\]:[ \t]*\S.*$")
HTML_PICTURE_RE = re.compile(r"<picture\b[^>]*>.*?</picture\s*>", re.IGNORECASE | re.DOTALL)
HTML_MEDIA_TAG_RE = re.compile(r"<(?:img|source)\b[^>]*?/?>", re.IGNORECASE | re.DOTALL)
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
STRUCTURAL_MARKUP_RE = re.compile(r"[\s`*_~>#|\[\](){}:;,.!?'\"/\\+=-]+")
FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
KNOWN_PLACEHOLDER_RE = re.compile(
    r"(?im)^\s*(?:\[PLACEHOLDER:\s*extraction pending\]|TODO:\s*extract source|待提取正文|提取内容待补)\s*$"
)
KNOWN_CHUNK_STUB_RE = re.compile(
    r"完整评审面已按标题语义分块（\d+\s*块），见\s*\[chunks/index\.md\]\(chunks/index\.md\)。"
)
CONTENT_UNIT_BYTES = 3
DEFAULT_LARGE_SOURCE_THRESHOLD = 10000
SPARSE_PAYLOAD_CHAR_THRESHOLD = 40
UNITS_ALGO = "utf8-normalized-ceil-div3-v1"


class AuditArgumentError(ValueError):
    pass


class AuditArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise AuditArgumentError(message)


def normalize_markdown_text(text: str) -> str:
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_markdown(path: Path) -> str:
    return normalize_markdown_text(path.read_text(encoding="utf-8"))


def content_units(text: str) -> int:
    normalized = normalize_markdown_text(text)
    return math.ceil(len(normalized.encode("utf-8")) / CONTENT_UNIT_BYTES)


def opening_fence(line: str) -> tuple[str, int] | None:
    match = FENCE_OPEN_RE.match(line)
    if match is None:
        return None
    marker = match.group(1)
    return marker[0], len(marker)


def is_closing_fence(line: str, fence_char: str, fence_length: int) -> bool:
    return bool(
        re.fullmatch(
            rf"[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*",
            line.rstrip("\r\n"),
        )
    )


def extract_headings(text: str) -> list[str]:
    headings: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    pending_plain: str | None = None
    normalized = FRONTMATTER_RE.sub("", normalize_markdown_text(text))
    for line in normalized.splitlines():
        stripped = line.strip()
        if fence_char is not None:
            if is_closing_fence(line, fence_char, fence_length):
                fence_char = None
                fence_length = 0
            pending_plain = None
            continue
        opening = opening_fence(line)
        if opening is not None:
            fence_char, fence_length = opening
            pending_plain = None
            continue
        match = HEADING_RE.match(stripped)
        if match:
            title = match.group(2).strip().rstrip("#").strip()
            if title:
                headings.append(title)
            pending_plain = None
            continue
        if pending_plain and SETEXT_RE.match(stripped):
            headings.append(pending_plain)
            pending_plain = None
            continue
        pending_plain = stripped if stripped else None
    return headings


def issue(code: str, path: Path, message: str) -> dict:
    return {"code": code, "path": path.as_posix(), "message": message}


def reviewable_payload_characters(text: str) -> int:
    payload = normalize_markdown_text(text)
    payload = FRONTMATTER_RE.sub("", payload)
    payload = transform_outside_fences(payload, strip_media_and_html_markup)
    payload = strip_heading_and_fence_markup(payload)
    payload = MARKDOWN_LINK_RE.sub(lambda match: match.group(1), payload)
    return len(STRUCTURAL_MARKUP_RE.sub("", payload))


def normalize_reference_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def strip_media_and_html_markup(text: str) -> str:
    without_media = HTML_COMMENT_RE.sub("", text)
    without_media = WIKI_EMBED_RE.sub("", without_media)
    without_media = MARKDOWN_IMAGE_RE.sub("", without_media)
    referenced_labels: set[str] = set()
    for match in REFERENCE_IMAGE_RE.finditer(without_media):
        label = match.group(2) or match.group(1)
        referenced_labels.add(normalize_reference_label(label))
    without_media = REFERENCE_IMAGE_RE.sub("", without_media)

    def remove_image_definition(match: re.Match[str]) -> str:
        return "" if normalize_reference_label(match.group(1)) in referenced_labels else match.group(0)

    without_media = REFERENCE_DEFINITION_RE.sub(remove_image_definition, without_media)
    without_media = HTML_PICTURE_RE.sub("", without_media)
    without_media = HTML_MEDIA_TAG_RE.sub("", without_media)
    return HTML_TAG_RE.sub("", without_media)


def transform_outside_fences(text: str, transform) -> str:
    pieces: list[str] = []
    outside: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in normalize_markdown_text(text).splitlines(keepends=True):
        if fence_char is not None:
            pieces.append(line)
            if is_closing_fence(line, fence_char, fence_length):
                fence_char = None
                fence_length = 0
            continue
        opening = opening_fence(line)
        if opening is not None:
            pieces.append(transform("".join(outside)))
            outside = []
            pieces.append(line)
            fence_char, fence_length = opening
            continue
        outside.append(line)
    pieces.append(transform("".join(outside)))
    return "".join(pieces)


def strip_heading_and_fence_markup(text: str) -> str:
    lines = normalize_markdown_text(text).splitlines()
    payload_lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if fence_char is not None:
            if is_closing_fence(line, fence_char, fence_length):
                fence_char = None
                fence_length = 0
            else:
                payload_lines.append(line)
            index += 1
            continue
        opening = opening_fence(line)
        if opening is not None:
            fence_char, fence_length = opening
            index += 1
            continue
        if HEADING_RE.match(stripped):
            index += 1
            continue
        if stripped and index + 1 < len(lines) and SETEXT_RE.match(lines[index + 1].strip()):
            index += 2
            continue
        payload_lines.append(line)
        index += 1
    return "\n".join(payload_lines)


def is_known_navigation_stub(text: str) -> bool:
    return KNOWN_CHUNK_STUB_RE.search(normalize_markdown_text(text)) is not None


def inspect_markdown(path: Path, threshold: int) -> dict:
    text = read_markdown(path)
    units = content_units(text)
    headings = extract_headings(text)
    errors: list[dict] = []
    warnings: list[dict] = []
    payload_chars = 0

    if not text.strip():
        errors.append(issue("empty_source", path, "source.md is empty or whitespace-only"))
    elif is_known_navigation_stub(text):
        errors.append(
            issue(
                "navigation_stub_source",
                path,
                "source.md is a known chunk-navigation stub, not the canonical reviewable extraction",
            )
        )
    elif KNOWN_PLACEHOLDER_RE.search(text):
        errors.append(
            issue(
                "placeholder_source",
                path,
                "source.md contains a known extraction placeholder instead of reviewable content",
            )
        )
    else:
        payload_chars = reviewable_payload_characters(text)
        if payload_chars == 0:
            errors.append(
                issue(
                    "no_reviewable_text",
                    path,
                    "source.md has no reviewable text; image embeds and headings alone are not an extraction",
                )
            )
        elif payload_chars < SPARSE_PAYLOAD_CHAR_THRESHOLD:
            warnings.append(
                issue(
                    "sparse_reviewable_text",
                    path,
                    f"source.md has only {payload_chars} reviewable payload characters; verify extraction quality",
                )
            )

        if units > threshold:
            warnings.append(
                issue(
                    "large_source",
                    path,
                    f"source.md has {units} content units (threshold {threshold}); consider semantic chunking",
                )
            )
            if not headings:
                warnings.append(
                    issue(
                        "no_headings",
                        path,
                        "large source has no reliable Markdown headings for semantic navigation",
                    )
                )

    errors.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    warnings.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    status = "fail" if errors else "warn" if warnings else "pass"
    return {
        "schema": SCHEMA_VERSION,
        "path": path.as_posix(),
        "thresholds": {"large_source": threshold, "units_algo": UNITS_ALGO},
        "status": status,
        "content_units": units,
        "reviewable_payload_characters": payload_chars,
        "heading_count": len(headings),
        "sample_headings": headings[:5],
        "errors": errors,
        "warnings": warnings,
        "summary": {"errors": len(errors), "warnings": len(warnings)},
    }


def input_error(path: Path, code: str, message: str, threshold: int) -> dict:
    return {
        "schema": SCHEMA_VERSION,
        "path": path.as_posix(),
        "thresholds": {"large_source": threshold, "units_algo": UNITS_ALGO},
        "status": "fail",
        "content_units": None,
        "reviewable_payload_characters": None,
        "heading_count": None,
        "sample_headings": [],
        "errors": [issue(code, path, message)],
        "warnings": [],
        "summary": {"errors": 1, "warnings": 0},
    }


def print_human(stats: dict) -> None:
    for label in ("errors", "warnings"):
        for item in stats[label]:
            print(f"{label[:-1]}: {item['code']}: {item['path']}: {item['message']}")
    if any(item["code"] == "large_source" for item in stats["warnings"]):
        if stats["sample_headings"]:
            print("source_headings: " + " | ".join(stats["sample_headings"]))
        else:
            print("source_headings: no reliable Markdown headings detected")


def emit(stats: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print_human(stats)


def main(argv: list[str] | None = None) -> int:
    raw_args = sys.argv[1:] if argv is None else argv
    json_requested = "--json" in raw_args
    parser = AuditArgumentParser(description="Audit one extracted intake source.md file.")
    parser.add_argument("path", help="Path to an extracted intake source.md file.")
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_LARGE_SOURCE_THRESHOLD,
        help="Large-source warning threshold in normalized content units.",
    )
    parser.add_argument("--json", action="store_true", help="Always print audit JSON.")
    try:
        args = parser.parse_args(raw_args)
    except AuditArgumentError as exc:
        stats = input_error(
            Path("."),
            "invalid_arguments",
            f"invalid command arguments: {exc}",
            DEFAULT_LARGE_SOURCE_THRESHOLD,
        )
        if json_requested:
            emit(stats, True)
        else:
            print(f"invalid arguments: {exc}", file=sys.stderr)
        return 2

    path = Path(args.path)
    if args.threshold < 1:
        stats = input_error(path, "invalid_threshold", "threshold must be at least 1", args.threshold)
        emit(stats, args.json)
        return 2
    if not path.is_file():
        stats = input_error(path, "missing_input", "input source.md file does not exist", args.threshold)
        if args.json:
            emit(stats, True)
        else:
            print(f"missing file: {path}", file=sys.stderr)
        return 2

    try:
        stats = inspect_markdown(path, args.threshold)
    except (UnicodeDecodeError, OSError) as exc:
        stats = input_error(path, "unreadable_input", f"cannot read UTF-8 input: {exc}", args.threshold)
        if args.json:
            emit(stats, True)
        else:
            print(f"unreadable file: {path}: {exc}", file=sys.stderr)
        return 2

    emit(stats, args.json)
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
