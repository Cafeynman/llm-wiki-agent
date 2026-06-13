# Source Kinds

Classify source material before selecting a provider. Source kinds describe the material, not the tool.

| Source kind | Description | Default policy meaning |
| --- | --- | --- |
| `document` | PDF, Word, PowerPoint, Excel, HTML files, and similar files submitted as documents. | Use the configured document provider. |
| `webpage` | A live URL or saved web page intended to be extracted as readable page content. | Use the configured webpage provider. |
| `image` | Standalone image files or sources whose useful content is locked in images. | Ask before OCR or mark unsupported, depending on `PROJECT.md`. |
| `audio` | Audio files or source material whose content requires transcription. | Ask before transcription or mark unsupported, depending on `PROJECT.md`. |
| `video` | Video files or sources whose content requires audio transcription or frame analysis. | Ask before transcription/frame OCR or mark unsupported, depending on `PROJECT.md`. |
| `archive` | ZIP or other archive containing mixed members. | List members first, then classify each useful member separately. |

## Temporary Extraction Handling

Use this table after classifying the source kind and checking `PROJECT.md` provider policy.

| File type | Temporary extraction handling |
| --- | --- |
| Markdown | Stage or copy to `intake/tmp/source-relative-parent/original-source-base-filename/source.md` without changing source text before review. |
| PDF | Convert readable content to Markdown; scanned or image-heavy PDFs become `needs-review` when important content is not processed. |
| Word | Convert text, headings, tables, captions, and any supported document content; unprocessed important embedded material becomes `needs-review`. |
| PowerPoint | Convert to Markdown and preserve slide structure. |
| Excel | Convert tables to Markdown and summarize table meaning when needed. |
| HTML | Extract readable Markdown while preserving extracted title, headings, and body text. |
| CSV / JSON / XML | Convert to Markdown table, structured summary, or both. |
| Image | Do not treat as first-class intake content by default; move to `raw/needs-review/` and record the missing text extraction or image review step when the image carries source information. |
| Audio | Transcribe only when `PROJECT.md` allows `ask-before-transcription` and the user approves; otherwise move to `raw/needs-review/` or `raw/unsupported/` according to the configured policy. |
| Video | Extract audio transcript or frame text only when `PROJECT.md` allows it and the user approves; otherwise move to `raw/needs-review/` or `raw/unsupported/` according to the configured policy. |
| ZIP or other archive | List members first, record member paths and file types, then selectively convert useful files. |
| Unsupported or damaged file | Move to `raw/unsupported/` and record the reason. |

## Policy Values

- `markitdown`, `mineru`, `defuddle`: Use the named provider for the source kind.
- `ask-before-ocr`: Ask the user before enabling OCR or image text extraction.
- `ask-before-transcription`: Ask the user before enabling audio transcription.
- `ask-before-transcription-or-frame-ocr`: Ask before extracting either audio transcript or video frame text.
- `unsupported`: Do not extract this kind for the current project; follow WIKI handling for unsupported material.
