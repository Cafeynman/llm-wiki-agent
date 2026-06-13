import argparse
import json
import math
import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SETEXT_RE = re.compile(r"^(=+|-+)\s*$")


def content_units(text: str) -> int:
    return math.ceil(len(text.encode("utf-8")) / 3)


def extract_headings(text: str) -> list[str]:
    headings: list[str] = []
    in_fence = False
    pending_plain: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            pending_plain = None
            continue
        if in_fence:
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


def inspect_markdown(path: Path, threshold: int) -> dict:
    text = path.read_text(encoding="utf-8")
    units = content_units(text)
    headings = extract_headings(text)
    alerts: list[str] = []
    if units > threshold:
        alerts.append("large_source")
        if not headings:
            alerts.append("no_headings")
    return {
        "schema": 1,
        "path": path.as_posix(),
        "content_units": units,
        "heading_count": len(headings),
        "sample_headings": headings[:5],
        "alerts": alerts,
    }


def print_alert(stats: dict, threshold: int) -> None:
    if "large_source" not in stats["alerts"]:
        return
    print(
        f"large_source: {stats['path']} has {stats['content_units']} content units "
        f"(threshold {threshold}). Consider semantic chunking before Source Review Gate."
    )
    if stats["sample_headings"]:
        print("source_headings: " + " | ".join(stats["sample_headings"]))
    else:
        print("source_headings: no reliable Markdown headings detected")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report lightweight intake Markdown size alerts.")
    parser.add_argument("path", help="Path to an extracted intake source.md file.")
    parser.add_argument("--threshold", type=int, default=10000, help="Alert threshold in content units.")
    parser.add_argument("--json", action="store_true", help="Print minimal JSON stats when alerts are present.")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.is_file():
        print(f"missing file: {path}", file=sys.stderr)
        return 2

    stats = inspect_markdown(path, args.threshold)
    if args.json and stats["alerts"]:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    elif not args.json:
        print_alert(stats, args.threshold)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
