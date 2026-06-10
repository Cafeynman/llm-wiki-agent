# MarkItDown Usage

Use MarkItDown as the default local document provider unless `PROJECT.md` selects another provider.

## Supported Source Kinds

- `document`
- HTML files submitted as document files

## Command Pattern

Run from the project root:

```bash
uv run markitdown <input-file> -o <intake-tmp-dir>/source.md
```

When OCR has been explicitly approved and configured:

```bash
uv run --env-file .env markitdown <input-file> --use-plugins --llm-client openai --llm-model <MARKITDOWN_OCR_MODEL> -o <intake-tmp-dir>/source.md
```

For the documented OpenAI-compatible OCR command, `OPENAI_API_KEY` and `MARKITDOWN_OCR_MODEL` are required. If `.env` or either variable is missing, stop before extraction and ask the user to configure it. Do not paste API keys into command examples, prompts, manifests, logs, review notes, wiki pages, or source cards.

## Output Handling

- Preserve provider output that comes from the source body, including inline media references. Do not silently delete `data:image/...;base64,...` links from `source.md`; record them as unprocessed embedded media instead.
- Record missing figures, scans, screenshots, embedded media, or audio in review notes or manifest metadata.
- If important non-text content was not processed, route the source to `needs-review` through the normal WIKI process.

## Do Not

- Do not enable OCR automatically.
- Do not transcribe audio automatically.
- Do not copy attachments into wiki pages by default.
- Do not treat a successful MarkItDown exit as Source Review Gate acceptance.
