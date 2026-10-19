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

The sentences inside this template are scaffolding, not acceptable source-card content. Before a card can represent a `digested` source, replace every exact instructional placeholder with source-specific text and real traceability links. The standard lint rejects the known placeholder sentences above; it does not use fuzzy token matching, require a fixed number of points, or pretend to judge semantic quality. If the accepted source does not support a substantive summary or claim, keep the card `draft` and route the gap to a question instead of filling it with generic prose.

For a Defuddle live-URL capture, keep the raw capture wikilink as the first source and also add the exact submitted URL as a quoted plain string under `sources:`. Add `Submitted URL: <url>` under Traceability. Do not replace the raw capture link with the external URL.

## Citation Placement

Use concise, accurate display aliases for long internal paths in body prose. Keep full targets and heading locators; short clear titles need no alias. Escape the alias separator inside Markdown tables. Frontmatter sources retain quoted full wikilinks.

Use a direct wikilink when it keeps the supporting source clear, for example `This claim follows [[wiki/sources/Source A#Relevant section|Source A]]`.

When multiple passages rely on the same evidence scope, they may reuse one footnote label:

```markdown
Source A supports the first claim[^source-a-evidence].
A later passage relying on the same evidence may reuse that label[^source-a-evidence].

[^source-a-evidence]: [[wiki/sources/Source A#Relevant section|Source A]], relevant section.
```

When one source supports different claims with different evidence scopes, use separate labels:

```markdown
Source A supports one claim[^source-a-first] and a separate claim[^source-a-second].

[^source-a-first]: [[wiki/sources/Source A#First relevant section|Source A]], first relevant section.
[^source-a-second]: [[wiki/sources/Source A#Second relevant section|Source A]], second relevant section.
```
