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

# Convert a URL
uv run markitdown https://example.com -o page.md
```

## 3. Package Usage Note

In this package, run MarkItDown with `uv run markitdown ...` from the package root. MarkItDown produces reviewable Markdown for the intake workflow; source-derived titles, paths, headings, and body text remain governed by the source-extraction provider contract.

## 4. Install Format-Specific Dependencies

Project dependencies are managed in `pyproject.toml`. After dependency changes, refresh the environment:

```bash
uv sync
```

## 5. System Dependencies (Optional)

### OCR (for images)
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

# URL conversion
uv run markitdown https://example.com -o page.md

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

**OCR not working**
```bash
sudo apt-get install tesseract-ocr
```
