# MinerU API Reference

Use this reference only when MinerU REST API mode, API/key smoke checks, or official endpoint details are relevant. Keep `usage.md` as the provider-selection and wiki-intake contract.

Official documentation:

- <https://mineru.net/apiManage/docs>

Check the official documentation before changing endpoint names, request parameters, limits, or response handling. This file records the provider workflow used by this package; the official documentation remains the source of truth for current API behavior.

## User Link Policy

When MinerU API configuration is missing, invalid, or rejected, send the user the official API management documentation link so they can view setup instructions, apply for access, or regenerate the API key:

- <https://mineru.net/apiManage/docs>

Do not ask the user to paste secrets into chat. Ask them to copy `.env.example` to `.env` in the project root and fill `MINERU_TOKEN` locally. If the provider uses a private deployment, `MINERU_BASE_URL` also belongs in `.env`.

When an API request returns an error that appears to be caused by an invalid token, expired access, endpoint drift, or permission limits, include the same link in the user-facing message and ask the user to verify the key or current API instructions there.

## API Families

MinerU exposes two REST API families.

Precision API:

- Requires `Authorization: Bearer <MINERU_TOKEN>`.
- Supports single-file URL parsing and batch workflows.
- Main documented endpoints include `POST /api/v4/extract/task`, `GET /api/v4/extract/task/{task_id}`, `POST /api/v4/file-urls/batch`, and `POST /api/v4/extract/task/batch`.
- Returns a task result that can include `full_zip_url`; for ordinary document outputs, `full.md` is the Markdown result inside the zip.

Agent lightweight API:

- Does not use Authorization.
- Is IP-rate-limited and intended for lightweight agent workflows.
- Supports one file per request.
- Main documented endpoints include `POST /api/v1/agent/parse/url`, `POST /api/v1/agent/parse/file`, and `GET /api/v1/agent/parse/{task_id}`.
- Returns Markdown through `markdown_url` when a task reaches `done`.

## Basic Smoke Check

The basic smoke check verifies API reachability and whether the configured precision API key is accepted. It is intentionally not an end-to-end parse.

Use:

```bash
uv run python .agents/skills/source-extraction/references/providers/mineru/scripts/smoke_check.py
```

The check:

1. Reads `MINERU_TOKEN` from the environment or `.env`.
2. Reads `MINERU_BASE_URL` from the environment or `.env`; if absent, uses the public MinerU API host.
3. Calls a lightweight Agent API query route with a synthetic task id to verify the API route returns a structured response.
4. Calls the precision API task-query route with a synthetic task id and the configured token.
5. Treats authentication or authorization errors as an invalid API key.

The check does not:

- Submit a document URL.
- Request a signed upload URL.
- Upload a file.
- Create a parsing task.
- Poll a real task.
- Download Markdown or zip results.
- Print API keys, tokens, or private endpoint URLs.

Passing this smoke check means the provider endpoint is reachable and the configured token appears accepted by the precision API route. It does not prove extraction quality, account quota, model availability, OCR behavior, or end-to-end parsing.

## Extraction Boundary

When the user later asks for real REST API parsing, start from the original source path or URL and follow `usage.md` plus the official API documentation. Record provider mode, task id, OCR flags, warnings, missing content, and result URLs in the intake manifest or review notes. The REST API result still must be normalized into the WIKI intake output contract before Source Review Gate.
