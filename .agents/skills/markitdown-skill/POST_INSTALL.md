# Post-Install Setup

MarkItDown skill installed! Here's how to get started.

## 1. Verify Installation

```bash
uv run markitdown --version
```

If not found, refresh the project environment from the package root:
```bash
uv sync
```

## 2. Test It

```bash
# Convert a PDF
uv run markitdown document.pdf -o output.md
```

## 3. Package Usage Note

In this package, run MarkItDown with `uv run markitdown ...` from the package root. For wiki intake, start with `source-extraction`; it selects MarkItDown when appropriate, writes `intake/tmp/.../source.md`, and leaves acceptance to Source Review Gate. OCR, image descriptions, audio transcription, video handling, and service-backed providers require `PROJECT.md` policy plus explicit user approval.

## 4. Install Format-Specific Dependencies

Project dependencies are managed in `pyproject.toml`. After dependency changes, refresh the environment:

```bash
uv sync
```

## 5. System Dependencies (Optional)

### OCR (for images)

Install this only when an approved OCR path needs it.

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

## Quick Reference

```bash
# File conversion
uv run markitdown file.pdf -o output.md

# Batch conversion
uv run .agents/skills/markitdown-skill/scripts/batch_convert.py docs/*.pdf -o markdown/ -v
```

## Troubleshooting

**"markitdown not found"**
```bash
uv sync
```

**"No module named 'xxx'"**
```bash
uv sync
```

**OCR not working on an approved OCR path**
```bash
sudo apt-get install tesseract-ocr
```
