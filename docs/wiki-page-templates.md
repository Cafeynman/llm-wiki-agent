# Wiki Page Templates

Use these templates when creating wiki pages that follow the operating contract in `WIKI.md`.

## Source Card

Create one source card under `wiki/sources/<source-relative-parent>/original-source-base-filename.md` for every `digested` source.

```markdown
---
title: "Source Title"
type: source
status: draft
confidence: medium
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - "[[raw/digested/source-relative-parent/original-filename.ext]]"
  - "[[intake/processed/source-relative-parent/original-source-base-filename/source.md]]"
  - "[[reviews/source-review/YYYY-MM-DD.md]]"
tags:
  - "llm-wiki"
---

# Source Title

## Summary

Explain what the source is about and why it matters to the wiki.

## Key Points

- Point grounded in the source.
- Point grounded in the source.

## Supported Claims

- Claim or claim page this source can support.

## Scope

State the time period, geography, domain, method, dataset, or context covered by the source.

## Limitations

State missing context, weak extraction, image-only material, uncertain claims, age, bias, or other constraints.

## Traceability

- Original file: [[raw/digested/source-relative-parent/original-filename.ext]]
- Processed Markdown: [[intake/processed/source-relative-parent/original-source-base-filename/source]]
- Source review: [[reviews/source-review/YYYY-MM-DD]]
- Manifest: [[intake/processed/source-relative-parent/original-source-base-filename/manifest]]
```
