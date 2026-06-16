#!/usr/bin/env python3
"""Shared helpers for MinerU API-based profiles."""

from __future__ import annotations

import json
import os
import re
import socket
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import requests


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


def api_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def request_json(
    url: str,
    *,
    method: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
    timeout: float,
) -> tuple[int, Any]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, headers=headers, data=data, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read()
    except HTTPError as exc:
        status = exc.code
        body = exc.read()
    except (TimeoutError, socket.timeout, URLError) as exc:
        raise RuntimeError(f"request failed: {type(exc).__name__}") from exc

    text = body.decode("utf-8", errors="replace").strip()
    try:
        parsed = json.loads(text) if text else None
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON response from {url}") from exc
    return status, parsed


def request_bytes(url: str, *, timeout: float) -> bytes:
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except (HTTPError, TimeoutError, socket.timeout, URLError) as exc:
        raise RuntimeError(f"download failed: {type(exc).__name__}") from exc


def upload_file(upload_url: str, file_path: Path, *, timeout: float) -> int:
    try:
        with file_path.open("rb") as handle:
            response = requests.put(upload_url, data=handle, timeout=timeout)
        return response.status_code
    except requests.RequestException as exc:
        raise RuntimeError(f"upload failed: {type(exc).__name__}") from exc


def require_api_success(status: int, payload: Any, action: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RuntimeError(f"{action} returned an unstructured response")
    if status >= 400:
        raise RuntimeError(f"{action} failed with HTTP {status}: {payload.get('msg', 'unknown error')}")
    if payload.get("code") != 0:
        raise RuntimeError(f"{action} failed: {payload.get('msg', 'unknown error')}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"{action} returned no data object")
    return data


def sanitize_data_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.")
    return cleaned[:128] or "file"
