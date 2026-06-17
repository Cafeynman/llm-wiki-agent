#!/usr/bin/env python3
"""Run MinerU API parsing for local file upload, including batch mode."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from api_common import (
    api_headers,
    api_url,
    env_value,
    parse_env_file,
    request_bytes,
    request_json,
    require_api_success,
    sanitize_data_id,
    upload_file,
)


DEFAULT_MODEL_VERSION = "vlm"
DEFAULT_POLL_INTERVAL = 5.0
DEFAULT_TIMEOUT = 300.0
DEFAULT_MAX_LOCAL_UPLOAD_FILES = 0
DEFAULT_MAX_FILE_MB = 0.0
RUNNING_STATES = {"waiting-file", "pending", "running", "converting"}
DONE_STATE = "done"
WATERMARK_MARKERS = ("watermark", "水印")


class BatchTimeoutError(RuntimeError):
    def __init__(self, *, batch_id: str, max_polls: int, items: list[dict[str, Any]]):
        super().__init__(f"batch did not finish after {max_polls} polls")
        self.batch_id = batch_id
        self.items = items


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MinerU API parsing for one or more local files.")
    parser.add_argument(
        "--file",
        dest="files",
        action="append",
        required=True,
        help="Local file path to upload. Repeat for batch parsing.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for output files.")
    parser.add_argument("--env-file", default=".env", help="Path to the project .env file.")
    parser.add_argument("--base-url", default="", help="Override MinerU base URL for this run.")
    parser.add_argument("--docs-url", default="", help="Documentation URL configured by the selected profile.")
    parser.add_argument("--model-version", default=DEFAULT_MODEL_VERSION, help="API model_version.")
    parser.add_argument("--language", default="", help="Optional language value for OCR-sensitive extraction.")
    parser.add_argument(
        "--enable-formula",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable formula recognition.",
    )
    parser.add_argument(
        "--enable-table",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable table recognition.",
    )
    parser.add_argument("--is-ocr", action="store_true", help="Enable OCR for all uploaded files.")
    parser.add_argument(
        "--page-ranges",
        action="append",
        default=None,
        help="Optional page range. Provide once to apply to all files, or once per file in order.",
    )
    parser.add_argument(
        "--data-id",
        action="append",
        default=None,
        help="Optional data id. Provide once per file in order.",
    )
    parser.add_argument(
        "--extra-format",
        action="append",
        default=None,
        help="Optional extra export format. Repeat for docx, html, or latex.",
    )
    parser.add_argument("--callback", default="", help="Optional callback URL.")
    parser.add_argument("--seed", default="", help="Optional callback seed. Required when callback is set.")
    parser.add_argument("--no-cache", action="store_true", help="Disable server-side cache reuse when supported.")
    parser.add_argument("--cache-tolerance", type=int, default=None, help="Optional cache tolerance value.")
    parser.add_argument(
        "--max-files-per-batch",
        type=int,
        default=DEFAULT_MAX_LOCAL_UPLOAD_FILES,
        help="Local precheck for files per invocation. Set 0 to disable for another profile.",
    )
    parser.add_argument(
        "--max-file-mb",
        type=float,
        default=DEFAULT_MAX_FILE_MB,
        help="Local precheck for each uploaded file size in MB. Set 0 to disable for another profile.",
    )
    parser.add_argument("--keep-result-zip", action="store_true", help="Keep the downloaded MinerU result zip.")
    parser.add_argument(
        "--keep-all-extracted",
        action="store_true",
        help="Keep every file from the MinerU result zip under extracted/.",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help="Seconds between batch-result polls.",
    )
    parser.add_argument("--max-polls", type=int, default=120, help="Maximum number of batch-result polls.")
    return parser.parse_args(argv)


def resolve_page_ranges(values: list[str], expected_count: int) -> list[str | None]:
    values = values or []
    if not values:
        return [None] * expected_count
    if len(values) == 1:
        return [values[0].strip() or None] * expected_count
    if len(values) != expected_count:
        raise RuntimeError("--page-ranges must be provided once or once per file")
    return [value.strip() or None for value in values]


def resolve_data_ids(values: list[str], file_paths: list[Path]) -> list[str]:
    values = values or []
    if values and len(values) != len(file_paths):
        raise RuntimeError("--data-id must be omitted or provided once per file")

    used: set[str] = set()
    resolved: list[str] = []
    for index, file_path in enumerate(file_paths):
        base = values[index] if values else sanitize_data_id(file_path.stem)
        candidate = sanitize_data_id(base)
        suffix = 2
        while candidate in used:
            candidate = sanitize_data_id(f"{base}-{suffix}")
            suffix += 1
        used.add(candidate)
        resolved.append(candidate)
    return resolved


def require_unique_output_basenames(file_paths: list[Path]) -> None:
    if len(file_paths) <= 1:
        return
    seen: dict[str, Path] = {}
    for file_path in file_paths:
        base_name = file_path.stem
        if base_name in seen:
            raise RuntimeError(
                f"duplicate original base filename {base_name}; split the batch so each output directory is unambiguous"
            )
        seen[base_name] = file_path


def build_file_specs(args: argparse.Namespace, file_paths: list[Path]) -> list[dict[str, Any]]:
    if args.max_files_per_batch > 0 and len(file_paths) > args.max_files_per_batch:
        raise RuntimeError(
            f"this local upload runner accepts up to {args.max_files_per_batch} files per invocation; split the batch and rerun"
        )
    require_unique_output_basenames(file_paths)

    page_ranges = resolve_page_ranges(args.page_ranges, len(file_paths))
    data_ids = resolve_data_ids(args.data_id, file_paths)
    file_specs: list[dict[str, Any]] = []
    for file_path, data_id, page_range in zip(file_paths, data_ids, page_ranges):
        file_size = file_path.stat().st_size
        max_file_bytes = int(args.max_file_mb * 1024 * 1024)
        if args.max_file_mb > 0 and file_size > max_file_bytes:
            raise RuntimeError(f"{file_path.name} exceeds the configured {args.max_file_mb:g} MB file-size limit")
        item: dict[str, Any] = {"name": file_path.name, "data_id": data_id}
        if args.is_ocr:
            item["is_ocr"] = True
        if page_range:
            item["page_ranges"] = page_range
        file_specs.append({"path": file_path, "request": item})
    return file_specs


def build_request_payload(args: argparse.Namespace, file_specs: list[dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "files": [dict(spec["request"]) for spec in file_specs],
        "model_version": args.model_version,
    }
    if args.language:
        payload["language"] = args.language
    if args.enable_formula is not None:
        payload["enable_formula"] = args.enable_formula
    if args.enable_table is not None:
        payload["enable_table"] = args.enable_table
    if args.extra_format:
        payload["extra_formats"] = list(args.extra_format)
    if args.callback:
        payload["callback"] = args.callback
    if args.seed:
        payload["seed"] = args.seed
    if args.no_cache:
        payload["no_cache"] = True
    if args.cache_tolerance is not None:
        payload["cache_tolerance"] = args.cache_tolerance
    return payload


def create_upload_batch(*, base_url: str, token: str, payload: dict[str, Any], timeout: float) -> tuple[str, list[str]]:
    status, response_payload = request_json(
        api_url(base_url, "/api/v4/file-urls/batch"),
        method="POST",
        headers=api_headers(token),
        payload=payload,
        timeout=timeout,
    )
    data = require_api_success(status, response_payload, "upload-url request")
    batch_id = str(data.get("batch_id", "")).strip()
    upload_urls = data.get("file_urls")
    if not batch_id:
        raise RuntimeError("upload-url request returned no batch_id")
    if not isinstance(upload_urls, list) or not all(isinstance(item, str) and item.strip() for item in upload_urls):
        raise RuntimeError("upload-url request returned invalid file_urls")
    return batch_id, [item.strip() for item in upload_urls]


def upload_files(upload_urls: list[str], file_paths: list[Path], *, timeout: float) -> None:
    if len(upload_urls) != len(file_paths):
        raise RuntimeError("upload-url count does not match file count")
    for upload_url, file_path in zip(upload_urls, file_paths):
        status = upload_file(upload_url, file_path, timeout=timeout)
        if not 200 <= status < 300:
            raise RuntimeError(f"upload failed for {file_path.name} with HTTP {status}")


def get_batch_result(*, base_url: str, token: str, batch_id: str, timeout: float) -> dict[str, Any]:
    status, response_payload = request_json(
        api_url(base_url, f"/api/v4/extract-results/batch/{batch_id}"),
        method="GET",
        headers=api_headers(token),
        timeout=timeout,
    )
    return require_api_success(status, response_payload, "batch polling")


def extract_result_items(batch_data: dict[str, Any]) -> list[dict[str, Any]]:
    items = batch_data.get("extract_result")
    if items is None:
        items = batch_data.get("extract_results")
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise RuntimeError("batch polling returned no extract_result list")
    return list(items)


def poll_batch_until_terminal(
    *,
    base_url: str,
    token: str,
    batch_id: str,
    timeout: float,
    poll_interval: float,
    max_polls: int,
    expected_count: int,
) -> list[dict[str, Any]]:
    last_items: list[dict[str, Any]] = []
    for attempt in range(max_polls):
        batch_data = get_batch_result(base_url=base_url, token=token, batch_id=batch_id, timeout=timeout)
        items = extract_result_items(batch_data)
        last_items = items
        states = [str(item.get("state", "")).strip().lower() for item in items]
        if len(items) >= expected_count and all(state not in RUNNING_STATES for state in states):
            return items
        if attempt < max_polls - 1:
            time.sleep(poll_interval)
    raise BatchTimeoutError(batch_id=batch_id, max_polls=max_polls, items=last_items)


def item_output_dir(output_dir: Path, file_name: str, total: int) -> Path:
    if total == 1:
        return output_dir
    return output_dir / Path(file_name).stem


def clean_generated_outputs(output_dir: Path) -> None:
    for relative_path in ("source.md", "full.md", "result.json", "result.zip"):
        (output_dir / relative_path).unlink(missing_ok=True)
    for relative_path in ("images", "extracted"):
        path = output_dir / relative_path
        if path.exists():
            shutil.rmtree(path)
    for path in output_dir.iterdir():
        if not path.is_file():
            continue
        lowered = path.name.lower()
        if (
            lowered.endswith(".zip")
            or lowered.endswith(".pdf")
            or lowered in {"layout.json", "model.json", "middle.json"}
            or lowered.startswith(("layout", "model", "content_list"))
            or re.search(r"_(origin|layout|model|middle|content_list)(\.[^.]+)?$", lowered)
        ):
            path.unlink()


def clean_batch_output_root(output_dir: Path, file_specs: list[dict[str, Any]]) -> None:
    expected_names = {Path(str(spec["request"].get("name", ""))).stem for spec in file_specs}
    for path in output_dir.iterdir():
        if not path.is_dir() or path.name in expected_names:
            continue
        if re.match(r"^\d{3}-", path.name) or any((path / marker).exists() for marker in ("source.md", "full.md", "result.json")):
            shutil.rmtree(path)


def download_result_zip(*, zip_url: str, output_dir: Path, timeout: float) -> Path:
    zip_path = output_dir / "result.zip"
    zip_path.write_bytes(request_bytes(zip_url, timeout=timeout))
    return zip_path


def zip_member_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"unsafe zip member path: {name}")
    return path


def write_zip_member(archive: zipfile.ZipFile, member_name: str, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(archive.read(member_name))


def choose_full_markdown_member(archive: zipfile.ZipFile) -> str:
    full_md_candidates = [
        name
        for name in archive.namelist()
        if not name.endswith("/") and PurePosixPath(name).name == "full.md"
    ]
    if not full_md_candidates:
        raise RuntimeError("MinerU result zip did not contain full.md")
    return min(full_md_candidates, key=lambda item: (len(PurePosixPath(item).parts), len(item)))


def image_member_relative_path(member_path: PurePosixPath, full_md_path: PurePosixPath) -> PurePosixPath | None:
    full_parent = full_md_path.parent
    if full_parent.parts and member_path.parts[: len(full_parent.parts)] == full_parent.parts:
        relative_parts = member_path.parts[len(full_parent.parts) :]
        if relative_parts and relative_parts[0] == "images":
            return PurePosixPath(*relative_parts)

    if "images" not in member_path.parts:
        return None
    images_index = member_path.parts.index("images")
    return PurePosixPath(*member_path.parts[images_index:])


def copy_selected_images(archive: zipfile.ZipFile, full_md_member: str, output_dir: Path) -> bool:
    full_md_path = zip_member_path(full_md_member)
    copied = False
    for member_name in archive.namelist():
        if member_name.endswith("/"):
            continue
        member_path = zip_member_path(member_name)
        relative_path = image_member_relative_path(member_path, full_md_path)
        if relative_path is None:
            continue
        write_zip_member(archive, member_name, output_dir.joinpath(*relative_path.parts))
        copied = True
    return copied


def extract_all_members(archive: zipfile.ZipFile, output_dir: Path) -> None:
    extracted_dir = output_dir / "extracted"
    for member_name in archive.namelist():
        if member_name.endswith("/"):
            continue
        member_path = zip_member_path(member_name)
        write_zip_member(archive, member_name, extracted_dir.joinpath(*member_path.parts))


def review_reasons_for_markdown(text: str) -> list[str]:
    lowered = text.lower()
    for marker in WATERMARK_MARKERS:
        if marker in text or marker in lowered:
            return ["possible watermark text detected in full.md"]
    return []


def extract_full_markdown(*, zip_path: Path, output_dir: Path, keep_all_extracted: bool) -> tuple[Path, list[str], list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as archive:
        full_md_member = choose_full_markdown_member(archive)
        full_md_bytes = archive.read(full_md_member)
        (output_dir / "full.md").write_bytes(full_md_bytes)
        copied_images = copy_selected_images(archive, full_md_member, output_dir)
        if keep_all_extracted:
            extract_all_members(archive, output_dir)

    markdown_text = full_md_bytes.decode("utf-8", errors="replace")
    source_path = output_dir / "source.md"
    source_path.write_text(markdown_text, encoding="utf-8")
    preserved_outputs = ["source.md", "full.md"]
    if copied_images:
        preserved_outputs.append("images/")
    if keep_all_extracted:
        preserved_outputs.append("extracted/")
    return source_path, review_reasons_for_markdown(markdown_text), preserved_outputs


def build_item_metadata(
    *,
    batch_id: str,
    item: dict[str, Any],
    model_version: str,
    review_reasons: list[str] | None = None,
    preserved_outputs: list[str] | None = None,
    extraction_error: str = "",
) -> dict[str, Any]:
    reasons = review_reasons or []
    metadata = {
        "batch_id": batch_id,
        "file_name": item.get("file_name", ""),
        "data_id": item.get("data_id", ""),
        "state": item.get("state", ""),
        "full_zip_url": item.get("full_zip_url", ""),
        "err_msg": item.get("err_msg", ""),
        "model_version": model_version,
        "needs_review": bool(reasons or extraction_error),
        "review_reasons": reasons,
        "preserved_outputs": preserved_outputs or [],
    }
    if extraction_error:
        metadata["extraction_error"] = extraction_error
    return metadata


def write_item_metadata(
    *,
    output_dir: Path,
    metadata: dict[str, Any],
) -> None:
    (output_dir / "result.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def write_batch_metadata(
    *,
    output_dir: Path,
    batch_id: str,
    payload: dict[str, Any],
    items: list[dict[str, Any]],
    error: str = "",
) -> None:
    metadata = {
        "batch_id": batch_id,
        "request": payload,
        "results": items,
        "needs_review": bool(error or any(item.get("needs_review") for item in items)),
    }
    if error:
        metadata["error"] = error
        metadata["review_reasons"] = [error]
    (output_dir / "batch.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def timeout_metadata_items(*, batch_id: str, payload: dict[str, Any], items: list[dict[str, Any]], error: str) -> list[dict[str, Any]]:
    model_version = str(payload.get("model_version", ""))
    if items:
        return [
            build_item_metadata(
                batch_id=batch_id,
                item=item,
                model_version=model_version,
                extraction_error=error,
            )
            for item in items
        ]
    return [
        build_item_metadata(
            batch_id=batch_id,
            item={"state": "timeout", "err_msg": error},
            model_version=model_version,
            extraction_error=error,
        )
    ]


def process_results(
    *,
    output_dir: Path,
    batch_id: str,
    file_specs: list[dict[str, Any]],
    payload: dict[str, Any],
    items: list[dict[str, Any]],
    timeout: float,
    keep_result_zip: bool,
    keep_all_extracted: bool,
) -> None:
    (output_dir / "batch.json").unlink(missing_ok=True)
    if len(file_specs) > 1:
        clean_batch_output_root(output_dir, file_specs)
    if len(items) != len(file_specs):
        raise RuntimeError(f"batch result count mismatch: expected {len(file_specs)}, got {len(items)}")

    results_by_data_id: dict[str, dict[str, Any]] = {}
    results_by_name: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        data_id = str(item.get("data_id", "")).strip()
        file_name = str(item.get("file_name", "")).strip()
        if data_id:
            results_by_data_id[data_id] = item
        if file_name:
            results_by_name.setdefault(file_name, []).append(item)

    failures: list[str] = []
    processed_items: list[dict[str, Any]] = []
    consumed_ids: set[int] = set()
    used_output_dirs: set[Path] = set()
    for spec in file_specs:
        request = spec["request"]
        expected_data_id = str(request.get("data_id", "")).strip()
        expected_name = str(request.get("name", "")).strip()
        item = results_by_data_id.get(expected_data_id)
        if item is None:
            candidates = results_by_name.get(expected_name, [])
            if len(candidates) == 1:
                item = candidates[0]
        if item is None:
            failures.append(f"{expected_name}: missing batch result")
            continue
        consumed_ids.add(id(item))

        file_name = str(item.get("file_name") or expected_name).strip()
        original_name = str(request.get("name") or expected_name).strip()
        item_dir = item_output_dir(output_dir, original_name, len(items))
        item_dir_key = item_dir.resolve()
        if item_dir_key in used_output_dirs:
            failures.append(f"{original_name}: duplicate output directory {item_dir.name}")
            continue
        used_output_dirs.add(item_dir_key)
        item_dir.mkdir(parents=True, exist_ok=True)
        clean_generated_outputs(item_dir)

        state = str(item.get("state", "")).strip().lower()
        if state != DONE_STATE:
            error = str(item.get("err_msg") or state or "unknown error")
            metadata = build_item_metadata(
                batch_id=batch_id,
                item=item,
                model_version=str(payload.get("model_version", "")),
                extraction_error=error,
            )
            write_item_metadata(output_dir=item_dir, metadata=metadata)
            processed_items.append(metadata)
            failures.append(f"{file_name}: {error}")
            continue

        zip_url = str(item.get("full_zip_url", "")).strip()
        if not zip_url:
            metadata = build_item_metadata(
                batch_id=batch_id,
                item=item,
                model_version=str(payload.get("model_version", "")),
                extraction_error="missing full_zip_url",
            )
            write_item_metadata(output_dir=item_dir, metadata=metadata)
            processed_items.append(metadata)
            failures.append(f"{file_name}: missing full_zip_url")
            continue
        zip_path = download_result_zip(zip_url=zip_url, output_dir=item_dir, timeout=timeout)
        try:
            _source_path, review_reasons, preserved_outputs = extract_full_markdown(
                zip_path=zip_path,
                output_dir=item_dir,
                keep_all_extracted=keep_all_extracted,
            )
            if keep_result_zip:
                preserved_outputs.append("result.zip")
            metadata = build_item_metadata(
                batch_id=batch_id,
                item=item,
                model_version=str(payload.get("model_version", "")),
                review_reasons=review_reasons,
                preserved_outputs=preserved_outputs,
            )
            write_item_metadata(output_dir=item_dir, metadata=metadata)
            processed_items.append(metadata)
        except RuntimeError as exc:
            metadata = build_item_metadata(
                batch_id=batch_id,
                item=item,
                model_version=str(payload.get("model_version", "")),
                extraction_error=str(exc),
            )
            write_item_metadata(output_dir=item_dir, metadata=metadata)
            processed_items.append(metadata)
            failures.append(f"{file_name}: {exc}")
        finally:
            if not keep_result_zip:
                zip_path.unlink(missing_ok=True)

    extra_results = [item for item in items if id(item) not in consumed_ids]
    if extra_results:
        failures.append("batch returned unexpected extra result items")
    write_batch_metadata(output_dir=output_dir, batch_id=batch_id, payload=payload, items=processed_items)
    if failures:
        raise RuntimeError("some files failed: " + "; ".join(failures))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.callback and not args.seed:
        print("--seed is required when --callback is set", file=sys.stderr)
        return 2

    env_values = parse_env_file(Path(args.env_file))
    token = env_value("MINERU_TOKEN", env_values)

    file_paths = [Path(raw).expanduser().resolve() for raw in args.files]
    missing = [str(path) for path in file_paths if not path.is_file()]
    if missing:
        print("missing input files: " + ", ".join(missing), file=sys.stderr)
        return 2

    base_url = args.base_url.strip() or env_value("MINERU_BASE_URL", env_values)
    docs_url = args.docs_url.strip() or env_value("MINERU_DOCS_URL", env_values)
    if not base_url:
        print("missing MinerU base URL; set MINERU_BASE_URL or pass --base-url for the selected profile", file=sys.stderr)
        return 2
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        file_specs = build_file_specs(args, file_paths)
        payload = build_request_payload(args, file_specs)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        batch_id, upload_urls = create_upload_batch(
            base_url=base_url,
            token=token,
            payload=payload,
            timeout=args.timeout,
        )
        upload_files(upload_urls, file_paths, timeout=args.timeout)
        items = poll_batch_until_terminal(
            base_url=base_url,
            token=token,
            batch_id=batch_id,
            timeout=args.timeout,
            poll_interval=args.poll_interval,
            max_polls=args.max_polls,
            expected_count=len(file_paths),
        )
        process_results(
            output_dir=output_dir,
            batch_id=batch_id,
            file_specs=file_specs,
            payload=payload,
            items=items,
            timeout=args.timeout,
            keep_result_zip=args.keep_result_zip,
            keep_all_extracted=args.keep_all_extracted,
        )
    except BatchTimeoutError as exc:
        error = str(exc)
        write_batch_metadata(
            output_dir=output_dir,
            batch_id=exc.batch_id,
            payload=payload,
            items=timeout_metadata_items(batch_id=exc.batch_id, payload=payload, items=exc.items, error=error),
            error=error,
        )
        print(error, file=sys.stderr)
        if docs_url:
            print("docs_url_configured=true", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        if docs_url:
            print("docs_url_configured=true", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
