#!/usr/bin/env python3
"""Check MinerU API reachability for the current upload-based MinerU path."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from api_common import api_headers, api_url, env_value, parse_env_file, request_json

AUTH_FAILURE_MARKERS = (
    "auth",
    "authorization",
    "bearer",
    "forbidden",
    "permission",
    "token",
    "unauthorized",
    "鉴权",
    "认证",
    "授权",
    "权限",
    "未登录",
)


def api_code(payload: Any) -> Any:
    return payload.get("code") if isinstance(payload, dict) else None


def api_message(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""

    parts = [payload.get("msg"), payload.get("message")]
    data = payload.get("data")
    if isinstance(data, dict):
        parts.extend([data.get("err_msg"), data.get("message")])
    return " ".join(str(part) for part in parts if part)


def is_structured_api_response(payload: Any) -> bool:
    return isinstance(payload, dict) and any(key in payload for key in ("code", "msg", "data"))


def is_auth_failure(status: int | None, payload: Any) -> bool:
    if status in (401, 403):
        return True
    message = api_message(payload).lower()
    return any(marker in message for marker in AUTH_FAILURE_MARKERS)


def check_upload_link_request(base_url: str, token: str, timeout: float) -> tuple[dict[str, Any], str | None]:
    try:
        status, payload = request_json(
            api_url(base_url, "/api/v4/file-urls/batch"),
            method="POST",
            headers=api_headers(token),
            payload={
                "files": [{"name": "smoke-check.pdf", "data_id": "smoke-check"}],
                "model_version": "vlm",
            },
            timeout=timeout,
        )
    except RuntimeError as exc:
        return {"name": "upload_link_request_valid", "ok": False, "detail": str(exc)}, None

    if not is_structured_api_response(payload):
        return {
            "name": "upload_link_request_valid",
            "ok": False,
            "detail": "route did not return a structured API response",
            "http_status": status,
            "api_code": api_code(payload),
        }, None

    if status >= 400 or is_auth_failure(status, payload):
        accepted = False
        detail = "API rejected the configured token" if token else "API rejected unauthenticated access"
    elif api_code(payload) != 0:
        accepted = False
        detail = api_message(payload) or "upload-link request failed"
    else:
        accepted = True
        detail = "API accepted the configured token" if token else "API accepted unauthenticated access"
    batch_id = payload.get("data", {}).get("batch_id") if isinstance(payload, dict) else None
    return ({
        "name": "upload_link_request_valid",
        "ok": accepted,
        "detail": detail,
        "http_status": status,
        "api_code": api_code(payload),
    }, str(batch_id).strip() if batch_id else None)


def check_batch_result_route(base_url: str, token: str, batch_id: str | None, timeout: float) -> dict[str, Any]:
    if not batch_id:
        return {
            "name": "batch_result_route_valid",
            "ok": False,
            "detail": "upload-link request did not return a batch_id",
        }

    try:
        status, payload = request_json(
            api_url(base_url, f"/api/v4/extract-results/batch/{batch_id}"),
            method="GET",
            headers=api_headers(token),
            timeout=timeout,
        )
    except RuntimeError as exc:
        return {"name": "batch_result_route_valid", "ok": False, "detail": str(exc)}

    return {
        "name": "batch_result_route_valid",
        "ok": is_structured_api_response(payload) and status < 400 and not is_auth_failure(status, payload),
        "detail": "route returned a structured API response"
        if is_structured_api_response(payload)
        else "route did not return a structured API response",
        "http_status": status,
        "api_code": api_code(payload),
    }


def print_result(result: dict[str, Any]) -> None:
    status = "ok" if result["ok"] else "fail"
    fields = [f"{result['name']}={status}", f"detail={result['detail']}"]
    if result.get("http_status") is not None:
        fields.append(f"http_status={result['http_status']}")
    if result.get("api_code") is not None:
        fields.append(f"api_code={result['api_code']}")
    print(" ".join(fields))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check MinerU upload-route reachability for the current MinerU API path."
    )
    parser.add_argument("--env-file", default=".env", help="Path to the project .env file.")
    parser.add_argument("--base-url", default="", help="Override MinerU base URL for this check.")
    parser.add_argument("--docs-url", default="", help="Documentation URL to print when the selected profile fails.")
    parser.add_argument("--requires-token", action="store_true", help="Fail before route checks when no token is configured.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds.")
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    env_file_values = parse_env_file(env_path)
    configured_base_url = args.base_url.strip() or env_value("MINERU_BASE_URL", env_file_values)
    base_url = configured_base_url
    base_url_source = "argument" if args.base_url.strip() else "environment" if configured_base_url else "missing"
    docs_url = args.docs_url.strip() or env_value("MINERU_DOCS_URL", env_file_values)
    token = env_value("MINERU_TOKEN", env_file_values)

    if not base_url:
        print("MinerU provider smoke check")
        print(f"env_file_present={env_path.exists()}")
        print(f"base_url_source={base_url_source}")
        print("upload_link_request_valid=fail detail=missing MinerU base URL for the selected profile")
        print("batch_result_route_valid=fail detail=upload-link request was skipped because base URL is missing")
        if docs_url:
            print(f"docs_url={docs_url}")
        return 2

    if args.requires_token and not token:
        upload_result = {
            "name": "upload_link_request_valid",
            "ok": False,
            "detail": "MINERU_TOKEN is missing for the selected profile",
        }
        results = [
            upload_result,
            {
                "name": "batch_result_route_valid",
                "ok": False,
                "detail": "upload-link request was skipped because MINERU_TOKEN is missing",
            },
        ]
    else:
        upload_result, batch_id = check_upload_link_request(base_url, token, args.timeout)
        results = [
            upload_result,
            check_batch_result_route(base_url, token, batch_id, args.timeout),
        ]

    print("MinerU provider smoke check")
    print(f"env_file_present={env_path.exists()}")
    print(f"base_url_source={base_url_source}")
    for result in results:
        print_result(result)

    if not all(result["ok"] for result in results):
        if docs_url:
            print(f"docs_url={docs_url}")
        print("next_action=Open the selected profile documentation to verify access rules, then configure local .env values required by that profile.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
