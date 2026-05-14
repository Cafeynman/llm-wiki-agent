# Provider Registry

This registry lists the initial supported extraction providers.

| Provider | Supported source kinds | Recommended use | Setup required |
| --- | --- | --- | --- |
| `markitdown` | `document` | Default document provider for local text-first extraction. | Installed through project dependencies. Optional OCR setup only when OCR is explicitly approved. |
| `mineru` | `document`, selected `image`/scan-heavy inputs when approved | High-structure parsing for complex PDFs, tables, formulas, scans, and multimodal document layouts. | Local or hosted/API setup. Some API modes require token or network access. |
| `defuddle` | `webpage` | Default webpage provider for extracting clean Markdown from web pages. | Defuddle CLI must be installed. |

## Recommended Defaults

- `document`: `markitdown`
- `webpage`: `defuddle`
- `image`: `ask-before-ocr`
- `audio`: `ask-before-transcription`
- `video`: `ask-before-transcription-or-frame-ocr`

If a project does not need a source kind, set that kind to `unsupported` in `PROJECT.md`.
