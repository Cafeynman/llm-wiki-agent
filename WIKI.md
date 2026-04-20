# LLM Wiki Operating Guide

This file defines the common operating rules for an agent-maintained Obsidian LLM Wiki.

## Core Goal

Maintain a persistent knowledge base that compounds over time. Do not treat sources as one-off retrieval material. Preserve source traceability, extract durable knowledge, connect related pages, mark uncertainty, and record meaningful changes.

The human curates priorities and reviews important judgments. The agent handles source review, intake, conversion, ingestion, synthesis, artifact creation, and routine wiki maintenance.

## Directory Contract

Use this structure unless the user explicitly asks for a different one:

```text
.
├── inbox/             Entry point for all user-submitted original files.
├── raw/
│   ├── digested/       Original files accepted, digested, and linked to wiki updates.
│   ├── needs-review/   Original files that need user judgment before final handling.
│   ├── ignored/        Original files judged not worth organizing into the wiki.
│   └── unsupported/    Original files that cannot currently be processed.
├── intake/
│   ├── tmp/            Temporary Markdown converted from raw files before review.
│   ├── processed/      Agent-generated Markdown outputs accepted for ingest.
│   └── logs/           Daily intake logs.
├── reviews/
│   ├── source-review/  Source review reports.
│   └── reflection/     Confirmed discussion-derived source records.
├── logs/
│   └── wiki.md         Append-only high-level operation history.
├── questions/          Open questions and investigation trails.
├── artifacts/          User-facing deliverables created from wiki knowledge.
└── wiki/
    ├── home.md         Human-facing main page: purpose, topics, artifacts, open questions.
    ├── index.md        Catalog of wiki pages and short summaries.
    ├── overview.md     Living synthesis of the whole wiki.
    ├── sources/        One content-rich source card per digested source.
    ├── entities/       People, organizations, projects, tools, files, datasets.
    ├── concepts/       Ideas, methods, frameworks, terms, patterns.
    ├── claims/         Important claims that need evidence and counterevidence.
    └── syntheses/      Durable answers, comparisons, timelines, briefs.
```

Create only the directories required for the current task. Do not add exports, dashboards, databases, watchers, static sites, or graph files unless the user asks.

For each digested raw source, write intake outputs under:

```text
intake/processed/YYYY-MM-DD/source-slug/
├── source.md
├── summary.md
├── manifest.md
├── digest.md        Optional short digest used to support review.
└── chunks/
    ├── index.md
    └── 01.md
```

Use `digest.md` only when it helps review. Use `chunks/` only when the source is too large or structurally complex to handle as one file.

## Source and Traceability Rules

1. Treat user-submitted files in `inbox/` and original files under `raw/` as source truth.
2. Do not rewrite, normalize, rename, or edit original file contents unless the user explicitly asks.
3. All user-submitted original files must enter through `inbox/` before conversion, review, or classification. Once a file is handled by intake, move it out of `inbox/` in the same pass, regardless of outcome.
4. Agent-generated Markdown never goes back into `raw/`; write temporary conversion output under `intake/tmp/` and accepted outputs under `intake/processed/`.
5. `intake/tmp/` is not a holding area. Every temporary conversion must end by promoting accepted Markdown to `intake/processed/` or by deleting the temporary folder after the original moves to `raw/needs-review/`, `raw/ignored/`, or `raw/unsupported/`.
6. Every factual wiki claim must be grounded in an original source, an intake Markdown output, a cited wiki page, or a confirmed discussion-derived source record under `reviews/reflection/`.
7. If a claim is useful but unsupported, put it in `questions/`, a needs-verification note on the relevant page, or a low-confidence page under `wiki/claims/`.
8. Do not copy API keys, tokens, passwords, private keys, session cookies, or sensitive personal information into generated notes. Redact and cite the source path instead.
9. Intake logs and review reports must record the complete original filename, file type, source path, final raw destination, and any generated Markdown path. Do not use ellipses or shortened paths for source traceability.
10. Intake must preserve meaningful text and identify important non-text material. If useful content appears to depend on figures, screenshots, scans, audio, or other non-text material that was not processed, move the original to `raw/needs-review/` and record the missing processing step.
11. This is a text-first workflow. Attachments, images, scans, screenshots, and audio may remain part of the preserved original source, but they are not first-class wiki content by default. Do not create attachment asset directories, copy images into wiki pages, or add image-reference schemes unless the user explicitly asks for image handling.

## Page Conventions

Use Obsidian-compatible Markdown. Prefer `[[wikilinks]]` for internal wiki pages and normal Markdown links for external URLs. Keep filenames human-readable and stable.

Recommended wiki frontmatter:

```yaml
---
title: Page Title
type: source | entity | concept | claim | synthesis
status: draft | reviewed | verified | stale | archived
confidence: low | medium | high
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - raw/digested/example.pdf
  - intake/processed/YYYY-MM-DD/example/source.md
tags:
  - llm-wiki
---
```

Keep pages focused. A page should have one clear purpose. If a page starts covering multiple topics, split it and link the new pages.

Use `wiki/home.md` as the human-facing main page. It should explain what the wiki is for, main topic areas, important entry points, current artifacts, and major open questions. Do not use it as a changelog.

Use `wiki/index.md` as the structured catalog and `logs/wiki.md` as the operation history. Do not let either file replace `wiki/home.md`.

Write deliverables to `artifacts/` when the user asks for a report, brief, outline, draft, comparison table, template, or other reusable output made from wiki knowledge. Track open questions and investigation trails under `questions/`. These files may use frontmatter with `type: artifact` or `type: question`, but they are work products next to the wiki, not canonical wiki knowledge pages.

Create one `wiki/sources/` source card for every `digested` source. Do not create source cards for `ignored`, `unsupported`, or unresolved `needs-review` files.

A source card is the wiki-facing summary of a source, not an intake receipt. It must contain substantive content: source summary, key points, supported claims, scope, limitations, and links to the raw file, processed Markdown, source review, and manifest. A page with only frontmatter, file size, line count, processing date, or paths is invalid.

Other wiki pages should normally cite the source card instead of citing raw files directly. The source card carries the full traceability chain back to `raw/digested/`, `intake/processed/`, and `reviews/source-review/`.

Source card template:

```markdown
---
title: Source Title
type: source
status: draft
confidence: medium
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - raw/digested/original-filename.ext
  - intake/processed/YYYY-MM-DD/source-slug/source.md
  - reviews/source-review/YYYY-MM-DD.md
tags:
  - llm-wiki
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

- Original file: `raw/digested/original-filename.ext`
- Processed Markdown: `intake/processed/YYYY-MM-DD/source-slug/source.md`
- Source review: `reviews/source-review/YYYY-MM-DD.md`
- Manifest: `intake/processed/YYYY-MM-DD/source-slug/manifest.md`
```

## Core Workflows

There are only three workflow modes:

```text
Add Knowledge
Use Knowledge
Maintain Wiki
```

Do not run every subroutine in sequence. Choose the shortest path that fully satisfies the user's request.

## Workflow: Add Knowledge

Use this mode when the user adds files, asks to process sources, asks to save discussion insights, or asks to update the wiki with new knowledge.

### 1. Route the Input

Classify the input before acting, then enter the matching path below. The "Start with" column maps directly to the later subsections in this workflow.

| Input type                                                                                               | Start with                           | Continue to                                                                                    |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| A batch of candidate raw files, `inbox/`, or a triage request                                            | Intake                               | Convert each file to `intake/tmp/`, optionally write a digest, then run Source Review Gate     |
| One specific raw file in `inbox/`                                                                        | Intake                               | Convert or normalize to `intake/tmp/`, optionally write a digest, then run Source Review Gate  |
| A non-Markdown source that needs conversion                                                              | Intake                               | Ensure the original is in `inbox/`, convert to `intake/tmp/`, then run Source Review Gate  |
| Large, archived, table-heavy, slide, scanned, multimodal, or noisy source                                | Large File and Context Budget Policy | Inspect metadata first; if it cannot be completed in the same pass, move the original to `raw/needs-review/` and record the next review question |
| An existing intake output under `intake/processed/`                                                      | Ingest                               | Update manifest, `wiki/index.md`, `wiki/home.md`, and `logs/wiki.md` as needed                 |
| An existing wiki page that needs new knowledge merged in                                                 | Ingest                               | Update related wiki pages; track unresolved threads in `questions/`                            |
| A discussion-derived insight from the current conversation                                               | Reflect                              | Update relevant wiki pages only after confirmation unless the user explicitly asked to reflect |
| A user question or deliverable request rather than new source material                                   | Use Knowledge                        | Save synthesis or artifact only when requested or confirmed                                    |

Use research-style writing inside any path whenever the material contains claims, evidence, counterevidence, uncertainty, methods, limitations, or open questions.

### 2. Follow the Selected Path

The following subsections define the path bodies referenced by the routing table. Run only the selected path and any continuation it explicitly requires.

### 3. Intake

Intake is the entry path for raw files. Its job is to produce reviewable Markdown first, then decide whether the material deserves permanent intake output and wiki ingestion.

For raw files, use the most reliable Markdown conversion path available in the environment. The converter must produce reviewable Markdown and identify important content it could not process.

Use the shortest reliable conversion path available in the environment.

| File type                   | Temporary conversion handling                                      |
| --------------------------- | ------------------------------------------------------------------ |
| Markdown                    | Normalize into `intake/tmp/YYYY-MM-DD/source-slug/source.md` before review |
| PDF                         | Convert readable content to Markdown; scanned or image-heavy PDFs become `needs-review` when important content is not processed |
| Word                        | Convert text, headings, tables, captions, and any supported document content; unprocessed important embedded material becomes `needs-review` |
| PowerPoint                  | Convert to Markdown and preserve slide structure                   |
| Excel                       | Convert tables to Markdown and summarize table meaning when needed |
| HTML                        | Convert to clean Markdown                                          |
| CSV / JSON / XML            | Convert to Markdown table, structured summary, or both             |
| Image                       | Do not treat as first-class intake content by default; move to `raw/needs-review/` and record the missing text extraction or image review step when the image carries source information |
| Audio                       | Transcribe with available approved tooling; otherwise move to `raw/needs-review/` with the missing processing step |
| ZIP or other archive        | List members first, record member paths and file types, then selectively convert useful files |
| Unsupported or damaged file | Move to `raw/unsupported/` and record the reason                   |

The intake order is:

1. Take original files from `inbox/`.
2. Inspect and record the complete raw file path, exact filename, file type, size, and basic readability.
3. Convert or normalize the file to temporary Markdown under `intake/tmp/YYYY-MM-DD/source-slug/`.
4. For archives, create a member listing first. Record each useful member's archive path, filename, detected type, and conversion result. Convert only members that are useful for review.
5. If conversion fails, move the original file to `raw/unsupported/`, record the blocker in `intake/logs/YYYY-MM-DD.md`, delete the temporary folder, and stop.
6. If conversion technically succeeds but the Markdown is garbled, empty, too thin to judge, obviously truncated, structurally broken, or missing important text, move the original to `raw/needs-review/`, record the conversion-quality question, move any useful review notes to `reviews/source-review/`, delete the temporary folder, and stop.
7. If the source is too large, ambiguous, encrypted, noisy, multimodal, or requires user selection before a final decision, move the original to `raw/needs-review/`, record the question, move any useful review notes to `reviews/source-review/`, delete the temporary folder, and stop.
8. Optionally write `digest.md` in the temporary intake folder when a short digest would make review easier; do not make digest mandatory.
9. Run Source Review Gate on the temporary Markdown and optional digest, not on the raw filename alone.
10. If the outcome is `digested`, promote the temporary Markdown to `intake/processed/YYYY-MM-DD/source-slug/`, write `source.md`, `summary.md`, `manifest.md`, include `digest.md` only if it was useful, move the original to `raw/digested/`, delete the temporary folder, then ingest.
11. If the outcome is `ignored`, move the original to `raw/ignored/`, log the reason, delete the temporary folder, and stop.
12. If the outcome is `unsupported`, move the original to `raw/unsupported/`, log the blocker, delete the temporary folder, and stop.
13. If the outcome is `needs-review`, move the original to `raw/needs-review/`, move any useful review notes to `reviews/source-review/`, delete the temporary folder, and record the question.

### 4. Source Review Gate

Source Review Gate is an intake step. It runs after conversion or normalization has produced readable temporary Markdown. Its goal is to decide what deserves permanent intake output and wiki ingestion, not to update wiki knowledge pages.

Each reviewed item receives one outcome that maps to a raw file location:

| Outcome | Raw destination | Intake effect | Meaning |
| --- | --- | --- | --- |
| `digested` | `raw/digested/` | Promote temporary Markdown to `intake/processed/`, then ingest | Useful, relevant, readable, and likely to improve the wiki |
| `needs-review` | `raw/needs-review/` | Move useful review notes to `reviews/source-review/` and clean `intake/tmp/` | Potentially useful but requires user judgment before final handling |
| `ignored` | `raw/ignored/` | Do not promote to `intake/processed/` and do not ingest | Duplicate, irrelevant, too shallow, or not worth preserving |
| `unsupported` | `raw/unsupported/` | Do not promote to `intake/processed/` and do not ingest | Cannot currently be converted, read, or trusted enough to review |

Use `digested` when a source adds new evidence, a useful framework, a meaningful contradiction, a reusable definition, a decision, a timeline, a comparison, a concrete example, or a strong source for a weak claim.

Do not use `ignored` for a source that might contain important information but was not readable enough to judge. Use `unsupported` or `needs-review`.

Do not treat a successful converter exit as acceptance. If the converted Markdown is garbled, empty, too thin, truncated, structurally broken, or missing expected content, classify it as `needs-review` unless the file is clearly damaged or unsupported.

Write review reports to:

```text
reviews/source-review/YYYY-MM-DD.md
```

Do not update wiki knowledge pages during source review.

Each accepted intake folder under `intake/processed/` must include:

```text
source.md      Clean Markdown converted or normalized from the original file.
summary.md     Short processing summary and value judgment.
manifest.md    Traceability record from original file to wiki updates.
```

It may also include `digest.md` when a short digest was useful for review, and `chunks/` when the source required chunking.

After intake, move each original file from `inbox/` into exactly one state directory: `raw/digested/`, `raw/needs-review/`, `raw/ignored/`, or `raw/unsupported/`. `inbox/` must not retain files that were already handled once. Record every move in `intake/logs/YYYY-MM-DD.md` with complete filenames, file types, source paths, and final destinations.

Treat `raw/needs-review/` as a queue, not a final archive. Each file moved there must have a recorded review question in `reviews/source-review/YYYY-MM-DD.md` or `intake/logs/YYYY-MM-DD.md`. When the user or a later agent resolves the question, restart intake from that original file, convert again to `intake/tmp/` if needed, then finish with `digested`, `ignored`, or `unsupported`. Do not leave a file in `raw/needs-review/` after a final decision exists.

### 5. Large File and Context Budget Policy

Use this policy whenever a raw file, converted `source.md`, or generated chunk is too large to read comfortably in the current context.

1. Inspect metadata before reading full content: exact filename, file type, file size, line count, page or slide count, table dimensions, archive listing, headings, and conversion warnings when available.
2. Do not load a very large original file or `source.md` into context in one pass. Work from `summary.md`, `manifest.md`, and `chunks/index.md` first.
3. For large sources, create `chunks/` before ingest. Each chunk must be a coherent unit small enough to read and summarize independently. Prefer semantic boundaries such as headings, chapters, slides, page ranges, sections, tables, or archive members.
4. Write or update `summary.md` progressively from chunk summaries. The summary should capture the source topic, useful claims, low-value regions, noisy regions, and recommended ingest scope.
5. During ingest, read only the chunks needed for the current wiki update. Do not read all chunks unless the user explicitly asks for a full-source pass and the available context can support it.
6. If a large source cannot be fully reviewed in the current pass, move the original out of `inbox/` to `raw/needs-review/`, record the review question, and clean `intake/tmp/`.
7. If the source is mostly boilerplate, duplicate text, extraction errors, generated logs, raw data dumps, or other noise, do not expand it into the wiki. Record the issue in the review report and move the original to `raw/ignored/`, `raw/needs-review/`, or `raw/unsupported/` according to the blocker.

### 6. Ingest

When a source is ready to become wiki knowledge:

1. Confirm the source path exists.
2. Read `summary.md`, `manifest.md`, and `chunks/index.md` first when available.
3. Read the original source only when accuracy or conversion quality needs verification.
4. Extract durable knowledge: main thesis, key claims, evidence, counterevidence, named entities, important concepts, decisions, recommendations, contradictions, and open questions.
5. Create or update exactly one content-rich source card under `wiki/sources/`.
6. Create or update relevant pages in `wiki/entities/`, `wiki/concepts/`, `wiki/claims/`, or `wiki/syntheses/` only when useful.
7. Create or update `questions/` only when an unresolved investigation thread is worth tracking separately.
8. Update `wiki/overview.md` only when the source changes the overall synthesis.
9. Update `wiki/index.md`, `wiki/home.md` when needed, and `logs/wiki.md`.
10. Update the intake `manifest.md` when intake outputs led to wiki, question, or artifact changes.

Do not flatten disagreement into false consensus. If sources conflict, preserve the disagreement and cite both sides.

### 7. Batch File Lifecycle Example

This example shows the intended lifecycle for a pile of files in `inbox/`.

Initial state:

```text
.
└── inbox/
    ├── paper.pdf
    ├── notes.md
    ├── slides.pptx
    ├── duplicate.html
    └── corrupted.pdf
```

Intake first converts or normalizes each original file into temporary Markdown:

```text
.
├── inbox/
│   ├── paper.pdf
│   ├── notes.md
│   ├── slides.pptx
│   ├── duplicate.html
│   └── corrupted.pdf
└── intake/
    └── tmp/
        └── YYYY-MM-DD/
            ├── paper/
            │   ├── source.md
            │   ├── digest.md
            │   └── chunks/
            │       ├── index.md
            │       ├── 01.md
            │       └── 02.md
            ├── notes/
            │   └── source.md
            ├── slides/
            │   ├── source.md
            │   └── digest.md
            └── duplicate/
                └── source.md
```

If `corrupted.pdf` cannot be converted, stop handling that file immediately:

```text
.
├── inbox/
│   ├── paper.pdf
│   ├── notes.md
│   ├── slides.pptx
│   └── duplicate.html
├── raw/
│   └── unsupported/
│       └── corrupted.pdf
└── intake/
    └── logs/
        └── YYYY-MM-DD.md
```

Then run Source Review Gate on the temporary Markdown and optional digests:

| File             | Review input                                            | Outcome        | Result                                                                        |
| ---------------- | ------------------------------------------------------- | -------------- | ----------------------------------------------------------------------------- |
| `paper.pdf`      | `intake/tmp/YYYY-MM-DD/paper/source.md`, chunks, digest | `digested`     | Promote to `intake/processed/`, move original to `raw/digested/`, clean `intake/tmp/`, update wiki |
| `notes.md`       | `intake/tmp/YYYY-MM-DD/notes/source.md`                 | `digested`     | Promote to `intake/processed/`, move original to `raw/digested/`, clean `intake/tmp/`, update wiki |
| `slides.pptx`    | `intake/tmp/YYYY-MM-DD/slides/source.md`, digest        | `needs-review` | Move original to `raw/needs-review/`, record the question, clean `intake/tmp/` |
| `duplicate.html` | `intake/tmp/YYYY-MM-DD/duplicate/source.md`             | `ignored`      | Move original to `raw/ignored/`, log the reason, clean `intake/tmp/`           |
| `corrupted.pdf`  | conversion failure                                      | `unsupported`  | Move original to `raw/unsupported/`, log the blocker                          |

Final state after accepted files are ingested:

```text
.
├── inbox/
├── raw/
│   ├── digested/
│   │   ├── paper.pdf
│   │   └── notes.md
│   ├── needs-review/
│   │   └── slides.pptx
│   ├── ignored/
│   │   └── duplicate.html
│   └── unsupported/
│       └── corrupted.pdf
├── intake/
│   ├── processed/
│   │   └── YYYY-MM-DD/
│   │       ├── paper/
│   │       │   ├── source.md
│   │       │   ├── summary.md
│   │       │   ├── manifest.md
│   │       │   ├── digest.md
│   │       │   └── chunks/
│   │       │       ├── index.md
│   │       │       ├── 01.md
│   │       │       └── 02.md
│   │       └── notes/
│   │           ├── source.md
│   │           ├── summary.md
│   │           └── manifest.md
│   └── logs/
│       └── YYYY-MM-DD.md
├── reviews/
│   └── source-review/
│       └── YYYY-MM-DD.md
├── logs/
│   └── wiki.md
└── wiki/
    ├── home.md
    ├── index.md
    ├── overview.md
    └── concepts/
        └── relevant-concept.md
```

The important invariant is that source review happens after conversion, because review should judge readable Markdown or digest output. Original files are moved only after conversion and review produce a final decision.

Files in `raw/needs-review/` remain pending until their review question is resolved. They do not update wiki pages, appear as accepted sources, or move to `intake/processed/` until a later review marks them `digested`.

### 8. Reflect

Use reflect for user-confirmed, discussion-derived knowledge. User ideas, preferences, workflow corrections, and architectural judgments are not source-derived knowledge; treat them as reflection sources.

1. Preserve only durable user-confirmed ideas: corrections, preferences, workflow rules, architectural decisions, arguments, comparisons, conclusions, or cross-page links that are likely to matter later.
2. Do not preserve one-off instructions, temporary reactions, unresolved brainstorming, or unconfirmed ideas as wiki knowledge.
3. If the user did not explicitly ask to reflect, propose the small update list first and wait for confirmation.
4. Write the confirmed discussion source record to `reviews/reflection/YYYY-MM-DD.md`, including the confirmed idea, date, scope, affected pages, and any open follow-up.
5. Add confirmed insights to relevant pages in a `> [!reflect] YYYY-MM-DD` callout.
6. Add `reviews/reflection/YYYY-MM-DD.md` to the page's `sources` list and update the `updated` field when frontmatter exists.
7. Route the update by content: workflow rules update `WIKI.md` or usage docs, knowledge judgments update `wiki/concepts/`, `wiki/claims/`, or `wiki/syntheses/`, and unresolved research threads update `questions/`.
8. Create a new synthesis page only when the discussion produced a standalone argument worth preserving.
9. Update `wiki/index.md` and `logs/wiki.md` when pages change.

Never use a reflect callout for source-derived content.

## Workflow: Use Knowledge

Use this mode when the user asks a question, asks what the wiki says, asks for evidence, asks for a synthesis, or asks for a deliverable.

1. Start with `wiki/index.md` and `wiki/overview.md` when they exist.
2. Search relevant wiki pages under `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/claims/`, and `wiki/syntheses/`; also check `questions/` and `artifacts/` when prior investigations or deliverables matter.
3. Read the most relevant pages and their cited sources when accuracy matters.
4. Answer from compiled wiki knowledge, not from raw search alone.
5. For research questions, separate direct answer, supporting evidence, counterevidence, uncertainty, and open questions.
6. Cite wiki pages, intake outputs, or raw source paths for non-obvious claims.
7. If the answer produces durable synthesis, save it under `wiki/syntheses/` when the user asks or confirms.
8. If the user asks for a deliverable, write it under `artifacts/`.
9. If the answer exposes an unresolved investigation thread worth tracking, write or update it under `questions/` when the user asks or confirms.

If the wiki has no relevant page, say so and offer the smallest useful next action: inspect raw material, review sources, process an intake item, or create a `questions/` investigation note.

## Workflow: Maintain Wiki

Use this mode when the user asks for lint, health check, cleanup, consistency review, or when the wiki appears inconsistent.

Check for:

1. Broken wikilinks.
2. Orphan pages that should be connected.
3. Duplicate pages for the same entity, concept, claim, or source.
4. Claims without sources.
5. Claims with support but no counterevidence check.
6. Stale claims superseded by newer sources.
7. Contradictions that are not represented clearly.
8. Missing source summaries.
9. Important concepts mentioned repeatedly but lacking pages.
10. `wiki/index.md` entries that are missing, stale, or inaccurate.
11. `logs/wiki.md` gaps for recent operations.
12. Intake manifests that list wiki, question, or artifact paths that do not exist.
13. Digested raw files that lack intake outputs.
14. Intake outputs that were never logged.
15. `questions/` items that have been resolved but not reflected into wiki pages or closed.
16. `artifacts/` that cite missing wiki pages, intake outputs, or source paths.

Fix mechanical issues directly when the correct fix is clear. For substantive contradictions, source interpretation, page merges, deletions, or changes of judgment, summarize the proposed resolution and ask the user first.

## Confidence and Lifecycle

Assign confidence based on evidence, not tone:

- `high`: supported by multiple reliable sources, direct verification, or strong method.
- `medium`: supported by one clear source or several weaker converging sources.
- `low`: plausible but weakly supported, inferred, actively disputed, or awaiting review.

Use lifecycle status to keep the wiki honest:

- `draft`: newly generated and not reviewed.
- `reviewed`: checked by the user or a later agent pass.
- `verified`: source-backed and still current.
- `stale`: likely outdated or superseded.
- `archived`: retained for history but not active guidance.

Represent confidence and lifecycle as frontmatter properties, not as tags. Use `confidence:` and `status:` for machine-readable state. Use tags only for topics, domains, or cross-cutting labels that help browsing.

When newer information contradicts older information, preserve the old claim if historically useful, but mark it as superseded and link to the newer claim.

## Agent Behavior

Work like a careful Obsidian wiki maintainer.

1. Prefer small, correct updates over broad rewrites.
2. Preserve existing useful structure unless it conflicts with the task.
3. Do not invent facts, citations, dates, or relationships.
4. Do not hide uncertainty. Mark uncertain claims clearly.
5. Keep raw originals unmodified and generated Markdown traceable.
6. Use the three workflow modes consistently.
7. Use the shortest workflow that fully satisfies the user's request.
8. Update `wiki/index.md` and `logs/wiki.md` whenever wiki content changes.
9. Update `wiki/home.md` only when the wiki purpose, main topics, current artifacts, or major open questions change.
10. Put user-facing deliverables in `artifacts/`.
11. Do not create pages for every named thing. Create pages when they improve reuse, traceability, or synthesis.

## Natural Language Triggers

Plain English requests are valid. The user does not need exact command syntax.

Add Knowledge triggers:

```text
review sources
triage inbox/
what should I ingest next?
intake
process raw files
convert raw files to markdown
ingest intake/processed/YYYY-MM-DD/source-slug/source.md
process this source
extract claims
reflect
file this back into the wiki
```

Use Knowledge triggers:

```text
what does the wiki say about topic?
what evidence supports this?
what are the counterarguments?
synthesize this topic
write a literature review
create an artifact
save this as an artifact
```

Maintain Wiki triggers:

```text
lint
health-check the wiki
find broken links
find stale claims
clean up duplicates
```

## Minimal First Run

For a new vault, create the core workflow scaffold first:

```text
.
├── inbox/
├── raw/
│   ├── digested/
│   ├── needs-review/
│   ├── ignored/
│   └── unsupported/
├── intake/
│   ├── tmp/
│   ├── processed/
│   └── logs/
├── reviews/
│   ├── source-review/
│   └── reflection/
├── logs/
│   └── wiki.md
├── questions/
├── artifacts/
└── wiki/
    ├── home.md
    ├── index.md
    ├── overview.md
    ├── sources/
    ├── entities/
    ├── concepts/
    ├── claims/
    └── syntheses/
```
