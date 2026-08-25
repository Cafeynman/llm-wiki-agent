#!/usr/bin/env python3
"""Record or remove one reviewed chunk-size exception in chunks/index.md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path, PurePosixPath

from audit_intake_file import (
    DEFAULT_LARGE_SOURCE_THRESHOLD,
    UNITS_ALGO,
    content_units,
    read_markdown,
)
from chunk_contract import (
    DEFAULT_SMALL_CHUNK_THRESHOLD,
    REGISTRY_SCHEMA,
    atomic_write_text,
    parse_index_text,
    parse_registry_text,
    replace_registry,
    sha256_text,
    valid_review_ref,
)


def nearest_index_for(path: Path, chunks_dir: Path) -> Path | None:
    chunks_resolved = chunks_dir.resolve()
    current = path.parent.resolve()
    while current == chunks_resolved or chunks_resolved in current.parents:
        candidate = current / "index.md"
        if candidate.is_file():
            return candidate
        if current == chunks_resolved:
            break
        current = current.parent
    return None


def canonical_chunk_path(chunks_dir: Path, value: str) -> str:
    supplied = Path(value)
    if supplied.is_absolute():
        resolved = supplied.resolve()
    else:
        parts = PurePosixPath(value.replace("\\", "/")).parts
        if parts and parts[0] == "chunks":
            parts = parts[1:]
        if not parts or ".." in parts:
            raise ValueError("chunk path must be a relative leaf path inside chunks/")
        resolved = chunks_dir.joinpath(*parts).resolve()
    chunks_resolved = chunks_dir.resolve()
    if chunks_resolved not in resolved.parents or resolved.name == "index.md" or resolved.suffix != ".md":
        raise ValueError("chunk path must name one Markdown leaf inside chunks/")
    return resolved.relative_to(chunks_resolved).as_posix()


def load_registry(root_index: Path) -> tuple[str, dict | None]:
    with root_index.open("r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    registry, problems = parse_registry_text(text)
    if problems:
        details = "; ".join(problem.message for problem in problems)
        raise ValueError(f"cannot update malformed exception registry: {details}")
    return text, registry


def record_exception(
    root: Path,
    chunk_value: str,
    review_ref: str | None,
    minimum: int,
    maximum: int,
    *,
    remove: bool = False,
) -> str:
    if minimum < 1 or maximum <= minimum:
        raise ValueError("thresholds must satisfy 0 < min < max")
    chunks_dir = root / "chunks"
    root_index = chunks_dir / "index.md"
    if not root_index.is_file():
        raise ValueError("chunks/index.md is required before recording an exception")
    relative = canonical_chunk_path(chunks_dir, chunk_value)
    root_text, registry = load_registry(root_index)

    if remove:
        if registry is None:
            return "unchanged"
        remaining = [item for item in registry["items"] if item["path"] != relative]
        if len(remaining) == len(registry["items"]):
            return "unchanged"
        updated_registry = {**registry, "items": remaining} if remaining else None
        updated = replace_registry(root_text, updated_registry)
        atomic_write_text(root_index, updated)
        return "removed"

    if not review_ref or not valid_review_ref(review_ref):
        raise ValueError(
            "--review-ref must be a vault-root-relative POSIX reviews/*.md Source Review Gate reference"
        )
    leaf = chunks_dir / PurePosixPath(relative)
    if not leaf.is_file():
        raise ValueError(f"chunk leaf does not exist: {relative}")
    text = read_markdown(leaf)
    if not text.strip():
        raise ValueError("empty leaf chunks cannot receive size exceptions")
    units = content_units(text)
    kind = "under" if units < minimum else "over" if units > maximum else "normal"
    if kind == "normal":
        raise ValueError(f"chunk has {units} units and is within the configured thresholds")

    nearest_index = nearest_index_for(leaf, chunks_dir)
    if nearest_index is None:
        raise ValueError("chunk has no nearest index.md")
    rows, problems = parse_index_text(read_markdown(nearest_index))
    if problems:
        details = "; ".join(problem.message for problem in problems)
        raise ValueError(f"nearest index is not canonical: {details}")
    matching_rows = []
    for row in rows:
        resolved = nearest_index.parent.joinpath(row.target).resolve()
        if resolved == leaf.resolve():
            matching_rows.append(row)
    if len(matching_rows) != 1:
        raise ValueError("chunk must appear exactly once in its nearest canonical index")
    row = matching_rows[0]
    expected_status = f"accepted-{kind}"
    if row.size_status != expected_status or not row.reason:
        raise ValueError(
            f"nearest index row must first use '{expected_status} — <single-line reason>'"
        )
    if row.review_status != "reviewed":
        raise ValueError("nearest index row must be marked reviewed before recording an exception")
    if row.units != units:
        raise ValueError(f"nearest index records {row.units} units but the chunk currently has {units}")

    policy = {"min": minimum, "max": maximum, "units_algo": UNITS_ALGO}
    if registry is None:
        registry = {"schema": REGISTRY_SCHEMA, "policy": policy, "items": []}
    elif registry["policy"] != policy:
        if registry["items"]:
            raise ValueError(
                "registry policy differs from the requested thresholds; re-review and rebuild all exceptions together"
            )
        registry = {**registry, "policy": policy}

    entry = {
        "path": relative,
        "kind": kind,
        "content_sha256": sha256_text(text),
        "reason_sha256": sha256_text(row.reason.strip()),
        "review_ref": review_ref,
    }
    items_by_path = {item["path"]: item for item in registry["items"]}
    items_by_path[relative] = entry
    updated_registry = {**registry, "items": [items_by_path[path] for path in sorted(items_by_path)]}
    updated = replace_registry(root_text, updated_registry)
    if updated == root_text:
        return "unchanged"
    atomic_write_text(root_index, updated)
    return "recorded"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record or remove one Source Review Gate chunk-size exception."
    )
    parser.add_argument("path", type=Path, help="Chunked intake folder containing chunks/.")
    parser.add_argument("--chunk", required=True, help="Leaf path relative to chunks/.")
    parser.add_argument("--review-ref", help="Source Review Gate decision/reference; required when recording.")
    parser.add_argument(
        "--min-threshold",
        type=int,
        default=DEFAULT_SMALL_CHUNK_THRESHOLD,
        help="Soft minimum in normalized content units.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_LARGE_SOURCE_THRESHOLD,
        help="Hard maximum in normalized content units.",
    )
    parser.add_argument("--remove", action="store_true", help="Remove this path from the registry.")
    args = parser.parse_args(argv)

    try:
        outcome = record_exception(
            args.path,
            args.chunk,
            args.review_ref,
            args.min_threshold,
            args.threshold,
            remove=args.remove,
        )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"chunk exception not recorded: {exc}", file=sys.stderr)
        return 1
    print(f"{outcome}: {args.chunk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
