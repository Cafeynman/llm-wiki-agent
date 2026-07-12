# MarkItDown Usage

Use MarkItDown as the default local document provider unless `PROJECT.md` selects another provider.

## Supported Source Kinds

- `document`
- HTML files submitted as document files
- approval-controlled audio or YouTube transcription when explicitly configured

## Command Pattern

Run from the project root:

```bash
uv run markitdown <input-file> -o <intake-tmp-dir>/source.md
```

Use `--use-plugins` only for installed, selected plugins. Use `--keep-data-uris` only when source review requires complete embedded data URIs; MarkItDown truncates them by default.

## Output Handling

- Keep provider-returned side outputs under the same intake folder as `source.md`.
- Promote accepted side outputs with that intake folder or delete them with the temporary folder for non-accepted outcomes.
- Record preserved side outputs in `manifest.md` for accepted sources or in review/log records before temporary cleanup for other outcomes.
- Record missing figures, scans, screenshots, embedded media, or audio when they affect reviewability.
- If important non-text content was not processed, route the source to `needs-review` through the normal WIKI process.

## Limits

- MarkItDown is not the package's general local OCR provider.
- Do not enable transcription without the configured policy and user approval.
- Do not treat a successful MarkItDown exit as Source Review Gate acceptance.
