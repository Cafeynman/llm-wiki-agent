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

## Policy Values

- `markitdown`, `mineru`, `defuddle`: Use the named provider for the source kind.
- `ask-before-ocr`: Ask the user before enabling OCR or image text extraction.
- `ask-before-transcription`: Ask the user before enabling audio transcription.
- `ask-before-transcription-or-frame-ocr`: Ask before extracting either audio transcript or video frame text.
- `unsupported`: Do not extract this kind for the current project; follow WIKI handling for unsupported material.
