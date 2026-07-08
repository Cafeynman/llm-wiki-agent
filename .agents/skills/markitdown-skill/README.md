# markitdown-skill

📄 Agent skill for converting documents to Markdown.

**Documentation and utilities** for Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

**Author:** Karman Verma

## What This Skill Is

This skill provides:
- ✅ Documentation for using MarkItDown
- ✅ A batch conversion script (`scripts/batch_convert.py`)
- ✅ Usage examples and API reference

In this package, the actual document conversion is done by Microsoft's `markitdown` CLI through the project `uv` environment.

For wiki intake, start with `source-extraction`; it selects MarkItDown according to `PROJECT.md`, writes reviewable Markdown to `intake/tmp/.../source.md`, and leaves acceptance to Source Review Gate. Use the direct examples below only for non-wiki conversion or after `source-extraction` has selected MarkItDown.

## Install

From the package root:

```bash
uv sync
uv run markitdown --help
```

## Quick Start

```bash
# Convert a local document outside wiki intake
uv run markitdown document.pdf -o output.md

# Batch convert outside wiki intake
uv run .agents/skills/markitdown-skill/scripts/batch_convert.py docs/*.pdf -o markdown/
```

## Supported Formats

| Format | Features |
|--------|----------|
| PDF | Text extraction |
| Word (.docx) | Headings, lists, tables |
| PowerPoint | Slides, text |
| Excel | Tables, sheets |
| Images | OCR only after `PROJECT.md` policy and user approval |
| Audio | Not a default wiki path; transcription only after approval |
| HTML | Structure preservation |
| YouTube | Not a default wiki path; handle through source-extraction policy |

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
