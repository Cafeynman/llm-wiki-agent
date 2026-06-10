# MarkItDown Setup

MarkItDown is installed through the project dependency set in `pyproject.toml`.

## Verify

Run from the project root:

```bash
uv run markitdown --help
```

## Optional OCR Setup

Use OCR only when the user explicitly approves OCR for the current task or project.

If OCR uses the documented OpenAI-compatible backend, configure these required variables in the project-root `.env` file:

- `OPENAI_API_KEY`
- `MARKITDOWN_OCR_MODEL`

Use `.env.example` as the non-secret template.

If another OCR backend is explicitly approved, its setup notes must name the required environment variables before extraction starts.

Run OCR commands from the project root with:

```bash
uv run --env-file .env markitdown ...
```

Do not store API keys in `PROJECT.md`, `WIKI.md`, `AGENTS.md`, `CLAUDE.md`, manifests, logs, wiki pages, or source cards. Agents may check whether required variables are present, but must not print or persist their values.
