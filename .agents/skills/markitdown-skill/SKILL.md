---
name: markitdown-skill
description: Run Microsoft's MarkItDown as the local document extraction provider after source-extraction selects `markitdown`, or for non-wiki document-to-Markdown conversion when no intake lifecycle applies. For wiki source material, use source-extraction first so PROJECT.md provider policy, transcription approval, Source Review Gate, and the WIKI.md output contract remain in control.
---

# MarkItDown

Use Microsoft MarkItDown for local document-to-Markdown conversion. The package installs the verified MarkItDown dependency through `pyproject.toml` and `uv.lock`.

For wiki intake, start with `source-extraction`. This skill runs the selected provider; it does not decide Source Review Gate outcomes or write directly to `wiki/`.

## Local Conversion

Run from the package root:

```bash
uv run markitdown <input-file> -o <output.md>
```

MarkItDown handles text-bearing PDF, DOCX, PPTX, XLS/XLSX, HTML, Outlook, and related document formats through the installed extras. Audio and YouTube transcription remain approval-controlled source kinds. Azure Document Intelligence is an optional service-backed mode and must follow the provider setup document.

MarkItDown is not the package's general OCR provider. If important source content requires OCR or visual interpretation, return to `source-extraction` and use an explicitly approved provider.

## Verified CLI Options

Use `--use-plugins` to enable installed third-party plugins and `--list-plugins` to inspect them. Use `--keep-data-uris` only when complete embedded data URIs are required for source review; the default CLI truncates them.

```bash
uv run markitdown --list-plugins
uv run markitdown --use-plugins <input-file> -o <output.md>
uv run markitdown --keep-data-uris <input-file> -o <output.md>
```

## Batch Conversion

The bundled helper performs verified local conversion and optional plugin loading:

```bash
uv run .agents/skills/markitdown-skill/scripts/batch_convert.py <files...> -o <output-directory>
```

## Python API

```python
from markitdown import MarkItDown

result = MarkItDown().convert("document.pdf")
print(result.text_content)
```

For wiki output paths, provider metadata, side-output handling, credentials, and review rules, follow `.agents/skills/source-extraction/references/providers/markitdown/`.
