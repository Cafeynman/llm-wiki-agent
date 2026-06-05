---
name: markitdown-skill
description: OpenClaw agent skill for converting documents to Markdown. Documentation and utilities for Microsoft's MarkItDown library. Supports PDF, Word, PowerPoint, Excel, images (OCR), audio (transcription), HTML, YouTube.
metadata:
  openclaw:
    emoji: "📄"
    homepage: https://github.com/karmanverma/markitdown-skill
    requires:
      bins: ["uv"]
---

# MarkItDown Skill

Documentation and utilities for converting documents to Markdown using Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

> **Note:** In this package, MarkItDown is installed through `pyproject.toml` and `uv sync`. Run it with `uv run markitdown ...` from the package root.

## When to Use

**Use markitdown for:**
- 📄 Fetching documentation (README, API docs)
- 🌐 Converting web pages to markdown
- 📝 Document analysis (PDFs, Word, PowerPoint)
- 🎬 YouTube transcripts
- 🖼️ Image text extraction (OCR)
- 🎤 Audio transcription

## Quick Start

```bash
# Convert file to markdown
uv run markitdown document.pdf -o output.md

# Convert URL
uv run markitdown https://example.com/docs -o docs.md
```

## Supported Formats

| Format | Features |
|--------|----------|
| PDF | Text extraction, structure |
| Word (.docx) | Headings, lists, tables |
| PowerPoint | Slides, text |
| Excel | Tables, sheets |
| Images | OCR + EXIF metadata |
| Audio | Speech transcription |
| HTML | Structure preservation |
| YouTube | Video transcription |

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

### Fetch Documentation
```bash
uv run markitdown https://github.com/user/repo/blob/main/README.md -o readme.md
```

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

### OCR Not Working
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

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
