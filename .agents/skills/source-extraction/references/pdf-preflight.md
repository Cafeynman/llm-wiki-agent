# PDF Preflight

Use this lightweight check before choosing a provider for a PDF document.

The preflight is only for provider selection and limit detection. It must not become a full extraction pass, OCR run, rendered-page review, or secondary conversion path.

## Allowed Checks

- Read basic metadata: file size, page count, encryption status, and page dimensions when available.
- Sample the text layer from a small set of pages: first page, middle page, last page, and at most two additional pages when the document looks mixed.
- Inspect lightweight structural clues when the local tool exposes them cheaply, such as whether sampled pages contain extractable text, many embedded images, or unusually sparse text.

Stop after the sampled inspection. Do not render all pages, OCR pages, export images, or process the full document during preflight.

## Provider Selection Signals

Prefer the configured simple document provider, normally `markitdown`, when sampled pages have a usable text layer and the document has ordinary single-column or lightly structured content.

Prefer `mineru` when it is available and allowed by `PROJECT.md` for scanned or image-heavy PDFs, sparse or absent text layers, dense tables, formulas, multi-column academic layouts, complex figure captions, or repeated MarkItDown quality failures observed from the original source.

If `PROJECT.md` says `Prefer MinerU when available: yes`, choose MinerU for supported document inputs whenever the required MinerU mode is available. If that preference is `no` or still `unconfirmed`, keep MarkItDown as the ordinary document default and use MinerU only for complex documents or explicit user choice.

## Large PDFs

Do not split a PDF automatically during preflight. If a selected provider mode cannot accept the whole file, report the limit and ask the user to approve a page-range or section split strategy.

When the user approves splitting, split from the original PDF only. Each part may produce an intermediate Markdown file, but the final intake output for the original source must still be one merged `<intake-tmp-dir>/source.md`.

Merge the part Markdown files in original page order. Preserve page-range boundaries with concise headings or comments when they are needed for traceability, and record each part path, page range, provider mode, and merge decision in the intake manifest or review notes. The merged `source.md` remains the reviewable text for the original PDF; part Markdown files are side outputs, not separate sources.

Never feed one provider's Markdown output into another provider.

## Inconclusive Checks

If local tools cannot cheaply inspect the PDF, mark preflight as inconclusive and choose according to `PROJECT.md`. Do not invent complexity signals from the filename alone.
