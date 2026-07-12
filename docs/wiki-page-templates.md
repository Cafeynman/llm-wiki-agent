# Wiki Page Templates

Use these templates when creating wiki pages that follow the operating contract in `WIKI.md`.

## Source Card

Create one source card under `wiki/sources/<source-relative-parent>/original-source-base-filename.md` for every `digested` source.

`Source Title` means the source's original-language title unless the source, user, or `PROJECT.md` confirms another naming scheme. Do not translate, romanize, convert to pinyin, slugify, force lowercase, case-normalize, or simplify it just because this template is written in English.

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

For a Defuddle live-URL capture, keep the raw capture wikilink as the first source and also add the exact submitted URL as a quoted plain string under `sources:`. Add `Submitted URL: <url>` under Traceability. Do not replace the raw capture link with the external URL.
