# MarkItDown Setup

MarkItDown is installed from the committed project lockfile. Run local commands from the package root.

## Verify Local Mode

```bash
uv run markitdown --version
uv run markitdown --help
```

Local document conversion requires no provider credentials.

## Azure Document Intelligence

Azure Document Intelligence is optional and service-backed. Use it only when the project has selected that mode and the endpoint and credential are configured locally.

MarkItDown 0.1.6 reads `AZURE_API_KEY` when present; otherwise it uses `DefaultAzureCredential`. Keep any real key and private endpoint in the project-root `.env` file. The CLI requires the endpoint with `--endpoint` when `--use-docintel` is enabled:

```bash
uv run --env-file .env markitdown <input-file> --use-docintel --endpoint <endpoint> -o <output.md>
```

Package verification covers the installed Azure modules and CLI wiring only. Do not imply that the service path passed a live check unless the configured endpoint and credential were actually exercised.

Do not persist real credentials or private endpoint values in project instructions, manifests, logs, review notes, wiki pages, source cards, or prompts.
