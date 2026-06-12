---
name: markitdown-skill
description: Run Microsoft's MarkItDown as the local document extraction provider after source-extraction selects `markitdown`, or for non-wiki document-to-Markdown conversion when no intake lifecycle applies. For wiki source material, use source-extraction first so PROJECT.md provider policy, OCR/transcription approval, Source Review Gate, and the WIKI.md output contract remain in control.
---

# MarkItDown Skill

Documentation and utilities for converting documents to Markdown using Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

> **Note:** In this package, MarkItDown is installed through `pyproject.toml` and `uv sync`. Run it with `uv run markitdown ...` from the package root.

## When to Use

In wiki intake, start with `source-extraction`. Use this skill only after that workflow selects `markitdown` for a document source.

Use MarkItDown for local document conversion, including PDFs, Word files, PowerPoint files, Excel workbooks, and HTML files submitted as document files. OCR, image extraction, audio transcription, and video transcription remain controlled by `PROJECT.md` and require explicit approval before use.

## Quick Start

```bash
# Wiki intake output selected by source-extraction
uv run markitdown document.pdf -o intake/tmp/source-relative-parent/original-source-base-filename/source.md

# Non-wiki one-off conversion
uv run markitdown document.pdf -o output.md
```

## Supported Formats

| Format | Features |
|--------|----------|
| PDF | Text extraction, structure |
| Word (.docx) | Headings, lists, tables |
| PowerPoint | Slides, text |
| Excel | Tables, sheets |
| HTML | Structure preservation |

## Installation

The project dependency set includes Microsoft's `markitdown` CLI. Initialize or refresh the environment from the package root:

```bash
uv sync
```

Verify the CLI through the project environment:

```bash
uv run markitdown --help
```

## Common Patterns

### Convert PDF
```bash
uv run markitdown document.pdf -o document.md
```

### Batch Convert
```bash
# Using included script
uv run .agents/skills/markitdown-skill/scripts/batch_convert.py docs/*.pdf -o markdown/ -v

# Or shell loop
for file in docs/*.pdf; do
  uv run markitdown "$file" -o "${file%.pdf}.md"
done
```

## Python API

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

## Troubleshooting

### "markitdown not found"
```bash
uv sync
```

### OCR or Transcription Needed

Do not enable OCR or transcription from this skill alone. Follow `source-extraction` and `PROJECT.md`; if approval and setup are missing, stop before extraction and ask the user to configure the required provider.

## What This Skill Provides

| Component | Source |
|-----------|--------|
| `markitdown` CLI | Project dependency in `pyproject.toml` |
| `markitdown` Python API | Project dependency in `pyproject.toml` |
| `scripts/batch_convert.py` | This skill (utility) |
| Documentation | This skill |

## See Also

- [USAGE-GUIDE.md](USAGE-GUIDE.md) - Detailed examples
- [reference.md](reference.md) - Full API reference
- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) - Upstream library
