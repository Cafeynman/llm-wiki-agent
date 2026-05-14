# MarkItDown Setup

MarkItDown is installed through the project dependency set in `pyproject.toml`.

## Verify

Run from the project root:

```bash
uv run markitdown --help
```

## Optional OCR Setup

Use OCR only when the user explicitly approves OCR for the current task or project.

If OCR uses an OpenAI-compatible backend, configure required secrets in the project-root `.env` file. Common variables:

- `OPENAI_API_KEY`
- `MARKITDOWN_OCR_MODEL`

Run OCR commands from the project root with:

```bash
uv run --env-file .env markitdown ...
```

Do not store API keys in `PROJECT.md`, `WIKI.md`, `AGENTS.md`, `CLAUDE.md`, manifests, logs, wiki pages, or source cards.
