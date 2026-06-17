#!/usr/bin/env python3
"""Run MinerU FastAPI parsing through /file_parse or /tasks."""

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

import requests

from api_common import api_url, env_value, parse_env_file


PROFILE_ID = "fastapi"
RUNNING_STATES = {"pending", "queued", "running", "processing", "waiting", "waiting-file", "converting"}
COMPLETE_STATES = {"completed", "complete", "success", "succeeded", "done"}
FAILED_STATES = {"failed", "error", "cancelled", "canceled"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
GENERATED_FILES = {"source.md", "full.md", "result.json", "result.zip", "batch-result.zip", "response.json", "batch.json"}
GENERATED_DIRS = {"images", "extracted"}
WATERMARK_MARKERS = ("watermark", "水印")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MinerU FastAPI parsing for local files.")
    parser.add_argument("--file", dest="files", action="append", required=True, help="Local file path. Repeat for batch parsing.")
    parser.add_argument("--output-dir", required=True, help="Directory for normalized output files.")
    parser.add_argument("--env-file", default=".env", help="Path to the project .env file.")
    parser.add_argument("--base-url", default="", help="Override MinerU FastAPI base URL.")
    parser.add_argument("--mode", choices=("sync", "async"), default="sync", help="Use /file_parse or /tasks.")
    parser.add_argument("--backend", default="", help="MinerU backend, such as pipeline, vlm-engine, or hybrid-http-client.")
    parser.add_argument("--lang-list", action="append", default=None, help="OCR language item. Repeat for multiple languages.")
    parser.add_argument("--parse-method", default="", help="auto, txt, or ocr.")
    parser.add_argument("--effort", default="", help="Hybrid backend effort, such as medium or high.")
    parser.add_argument("--server-url", default="", help="OpenAI-compatible VLM server URL for *-http-client backends.")
    parser.add_argument("--formula-enable", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--table-enable", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--image-analysis", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--return-md", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--return-images", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--response-format-zip", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--return-content-list", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--return-middle-json", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--return-model-output", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--return-original-file", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--client-side-output-generation", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--start-page-id", type=int, default=None)
    parser.add_argument("--end-page-id", type=int, default=None)
    parser.add_argument("--max-files-per-run", type=int, default=0, help="Local file count precheck. Set 0 to disable.")
    parser.add_argument("--max-file-mb", type=float, default=0.0, help="Local file-size precheck. Set 0 to disable.")
    parser.add_argument("--timeout", type=float, default=600.0, help="HTTP timeout in seconds.")
    parser.add_argument("--poll-interval", type=float, default=10.0, help="Seconds between /tasks polls.")
    parser.add_argument("--max-wait", type=float, default=3600.0, help="Maximum async wait in seconds.")
    parser.add_argument("--user-agent", default="", help="Optional User-Agent for deployments behind filtering gateways.")
    parser.add_argument("--keep-result-zip", action="store_true", help="Keep result.zip.")
    parser.add_argument("--keep-all-extracted", action="store_true", help="Keep full extracted ZIP contents.")
    parser.add_argument("--keep-json-response", action="store_true", help="Keep response.json for JSON API responses.")
    return parser.parse_args(argv)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def request_headers(token: str, user_agent: str) -> dict[str, str]:
    headers = {"Accept": "*/*"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if user_agent:
        headers["User-Agent"] = user_agent
    return headers


def resolve_base_url(args: argparse.Namespace, env_values: dict[str, str]) -> str:
    return args.base_url.strip() or env_value("MINERU_FASTAPI_BASE_URL", env_values)


def resolve_server_url(args: argparse.Namespace, env_values: dict[str, str]) -> str:
    return args.server_url.strip() or env_value("MINERU_FASTAPI_SERVER_URL", env_values)


def file_paths_from_args(args: argparse.Namespace) -> list[Path]:
    return [Path(raw).expanduser().resolve() for raw in args.files]


def require_input_files(file_paths: list[Path]) -> None:
    missing = [str(path) for path in file_paths if not path.is_file()]
    if missing:
        raise RuntimeError("missing input files: " + ", ".join(missing))


def require_prechecks(args: argparse.Namespace, file_paths: list[Path]) -> None:
    if args.max_files_per_run > 0 and len(file_paths) > args.max_files_per_run:
        raise RuntimeError(f"this FastAPI runner accepts up to {args.max_files_per_run} files per invocation; split the batch")
    seen: set[str] = set()
    for file_path in file_paths:
        base_name = file_path.stem
        if base_name in seen:
            raise RuntimeError(f"duplicate original base filename {base_name}; split the batch")
        seen.add(base_name)
        if args.max_file_mb > 0 and file_path.stat().st_size > int(args.max_file_mb * 1024 * 1024):
            raise RuntimeError(f"{file_path.name} exceeds the configured {args.max_file_mb:g} MB file-size limit")


def build_form_fields(args: argparse.Namespace, server_url: str) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    scalar_values = {
        "backend": args.backend.strip(),
        "parse_method": args.parse_method.strip(),
        "effort": args.effort.strip(),
        "server_url": server_url.strip(),
    }
    for key, value in scalar_values.items():
        if value:
            fields.append((key, value))
    for value in args.lang_list or []:
        if value.strip():
            fields.append(("lang_list", value.strip()))
    bool_values = {
        "formula_enable": args.formula_enable,
        "table_enable": args.table_enable,
        "image_analysis": args.image_analysis,
        "return_md": args.return_md,
        "return_images": args.return_images,
        "response_format_zip": args.response_format_zip,
        "return_content_list": args.return_content_list,
        "return_middle_json": args.return_middle_json,
        "return_model_output": args.return_model_output,
        "return_original_file": args.return_original_file,
        "client_side_output_generation": args.client_side_output_generation,
    }
    for key, value in bool_values.items():
        if value is not None:
            fields.append((key, bool_text(value)))
    if args.start_page_id is not None:
        fields.append(("start_page_id", str(args.start_page_id)))
    if args.end_page_id is not None:
        fields.append(("end_page_id", str(args.end_page_id)))
    return fields


def post_multipart(
    *,
    base_url: str,
    path: str,
    token: str,
    user_agent: str,
    file_paths: list[Path],
    fields: list[tuple[str, str]],
    timeout: float,
) -> requests.Response:
    handles = []
    files = []
    try:
        for file_path in file_paths:
            handle = file_path.open("rb")
            handles.append(handle)
            files.append(("files", (file_path.name, handle, "application/octet-stream")))
        return requests.post(
            api_url(base_url, path),
            data=fields,
            files=files,
            headers=request_headers(token, user_agent),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"request failed: {type(exc).__name__}") from exc
    finally:
        for handle in handles:
            handle.close()


def get_json(*, base_url: str, path: str, token: str, user_agent: str, timeout: float) -> tuple[int, Any]:
    try:
        response = requests.get(api_url(base_url, path), headers=request_headers(token, user_agent), timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"request failed: {type(exc).__name__}") from exc
    return response.status_code, response_json(response)


def get_response(*, base_url: str, path: str, token: str, user_agent: str, timeout: float) -> requests.Response:
    try:
        return requests.get(api_url(base_url, path), headers=request_headers(token, user_agent), timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"request failed: {type(exc).__name__}") from exc


def response_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("invalid JSON response from configured endpoint") from exc


def is_zip_response(response: requests.Response) -> bool:
    content_type = response.headers.get("content-type", "").lower()
    return "zip" in content_type or "octet-stream" in content_type


def is_json_response(response: requests.Response) -> bool:
    return "json" in response.headers.get("content-type", "").lower()


def clean_generated_outputs(output_dir: Path) -> None:
    for name in GENERATED_FILES:
        (output_dir / name).unlink(missing_ok=True)
    for name in GENERATED_DIRS:
        path = output_dir / name
        if path.exists():
            shutil.rmtree(path)


def clean_batch_output_root(output_dir: Path, file_paths: list[Path]) -> None:
    clean_generated_outputs(output_dir)
    for file_path in file_paths:
        path = output_dir / file_path.stem
        if path.exists():
            shutil.rmtree(path)


def safe_zip_member_path(member_name: str) -> PurePosixPath:
    if "\\" in member_name:
        raise RuntimeError(f"unsafe zip member path: {member_name}")
    path = PurePosixPath(member_name)
    if path.is_absolute() or ".." in path.parts or any(":" in part for part in path.parts):
        raise RuntimeError(f"unsafe zip member path: {member_name}")
    return path


def safe_output_path(root: Path, *parts: str) -> Path:
    target = root.joinpath(*parts)
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    if target_resolved != root_resolved and root_resolved not in target_resolved.parents:
        raise RuntimeError(f"unsafe output path: {target}")
    return target


def markdown_members(archive: zipfile.ZipFile) -> list[str]:
    members = []
    for member in archive.namelist():
        path = safe_zip_member_path(member)
        if path.suffix.lower() == ".md" and "__MACOSX" not in path.parts:
            members.append(member)
    return members


def choose_markdown_member(candidates: list[str], file_path: Path, *, total: int) -> str:
    if not candidates:
        raise RuntimeError("result zip contains no Markdown file")
    base = file_path.stem.lower()
    exact = [member for member in candidates if PurePosixPath(member).stem.lower() == base]
    if len(exact) == 1:
        return exact[0]
    in_path = [member for member in candidates if base in [part.lower() for part in PurePosixPath(member).parts]]
    if len(in_path) == 1:
        return in_path[0]
    if total == 1 and len(candidates) == 1:
        return candidates[0]
    raise RuntimeError(f"could not identify Markdown result for {file_path.name}")


def review_reasons_for_markdown(text: str) -> list[str]:
    lowered = text.lower()
    for marker in WATERMARK_MARKERS:
        if marker in text or marker in lowered:
            return ["possible watermark text detected in full.md"]
    return []


def copy_zip_images(archive: zipfile.ZipFile, md_member: str, output_dir: Path) -> list[str]:
    md_parent = safe_zip_member_path(md_member).parent
    copied: list[str] = []
    for member in archive.namelist():
        path = safe_zip_member_path(member)
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if len(path.parts) < 2 or "images" not in path.parts:
            continue
        try:
            images_index = path.parts.index("images")
        except ValueError:
            continue
        if PurePosixPath(*path.parts[:images_index]) != md_parent:
            continue
        relative = PurePosixPath(*path.parts[images_index + 1 :])
        target = safe_output_path(output_dir, "images", *relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(member))
        copied.append(str(PurePosixPath("images", *relative.parts)))
    return copied


def extract_all_members(archive: zipfile.ZipFile, output_dir: Path) -> None:
    extracted_dir = output_dir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    for member in archive.namelist():
        member_path = safe_zip_member_path(member)
        if member.endswith("/"):
            continue
        target = safe_output_path(extracted_dir, *member_path.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(member))


def build_result_metadata(
    *,
    mode: str,
    file_path: Path,
    status: str,
    task_id: str = "",
    http_status: int = 0,
    content_type: str = "",
    backend: str = "",
    parse_method: str = "",
    preserved_outputs: list[str] | None = None,
    review_reasons: list[str] | None = None,
    error: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reasons = list(review_reasons or [])
    if error:
        reasons.append(error)
    metadata: dict[str, Any] = {
        "profile_id": PROFILE_ID,
        "mode": mode,
        "file_name": file_path.name,
        "task_id": task_id,
        "status": status,
        "http_status": http_status,
        "content_type": content_type,
        "backend": backend,
        "parse_method": parse_method,
        "needs_review": bool(reasons),
        "review_reasons": reasons,
        "preserved_outputs": preserved_outputs or [],
    }
    if error:
        metadata["error"] = error
    if extra:
        metadata.update(extra)
    return metadata


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_markdown_output(
    *,
    output_dir: Path,
    markdown_text: str,
    mode: str,
    file_path: Path,
    task_id: str,
    http_status: int,
    content_type: str,
    backend: str,
    parse_method: str,
    preserved_outputs: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "full.md").write_text(markdown_text, encoding="utf-8")
    (output_dir / "source.md").write_text(markdown_text, encoding="utf-8")
    if "full.md" not in preserved_outputs:
        preserved_outputs.insert(0, "full.md")
    if "source.md" not in preserved_outputs:
        preserved_outputs.insert(0, "source.md")
    metadata = build_result_metadata(
        mode=mode,
        file_path=file_path,
        task_id=task_id,
        status="completed",
        http_status=http_status,
        content_type=content_type,
        backend=backend,
        parse_method=parse_method,
        preserved_outputs=preserved_outputs,
        review_reasons=review_reasons_for_markdown(markdown_text),
        extra=extra,
    )
    write_json(output_dir / "result.json", metadata)
    return metadata


def process_zip_response(
    *,
    response: requests.Response,
    output_dir: Path,
    file_paths: list[Path],
    mode: str,
    task_id: str,
    backend: str,
    parse_method: str,
    keep_result_zip: bool,
    keep_all_extracted: bool,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if len(file_paths) > 1:
        clean_batch_output_root(output_dir, file_paths)
    target_dirs = [output_dir] if len(file_paths) == 1 else [output_dir / file_path.stem for file_path in file_paths]
    for target_dir in target_dirs:
        target_dir.mkdir(parents=True, exist_ok=True)
        clean_generated_outputs(target_dir)

    zip_path = output_dir / "result.zip" if len(file_paths) == 1 else output_dir / "batch-result.zip"
    zip_path.write_bytes(response.content)
    processed: list[dict[str, Any]] = []
    try:
        try:
            archive = zipfile.ZipFile(zip_path, "r")
        except zipfile.BadZipFile:
            for file_path, target_dir in zip(file_paths, target_dirs):
                metadata = build_result_metadata(
                    mode=mode,
                    file_path=file_path,
                    task_id=task_id,
                    status="failed",
                    http_status=response.status_code,
                    content_type=response.headers.get("content-type", ""),
                    backend=backend,
                    parse_method=parse_method,
                    error="parse response ZIP could not be opened",
                )
                write_json(target_dir / "result.json", metadata)
                processed.append(metadata)
            return processed
        with archive:
            try:
                candidates = markdown_members(archive)
            except RuntimeError as exc:
                for file_path, target_dir in zip(file_paths, target_dirs):
                    metadata = build_result_metadata(
                        mode=mode,
                        file_path=file_path,
                        task_id=task_id,
                        status="failed",
                        http_status=response.status_code,
                        content_type=response.headers.get("content-type", ""),
                        backend=backend,
                        parse_method=parse_method,
                        error=str(exc),
                    )
                    write_json(target_dir / "result.json", metadata)
                    processed.append(metadata)
                return processed
            for file_path, target_dir in zip(file_paths, target_dirs):
                try:
                    md_member = choose_markdown_member(candidates, file_path, total=len(file_paths))
                    markdown_text = archive.read(md_member).decode("utf-8", errors="replace")
                    copied_images = copy_zip_images(archive, md_member, target_dir)
                    if keep_all_extracted:
                        extract_all_members(archive, target_dir)
                    preserved = []
                    if copied_images:
                        preserved.append("images/")
                    if keep_all_extracted:
                        preserved.append("extracted/")
                    if keep_result_zip and len(file_paths) == 1:
                        preserved.append("result.zip")
                    metadata = normalize_markdown_output(
                        output_dir=target_dir,
                        markdown_text=markdown_text,
                        mode=mode,
                        file_path=file_path,
                        task_id=task_id,
                        http_status=response.status_code,
                        content_type=response.headers.get("content-type", ""),
                        backend=backend,
                        parse_method=parse_method,
                        preserved_outputs=preserved,
                        extra={"zip_markdown_member": md_member},
                    )
                except RuntimeError as exc:
                    metadata = build_result_metadata(
                        mode=mode,
                        file_path=file_path,
                        task_id=task_id,
                        status="failed",
                        http_status=response.status_code,
                        content_type=response.headers.get("content-type", ""),
                        backend=backend,
                        parse_method=parse_method,
                        error=str(exc),
                    )
                    write_json(target_dir / "result.json", metadata)
                processed.append(metadata)
    finally:
        if not keep_result_zip:
            zip_path.unlink(missing_ok=True)
    return processed


def result_for_file(payload: dict[str, Any], file_path: Path, *, total: int) -> dict[str, Any] | None:
    results = payload.get("results")
    if isinstance(results, dict):
        if file_path.name in results and isinstance(results[file_path.name], dict):
            return results[file_path.name]
        for key, value in results.items():
            if Path(str(key)).stem == file_path.stem and isinstance(value, dict):
                return value
    if total == 1:
        if "md_content" in payload:
            return payload
        if isinstance(results, dict) and len(results) == 1:
            value = next(iter(results.values()))
            if isinstance(value, dict):
                return value
    return None


def process_json_response(
    *,
    response: requests.Response,
    output_dir: Path,
    file_paths: list[Path],
    mode: str,
    task_id: str,
    backend: str,
    parse_method: str,
    keep_json_response: bool,
) -> list[dict[str, Any]]:
    payload = response_json(response)
    if not isinstance(payload, dict):
        raise RuntimeError("JSON response is not an object")
    output_dir.mkdir(parents=True, exist_ok=True)
    if len(file_paths) > 1:
        clean_batch_output_root(output_dir, file_paths)
    target_dirs = [output_dir] if len(file_paths) == 1 else [output_dir / file_path.stem for file_path in file_paths]
    processed: list[dict[str, Any]] = []
    for file_path, target_dir in zip(file_paths, target_dirs):
        target_dir.mkdir(parents=True, exist_ok=True)
        clean_generated_outputs(target_dir)
        if keep_json_response and len(file_paths) == 1:
            write_json(target_dir / "response.json", payload)
        result = result_for_file(payload, file_path, total=len(file_paths))
        if not result:
            metadata = build_result_metadata(
                mode=mode,
                file_path=file_path,
                task_id=task_id,
                status=str(payload.get("status", "unknown")),
                http_status=response.status_code,
                content_type=response.headers.get("content-type", ""),
                backend=backend,
                parse_method=parse_method,
                error="JSON response contains no Markdown result for this file",
            )
            write_json(target_dir / "result.json", metadata)
            processed.append(metadata)
            continue
        markdown_text = str(result.get("md_content") or "")
        if not markdown_text:
            metadata = build_result_metadata(
                mode=mode,
                file_path=file_path,
                task_id=task_id,
                status=str(payload.get("status", "unknown")),
                http_status=response.status_code,
                content_type=response.headers.get("content-type", ""),
                backend=backend,
                parse_method=parse_method,
                error="JSON result contains no md_content",
                extra={"result_keys": sorted(result.keys())},
            )
            write_json(target_dir / "result.json", metadata)
            processed.append(metadata)
            continue
        extra = {
            "source_response_status": payload.get("status", ""),
            "result_keys": sorted(result.keys()),
        }
        if isinstance(result.get("content_list"), list):
            extra["content_list_count"] = len(result["content_list"])
        metadata = normalize_markdown_output(
            output_dir=target_dir,
            markdown_text=markdown_text,
            mode=mode,
            file_path=file_path,
            task_id=task_id or str(payload.get("task_id", "")),
            http_status=response.status_code,
            content_type=response.headers.get("content-type", ""),
            backend=backend,
            parse_method=parse_method,
            preserved_outputs=["response.json"] if keep_json_response else [],
            extra=extra,
        )
        processed.append(metadata)
    if keep_json_response and len(file_paths) > 1:
        write_json(output_dir / "response.json", payload)
    return processed


def write_batch_metadata(output_dir: Path, metadata: dict[str, Any]) -> None:
    write_json(output_dir / "batch.json", metadata)


def process_response(
    *,
    response: requests.Response,
    output_dir: Path,
    file_paths: list[Path],
    mode: str,
    task_id: str,
    backend: str,
    parse_method: str,
    keep_result_zip: bool,
    keep_all_extracted: bool,
    keep_json_response: bool,
) -> list[dict[str, Any]]:
    if response.status_code >= 400:
        raise RuntimeError(f"parse request failed with HTTP {response.status_code}")
    if is_zip_response(response):
        return process_zip_response(
            response=response,
            output_dir=output_dir,
            file_paths=file_paths,
            mode=mode,
            task_id=task_id,
            backend=backend,
            parse_method=parse_method,
            keep_result_zip=keep_result_zip,
            keep_all_extracted=keep_all_extracted,
        )
    if is_json_response(response):
        return process_json_response(
            response=response,
            output_dir=output_dir,
            file_paths=file_paths,
            mode=mode,
            task_id=task_id,
            backend=backend,
            parse_method=parse_method,
            keep_json_response=keep_json_response,
        )
    raise RuntimeError("parse response was neither ZIP nor JSON")


def run_sync(
    *,
    args: argparse.Namespace,
    base_url: str,
    token: str,
    user_agent: str,
    file_paths: list[Path],
    fields: list[tuple[str, str]],
) -> requests.Response:
    return post_multipart(
        base_url=base_url,
        path="/file_parse",
        token=token,
        user_agent=user_agent,
        file_paths=file_paths,
        fields=fields,
        timeout=args.timeout,
    )


def run_async(
    *,
    args: argparse.Namespace,
    base_url: str,
    token: str,
    user_agent: str,
    file_paths: list[Path],
    fields: list[tuple[str, str]],
    output_dir: Path,
) -> tuple[str, requests.Response, list[dict[str, Any]]]:
    submit_response = post_multipart(
        base_url=base_url,
        path="/tasks",
        token=token,
        user_agent=user_agent,
        file_paths=file_paths,
        fields=fields,
        timeout=args.timeout,
    )
    if submit_response.status_code not in (200, 201, 202):
        raise RuntimeError(f"task submission failed with HTTP {submit_response.status_code}")
    submit_payload = response_json(submit_response)
    if not isinstance(submit_payload, dict):
        raise RuntimeError("task submission returned non-json response")
    task_id = str(submit_payload.get("task_id", "")).strip()
    if not task_id:
        raise RuntimeError("task submission returned no task_id")

    history = [{"status": submit_payload.get("status", ""), "queued_ahead": submit_payload.get("queued_ahead")}]
    elapsed = 0.0
    while elapsed < args.max_wait:
        time.sleep(args.poll_interval)
        elapsed += args.poll_interval
        status_code, status_payload = get_json(
            base_url=base_url,
            path=f"/tasks/{task_id}",
            token=token,
            user_agent=user_agent,
            timeout=args.timeout,
        )
        if status_code >= 400 or not isinstance(status_payload, dict):
            continue
        status = str(status_payload.get("status", "unknown")).lower()
        history.append(
            {
                "status": status,
                "queued_ahead": status_payload.get("queued_ahead"),
                "elapsed_seconds": elapsed,
            }
        )
        if status in COMPLETE_STATES:
            result_response = get_response(
                base_url=base_url,
                path=f"/tasks/{task_id}/result",
                token=token,
                user_agent=user_agent,
                timeout=args.timeout,
            )
            return task_id, result_response, history
        if status in FAILED_STATES:
            error = str(status_payload.get("error") or status_payload.get("message") or status)
            write_batch_metadata(
                output_dir,
                {
                    "profile_id": PROFILE_ID,
                    "mode": "async",
                    "task_id": task_id,
                    "status_history": history,
                    "needs_review": True,
                    "error": error,
                },
            )
            raise RuntimeError(f"task failed: {error}")

    error = f"task did not finish after {args.max_wait:g} seconds"
    write_batch_metadata(
        output_dir,
        {
            "profile_id": PROFILE_ID,
            "mode": "async",
            "task_id": task_id,
            "status_history": history,
            "needs_review": True,
            "error": error,
        },
    )
    raise RuntimeError(error)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    env_values = parse_env_file(Path(args.env_file))
    base_url = resolve_base_url(args, env_values)
    token = env_value("MINERU_FASTAPI_TOKEN", env_values)
    server_url = resolve_server_url(args, env_values)
    user_agent = args.user_agent.strip() or env_value("MINERU_FASTAPI_USER_AGENT", env_values)
    if not base_url:
        print("missing MinerU FastAPI base URL; set MINERU_FASTAPI_BASE_URL or pass --base-url", file=sys.stderr)
        return 2

    file_paths = file_paths_from_args(args)
    output_dir = Path(args.output_dir)
    try:
        require_input_files(file_paths)
        require_prechecks(args, file_paths)
        fields = build_form_fields(args, server_url)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    backend = args.backend.strip()
    parse_method = args.parse_method.strip()
    try:
        if args.mode == "sync":
            task_id = ""
            status_history: list[dict[str, Any]] = []
            response = run_sync(
                args=args,
                base_url=base_url,
                token=token,
                user_agent=user_agent,
                file_paths=file_paths,
                fields=fields,
            )
        else:
            task_id, response, status_history = run_async(
                args=args,
                base_url=base_url,
                token=token,
                user_agent=user_agent,
                file_paths=file_paths,
                fields=fields,
                output_dir=output_dir,
            )
        results = process_response(
            response=response,
            output_dir=output_dir,
            file_paths=file_paths,
            mode=args.mode,
            task_id=task_id,
            backend=backend,
            parse_method=parse_method,
            keep_result_zip=args.keep_result_zip,
            keep_all_extracted=args.keep_all_extracted,
            keep_json_response=args.keep_json_response,
        )
        if args.mode == "async":
            write_batch_metadata(
                output_dir,
                {
                    "profile_id": PROFILE_ID,
                    "mode": "async",
                    "task_id": task_id,
                    "status_history": status_history,
                    "results": results,
                    "needs_review": any(item.get("needs_review") for item in results),
                },
            )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if any(item.get("needs_review") for item in results):
        print("one or more parsed files need review", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
