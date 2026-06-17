#!/usr/bin/env python3
"""Check a MinerU FastAPI-compatible deployment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from api_common import api_url, env_value, parse_env_file, request_json


def request_headers(token: str, user_agent: str) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if user_agent:
        headers["User-Agent"] = user_agent
    return headers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MinerU FastAPI /health route reachability.")
    parser.add_argument("--env-file", default=".env", help="Path to the project .env file.")
    parser.add_argument("--base-url", default="", help="Override MinerU FastAPI base URL for this check.")
    parser.add_argument("--requires-token", action="store_true", help="Fail before route checks when no token is configured.")
    parser.add_argument("--user-agent", default="", help="Optional User-Agent for deployments behind filtering gateways.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds.")
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    env_file_values = parse_env_file(env_path)
    base_url = args.base_url.strip() or env_value("MINERU_FASTAPI_BASE_URL", env_file_values)
    token = env_value("MINERU_FASTAPI_TOKEN", env_file_values)
    user_agent = args.user_agent.strip() or env_value("MINERU_FASTAPI_USER_AGENT", env_file_values)
    base_url_source = "argument" if args.base_url.strip() else "environment" if base_url else "missing"

    print("MinerU FastAPI profile smoke check")
    print(f"env_file_present={env_path.exists()}")
    print(f"base_url_source={base_url_source}")
    print(f"token_configured={bool(token)}")

    if args.requires_token and not token:
        print("health_route_valid=fail detail=required token is missing for the selected profile")
        return 2

    if not base_url:
        print("health_route_valid=fail detail=missing MinerU FastAPI base URL for the selected profile")
        return 2

    try:
        status, payload = request_json(
            api_url(base_url, "/health"),
            method="GET",
            headers=request_headers(token, user_agent),
            timeout=args.timeout,
        )
    except RuntimeError as exc:
        print(f"health_route_valid=fail detail={exc}")
        return 1

    if status >= 400:
        print(f"health_route_valid=fail http_status={status}")
        return 1
    if not isinstance(payload, dict):
        print("health_route_valid=fail detail=health route returned non-json response")
        return 1

    print(f"health_route_valid=ok http_status={status}")
    for key in ("protocol_version", "processing_window_size", "max_concurrent_requests"):
        if key in payload:
            print(f"{key}_present=true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
