# markitdown-skill

📄 OpenClaw agent skill for converting documents to Markdown.

**Documentation and utilities** for Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

**Author:** Karman Verma

## What This Skill Is

This skill provides:
- ✅ Documentation for using MarkItDown
- ✅ A batch conversion script (`scripts/batch_convert.py`)
- ✅ Usage examples and API reference

In this package, the actual document conversion is done by Microsoft's `markitdown` CLI through the project `uv` environment.

## Install

From the package root:

```bash
uv sync
uv run markitdown --help
```

## Quick Start

```bash
# Convert PDF
uv run markitdown document.pdf -o output.md

# Fetch web docs
uv run markitdown https://example.com/docs -o docs.md

# Batch convert
uv run .agents/skills/markitdown-skill/scripts/batch_convert.py docs/*.pdf -o markdown/
```

## Supported Formats

| Format | Features |
|--------|----------|
| PDF | Text extraction |
| Word (.docx) | Headings, lists, tables |
| PowerPoint | Slides, text |
| Excel | Tables, sheets |
| Images | OCR + metadata |
| Audio | Speech transcription |
| HTML | Structure preservation |
| YouTube | Video transcription |

## Documentation

- [SKILL.md](SKILL.md) - Main documentation
- [USAGE-GUIDE.md](USAGE-GUIDE.md) - Detailed examples
- [reference.md](reference.md) - Full API reference
- [POST_INSTALL.md](POST_INSTALL.md) - Setup guide

## Credits

- **Upstream library:** [Microsoft MarkItDown](https://github.com/microsoft/markitdown) by AutoGen Team
- **This skill:** Karman Verma

## License

MIT
