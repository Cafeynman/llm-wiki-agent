#!/usr/bin/env python3
"""Check MinerU API reachability and API key acceptance without parsing files."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://mineru.net"
DOCS_URL = "https://mineru.net/apiManage/docs"
SYNTHETIC_TASK_ID = "__mineru_smoke_check__"
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


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_value(name: str, env_file_values: dict[str, str]) -> str:
    return os.environ.get(name, "").strip() or env_file_values.get(name, "").strip()


def api_url(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def request_json(url: str, headers: dict[str, str], timeout: float) -> tuple[bool, int | None, Any, str]:
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read(65536)
    except HTTPError as exc:
        status = exc.code
        body = exc.read(65536)
    except (TimeoutError, socket.timeout, URLError) as exc:
        return False, None, None, type(exc).__name__

    text = body.decode("utf-8", errors="replace").strip()
    try:
        payload = json.loads(text) if text else None
    except json.JSONDecodeError:
        payload = None
    return True, status, payload, ""


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


def check_agent_api(base_url: str, timeout: float) -> dict[str, Any]:
    reached, status, payload, error = request_json(
        api_url(base_url, f"/api/v1/agent/parse/{SYNTHETIC_TASK_ID}"),
        {"Accept": "application/json"},
        timeout,
    )
    if not reached:
        return {"name": "agent_api_reachable", "ok": False, "detail": f"request failed: {error}"}

    return {
        "name": "agent_api_reachable",
        "ok": is_structured_api_response(payload),
        "detail": "route returned a structured API response"
        if is_structured_api_response(payload)
        else "route did not return a structured API response",
        "http_status": status,
        "api_code": api_code(payload),
    }


def check_precision_api_key(base_url: str, token: str, timeout: float) -> dict[str, Any]:
    if not token:
        return {"name": "precision_api_key_valid", "ok": False, "detail": "MINERU_TOKEN is missing"}

    reached, status, payload, error = request_json(
        api_url(base_url, f"/api/v4/extract/task/{SYNTHETIC_TASK_ID}"),
        {"Accept": "application/json", "Authorization": f"Bearer {token}"},
        timeout,
    )
    if not reached:
        return {"name": "precision_api_key_valid", "ok": False, "detail": f"request failed: {error}"}
    if not is_structured_api_response(payload):
        return {
            "name": "precision_api_key_valid",
            "ok": False,
            "detail": "route did not return a structured API response",
            "http_status": status,
            "api_code": api_code(payload),
        }

    accepted = not is_auth_failure(status, payload)
    return {
        "name": "precision_api_key_valid",
        "ok": accepted,
        "detail": "API accepted the configured token" if accepted else "API rejected the configured token",
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check MinerU API reachability and API key validity without parsing files."
    )
    parser.add_argument("--env-file", default=".env", help="Path to the project .env file.")
    parser.add_argument("--base-url", default="", help="Override MinerU base URL for this check.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds.")
    args = parser.parse_args()

    env_path = Path(args.env_file)
    env_file_values = parse_env_file(env_path)
    configured_base_url = args.base_url.strip() or env_value("MINERU_BASE_URL", env_file_values)
    base_url = configured_base_url or DEFAULT_BASE_URL
    base_url_source = "argument" if args.base_url.strip() else "environment" if configured_base_url else "default"

    results = [
        check_agent_api(base_url, args.timeout),
        check_precision_api_key(base_url, env_value("MINERU_TOKEN", env_file_values), args.timeout),
    ]

    print("MinerU provider smoke check")
    print(f"env_file_present={env_path.exists()}")
    print(f"base_url_source={base_url_source}")
    for result in results:
        print_result(result)

    if not all(result["ok"] for result in results):
        print(f"docs_url={DOCS_URL}")
        print("next_action=Open the MinerU API documentation to verify or apply for API access, then configure MINERU_TOKEN locally in .env.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
