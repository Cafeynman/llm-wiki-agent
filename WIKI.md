# LLM Wiki Operating Guide

This file defines the common operating rules for an agent-maintained Obsidian LLM Wiki.

## Core Goal

Maintain a persistent knowledge base that compounds over time. Do not treat sources as one-off retrieval material. Preserve source traceability, extract durable knowledge, connect related pages, mark uncertainty, and record meaningful changes.

The human curates priorities and reviews important judgments. The agent handles source review, intake, extraction, ingestion, synthesis, artifact creation, and routine wiki maintenance.

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
│   ├── tmp/            Temporary Markdown extracted from raw files before review.
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
    ├── index.md        Navigation catalog of wiki pages, one-line purpose, and pointers.
    ├── overview.md     Living synthesis of the whole wiki.
    ├── sources/        One content-rich source card per digested source.
    ├── entities/       People, organizations, projects, tools, files, datasets.
    ├── concepts/       Ideas, methods, frameworks, terms, patterns.
    ├── claims/         Important claims that need evidence and counterevidence.
    └── syntheses/      Durable answers, comparisons, timelines, briefs.
```

Create only the directories required for the current task. Do not add exports, dashboards, databases, watchers, static sites, or graph files unless the user asks.

For each digested raw source, write intake outputs under the source-relative path:

```text
intake/processed/source-relative-parent/original-source-base-filename/
├── source.md
├── summary.md
├── manifest.md
├── digest.md        Optional short digest used to support review.
└── chunks/
    ├── index.md
    └── 01-source-heading-or-range.md
```

If the source has no parent directory under the intake root, omit `source-relative-parent`. The `original-source-base-filename` directory must preserve the original source file's base filename and source language. Except for removing the extension, do not translate, romanize, convert to pinyin, slugify, force lowercase, case-normalize, URL encode, or simplify it. Use the same source-relative parent and source-language base filename for source cards under `wiki/sources/`.

The source-relative path is the path below `inbox/` for first intake, or the path below the current `raw/<state>/` directory for reprocessing. Preserve this relative path when moving originals between raw state directories, when writing `intake/tmp/` or `intake/processed/` outputs, and when creating source cards under `wiki/sources/`. The relative path is traceability, not a wiki taxonomy.

Do not add a date directory under `intake/tmp/` or `intake/processed/`. Processing dates belong in `manifest.md`, `intake/logs/YYYY-MM-DD.md`, `reviews/source-review/YYYY-MM-DD.md`, and other dated logs or review records.

If preserving the source-relative output path would collide with an existing path for a distinct source, do not invent a suffix or choose a new title by assumption. Move the duplicate or ambiguous source to `raw/needs-review/`, record the naming collision question, and wait for user judgment.

Use `digest.md` only when it helps review. Use `chunks/` only when the source is too large or structurally complex to handle as one file. Chunking is an intake-output structure, not a raw-file structure: agent-generated Markdown stays under `intake/tmp/` while under review or `intake/processed/` after acceptance, and never goes under `raw/`.

Intake outputs are processing records, not the final place for durable knowledge. Detailed source syntheses, core arguments, concept explanations, and reusable claims belong in `wiki/` pages after ingest, not in `digest.md`, `summary.md`, or `manifest.md`.

## Log Structure

Use `intake/logs/YYYY-MM-DD.md` for daily source handling logs. Use `reviews/source-review/YYYY-MM-DD.md` for daily review decisions. Use `logs/wiki.md` as one append-only high-level operation history grouped by date headings. `logs/wiki.md` may grow over time, so entries should stay concise and should not duplicate detailed intake or source review records. Do not split, summarize, or archive `logs/wiki.md` unless the user explicitly changes the package contract.

## Wiki Surface Budget Policy

Use this policy for growing wiki-maintained surfaces such as `wiki/index.md`,
`wiki/overview.md`, `logs/wiki.md`, dashboards, and long-running queue or index
pages.

1. Treat growing surfaces as navigation or current-state surfaces, not as places
   to store full records, detailed source summaries, full histories, or repeated
   content from other pages.
2. Before reading a growing surface, locate the relevant scope with search,
   headings, date windows, tail reads, linked indexes, manifests, or other local
   pointers. Do not read the whole surface by default when the task only needs a
   local update or answer.
3. Keep searches over growing surfaces narrow or bounded. To check whether a
   known entry exists, search for the exact ID or link. To measure size, use
   count-only output. To find an append point, use the relevant heading or a tail
   window. Do not use broad content-returning searches that can emit an entire
   table, long queue, or log section.
4. When updating a growing surface, change only the affected entry, current
   section, date heading, or short pointer. Create or update the detailed record
   page separately when the content does not fit as navigation metadata.
5. Keep `wiki/index.md` to navigation metadata: page title, type or area, a
   one-line purpose, and links. Do not use it to repeat source-card summaries,
   long syntheses, or detailed page content.
6. Keep `wiki/overview.md` as a concise synthesis organized by stable sections.
   Read or update only the section relevant to the current task unless the user
   asks for a whole-wiki review.
7. For `logs/wiki.md`, use the relevant date heading or the tail of the file for
   routine appends and recent-operation checks. Do not load the full log unless
   the user asks for a full log review or the current task requires it.
8. Dashboards and queue pages should show current state and next action. Move
   resolved history or detailed records to the appropriate artifact, question,
   synthesis, source card, or log entry instead of keeping long histories on the
   current-state page.

## Source and Traceability Rules

1. Treat user-submitted files in `inbox/` and original files under `raw/` as source truth.
2. Do not rewrite, normalize, rename, or edit original file contents unless the user explicitly asks.
3. All new user-submitted original files must enter through `inbox/` before extraction, review, or classification. Once a file is handled by intake, move it out of `inbox/` in the same pass, regardless of outcome.
4. Files already under `raw/digested/`, `raw/needs-review/`, `raw/ignored/`, or `raw/unsupported/` have already entered the lifecycle. They may be reprocessed from their current raw state directory without moving them back to `inbox/`.
5. Preserve the source-relative path when moving originals into or between raw state directories. For first intake, this is the path below `inbox/`; for reprocessing, this is the path below the current `raw/<state>/` directory. The raw state directory records lifecycle status; the preserved relative path records source identity.
6. Agent-generated Markdown never goes back into `raw/`; write temporary extraction output under `intake/tmp/` and accepted outputs under `intake/processed/`.
7. `intake/tmp/` is not a holding area. Every temporary extraction must end by promoting accepted Markdown to `intake/processed/` or by deleting the temporary folder after the original moves to `raw/needs-review/`, `raw/ignored/`, or `raw/unsupported/`.
8. Every factual wiki claim must be grounded in an original source, an intake Markdown output, a cited wiki page, or a confirmed discussion-derived source record under `reviews/reflection/`.
9. If a claim is useful but unsupported, put it in `questions/`, a needs-verification note on the relevant page, or a low-confidence page under `wiki/claims/`.
10. Do not copy API keys, tokens, passwords, private keys, session cookies, or sensitive personal information into generated notes. Redact and cite the source path instead.
11. Intake logs and review reports must record the complete original filename, file type, source path, final raw destination, and any generated Markdown path. Do not use ellipses or shortened paths for source traceability.
12. Intake must preserve meaningful text and identify important non-text material. If useful content appears to depend on figures, screenshots, scans, audio, or other non-text material that was not processed, move the original to `raw/needs-review/` and record the missing processing step.
13. This is a text-first workflow. Attachments, images, scans, screenshots, and audio may remain part of the preserved original source, but they are not first-class wiki content by default. Do not create attachment asset directories, copy images into wiki pages, or add image-reference schemes unless the user explicitly asks for image handling.

## Page Conventions

Use Obsidian-compatible Markdown. Prefer `[[wikilinks]]` for internal wiki pages and normal Markdown links for external URLs. Keep filenames human-readable and stable.

Traceability links to vault-internal files and notes must use Obsidian wikilinks. In frontmatter `sources:`, write vault-internal paths as quoted wikilink strings, for example `"[[raw/digested/source-relative-parent/original-filename.ext]]"` or `"[[intake/processed/source-relative-parent/original-source-base-filename/source.md]]"`. Omit `source-relative-parent/` only when the source is directly under the intake root. External URLs remain quoted plain strings. See `.agents/skills/obsidian-markdown/references/PROPERTIES.md` for exact YAML quoting rules.

Preserve source-derived text exactly as content. Do not delete, replace, romanize, convert to pinyin, slugify, or otherwise normalize special characters just because a target syntax treats them specially. Encode or quote the value only at the output boundary that needs it, such as YAML frontmatter, Markdown table cells, wikilinks, or command examples.

Preserve source-language names for source-specific artifacts: source cards, source-specific reading pages, chunk files and directories, source-derived page titles, headings, aliases, catalog labels, and index entries. Do not translate, romanize, convert to pinyin, slugify, force lowercase, case-normalize, or simplify source-derived names unless the user explicitly asks or `PROJECT.md` records a confirmed naming preference. For cross-source pages such as entities, concepts, claims, and syntheses, follow `PROJECT.md` naming preferences; if none are confirmed, use the dominant language of the relevant sources, or the user's request language when there is no dominant source language. Add alternative-language names as aliases when they help prevent duplicate pages. Fixed system-role filenames, including `source.md`, `summary.md`, `manifest.md`, `digest.md`, `index.md`, `home.md`, `overview.md`, and `logs/wiki.md`, keep their contract names.

Use `type` values from `source`, `entity`, `concept`, `claim`, or `synthesis`; use `status` values from `draft`, `reviewed`, `verified`, `stale`, or `archived`; and use `confidence` values from `low`, `medium`, or `high`.

Use `docs/wiki-page-templates.md` for page templates.

Directory links must explicitly end with `/` or `\`. A directory link points to an existing directory and is not a page link; a link without a trailing slash is treated as a file or note link.

Keep pages focused. A page should have one clear purpose. If a page starts covering multiple topics, split it and link the new pages.

Use `wiki/home.md` as the human-facing main page. It should explain what the wiki is for, main topic areas, important entry points, current artifacts, and major open questions. Do not use it as a changelog.

Use `wiki/index.md` as the structured navigation catalog and `logs/wiki.md` as the operation history. Do not let either file replace `wiki/home.md`.

Write deliverables to `artifacts/` when the user asks for a report, brief, outline, draft, comparison table, template, or other reusable output made from wiki knowledge. Track open questions and investigation trails under `questions/`. These files may use frontmatter with `type: artifact` or `type: question`, but they are work products next to the wiki, not canonical wiki knowledge pages.

Create one source card under `wiki/sources/<source-relative-parent>/original-source-base-filename.md` for every `digested` source. Do not create source cards for `ignored`, `unsupported`, or unresolved `needs-review` files.

A source card is the wiki-facing summary of a source, not an intake receipt. It must contain substantive content: source summary, key points, supported claims, scope, limitations, and links to the raw file, processed Markdown, source review, and manifest. A page with only frontmatter, file size, line count, processing date, or paths is invalid.

Other wiki pages should normally cite the source card instead of citing raw files directly. The source card carries the full traceability chain back to `raw/digested/`, `intake/processed/`, and `reviews/source-review/`.

Use the source card template in `docs/wiki-page-templates.md` when creating a new source card.

## Core Workflows

There are only three workflow modes:

```text
Add Knowledge
Use Knowledge
Maintain Wiki
```

Do not run every subroutine in sequence. Choose the shortest path that fully satisfies the user's request.

Usage examples and natural-language prompts belong in `docs/usage.md`; the batch source lifecycle example belongs in `docs/source-lifecycle.md`.

## Workflow: Add Knowledge

Use this mode when the user adds files, asks to process sources, asks to save discussion insights, or asks to update the wiki with new knowledge.

### 1. Route the Input

Classify the input before acting, then enter the matching path below. The "Start with" column maps directly to the later subsections in this workflow.

| Input type                                                                                               | Start with                           | Continue to                                                                                    |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| A batch of candidate raw files, `inbox/`, or a triage request                                            | Intake                               | Extract each file to `intake/tmp/`, optionally write a digest, then run Source Review Gate     |
| One specific raw file in `inbox/`                                                                        | Intake                               | Extract or stage Markdown to `intake/tmp/`, optionally write a digest, then run Source Review Gate |
| A file already under `raw/digested/`, `raw/needs-review/`, `raw/ignored/`, or `raw/unsupported/` that needs reprocessing | Intake | Use the current raw state directory as the intake root, preserve the path below it, extract to `intake/tmp/`, then run Source Review Gate |
| A new non-Markdown source that needs extraction                                                          | Intake                               | Ensure the original is in `inbox/`, extract to `intake/tmp/`, then run Source Review Gate  |
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

For raw files, use the local `source-extraction` skill to classify the source kind, select the configured provider, and produce reviewable Markdown. Provider selection is project-specific and belongs in `PROJECT.md`; the stable provider contract belongs in `.agents/skills/source-extraction/references/contract.md`.

Before extraction, check whether a batch or file appears likely to benefit from OCR, such as scan-heavy PDFs or image-heavy Word, PowerPoint, and Excel files. If OCR appears available in the current environment, do not enable it automatically. First group the files into `recommend OCR`, `do not recommend OCR`, or `unclear`, then ask the user once whether to enable OCR for the recommended group and how to handle any unclear files.

Use the shortest reliable extraction path allowed by `PROJECT.md`, `.agents/skills/source-extraction/references/source-kinds.md`, and the selected provider's usage document.

The intake order is:

`intake/tmp/` is the first Markdown landing area after extraction or Markdown staging. `intake/processed/` is not a scratch area; it is only for Markdown accepted by Source Review Gate and ready for ingest. Any extraction or Markdown staging path that produces accepted Markdown must follow the same lifecycle and output requirements.

1. Choose the intake root. For first intake, take original files from `inbox/`. For reprocessing, take original files from their current `raw/<state>/` directory.
2. Compute the source-relative path from the intake root, then inspect and record the complete raw file path, exact filename, file type, size, and basic readability.
3. For batch intake and other multi-file requests, perform OCR precheck before extraction when any file appears likely to benefit from OCR. Present the grouped recommendation once and wait for the user's decision before enabling OCR.
4. Use the `source-extraction` skill to select the source kind and provider, then extract or stage the file as temporary Markdown under `intake/tmp/source-relative-parent/original-source-base-filename/`.
5. For archives, create a member listing first. Record each useful member's archive path, filename, detected type, and extraction result. Extract only members that are useful for review.
6. If extraction fails, move the original file to `raw/unsupported/` while preserving its source-relative path, record the blocker in `intake/logs/YYYY-MM-DD.md`, delete the temporary folder, and stop.
7. If extraction technically succeeds but the Markdown is garbled, empty, too thin to judge, obviously truncated, structurally broken, or missing important text, move the original to `raw/needs-review/` while preserving its source-relative path, record the extraction-quality question, move any useful review notes to `reviews/source-review/`, delete the temporary folder, and stop.
8. Run the source-extraction intake file audit on the temporary `source.md` just produced by the current intake step. Normal files need no audit record. If it reports `large_source`, create semantic chunks under the same temporary intake folder before Source Review Gate when reliable source boundaries exist. When `chunks/` is generated, run the chunk audit on the temporary intake folder; resolve hard chunk errors before promotion, and treat warnings as Source Review Gate caveats.
9. If a large, ambiguous, encrypted, noisy, multimodal, or user-selection-dependent source cannot be made reviewable through semantic chunks in the same pass, or if hard chunk audit errors cannot be resolved in the same pass, move the original to `raw/needs-review/` while preserving its source-relative path, record the question, move any useful review notes to `reviews/source-review/`, delete the temporary folder, and stop.
10. Optionally write `digest.md` in the temporary intake folder when a short digest would make review easier; do not make digest mandatory.
11. Run Source Review Gate on the temporary Markdown, chunks, and optional digest, not on the raw filename alone.
12. If the outcome is `digested`, promote the temporary Markdown to `intake/processed/source-relative-parent/original-source-base-filename/`, write `source.md`, `summary.md`, `manifest.md`, include `digest.md` only if it was useful, move the original to `raw/digested/` while preserving its source-relative path, delete the temporary folder, then ingest.
13. If the outcome is `ignored`, move the original to `raw/ignored/` while preserving its source-relative path, log the reason, delete the temporary folder, and stop.
14. If the outcome is `unsupported`, move the original to `raw/unsupported/` while preserving its source-relative path, log the blocker, delete the temporary folder, and stop.
15. If the outcome is `needs-review`, move the original to `raw/needs-review/` while preserving its source-relative path, move any useful review notes to `reviews/source-review/`, delete the temporary folder, and record the question.

After a final outcome is reached for a source, no temporary folder for that source may remain under `intake/tmp/`.

### 4. Source Review Gate

Source Review Gate is an intake step. It runs after extraction or Markdown staging has produced readable temporary Markdown. Its goal is to decide what deserves permanent intake output and wiki ingestion, not to update wiki knowledge pages.

Before assigning a Source Review Gate outcome, classify extraction quality separately from source value. A source must not be treated as `digested` only because extraction exited successfully.

| Quality | Standard | Intake effect |
| --- | --- | --- |
| `good` | Main body text is readable, structure is understandable, and any garbling is minor enough that it does not affect interpretation | May continue to value review |
| `usable-with-caveats` | Most main content is readable, but there is local garbling, missing text, broken tables, or structural damage that should be recorded | May continue to value review, but record the quality caveat in review notes or `summary.md` |
| `poor` | Readable content is mixed with substantial garbling or broken structure, and key paragraphs, tables, conclusions, claims, or evidence cannot be judged reliably | Must become `needs-review` |
| `unreadable` | Most main body content is garbled, mojibake, meaningless symbols, repeated broken characters, empty, or obviously truncated | Must become `needs-review`, unless the original file is clearly damaged or unsupported |

Use conservative thresholds for garbling. If roughly 5-20% of the main body is garbled, the best possible quality is usually `usable-with-caveats`. If roughly 20-50% is garbled, the best possible quality is usually `poor`. If more than half of the main body is unreadable, the quality is `unreadable`. A source whose main body is about 90% garbled must never be classified as `good` or `digested`.

Critical content overrides percentages. If definitions, conclusions, source evidence, important tables, or other core content are garbled or missing, do not classify the extraction as `good` even when the overall garbling ratio appears low.

Each reviewed item receives one outcome that maps to a raw file location:

| Outcome | Raw destination | Intake effect | Meaning |
| --- | --- | --- | --- |
| `digested` | `raw/digested/<source-relative-path>` | Promote temporary Markdown to `intake/processed/`, then ingest | Useful, relevant, readable, and likely to improve the wiki |
| `needs-review` | `raw/needs-review/<source-relative-path>` | Move useful review notes to `reviews/source-review/` and clean `intake/tmp/` | Potentially useful but requires user judgment before final handling |
| `ignored` | `raw/ignored/<source-relative-path>` | Do not promote to `intake/processed/` and do not ingest | Duplicate, irrelevant, too shallow, or not worth preserving |
| `unsupported` | `raw/unsupported/<source-relative-path>` | Do not promote to `intake/processed/` and do not ingest | Cannot currently be extracted, read, or trusted enough to review |

Use `digested` when a source adds new evidence, a useful framework, a meaningful contradiction, a reusable definition, a decision, a timeline, a comparison, a concrete example, or a strong source for a weak claim.

Do not use `ignored` for a source that might contain important information but was not readable enough to judge. Use `unsupported` or `needs-review`.

Do not treat a successful provider exit as acceptance. If the extracted Markdown is garbled, empty, too thin, truncated, structurally broken, or missing expected content, classify it as `needs-review` unless the file is clearly damaged or unsupported.

Write review reports to:

```text
reviews/source-review/YYYY-MM-DD.md
```

Do not update wiki knowledge pages during source review.

Each accepted intake folder under `intake/processed/` must include:

```text
source.md      Reviewable source Markdown from the original file.
summary.md     Processing decision: outcome, extraction quality, source value, caveats, and recommended ingest scope.
manifest.md    Traceability ledger: original file, generated intake outputs, source review, and wiki/question/artifact updates.
```

These files are required for every accepted source, including later reprocessing, repaired document extraction, manual normalization, and any other approved text extraction path. A `source.md` without `summary.md` and `manifest.md` is incomplete and must not be treated as fully ingested.

It may also include `digest.md` when a short digest was useful for review, and `chunks/` when the source required chunking.

Keep accepted intake files distinct:

- `digest.md` is optional review support. It may contain a compact content map, review cues, likely useful sections, and extraction warnings. It must not record final wiki updates, act as the final value judgment, or duplicate the manifest ledger.
- `summary.md` is the final intake processing summary. It should say why the source was accepted, how reliable the extraction is, what caveats matter, and what scope should be ingested. It must not become a detailed source note, chapter-by-chapter digest, or final knowledge synthesis.
- `manifest.md` is the traceability ledger. It should list paths and updates, not content summaries, core viewpoints, detailed quality analysis, or reading recommendations. If quality caveats matter, link to or briefly point at `summary.md` instead of restating them.
- `chunks/index.md` is the chunk directory entrypoint. It must list each chunk path, title or range, source page, slide, section, table, or archive-member range when known, extraction caveats, and review or ingest status. If it already lists chunk titles and ranges, `summary.md` should link to it or state the chunk count rather than copying the full chunk table. For chunked sources, final `summary.md`, `manifest.md`, and source cards must not be finalized while hard chunk audit errors remain.
- For books, reports, standards, manuals, and other long structured sources, prefer semantic chunking under `chunks/`: major chapters may become first-level subdirectories, subchapters may become nested subdirectories, and each directory should have an `index.md`. Follow `.agents/skills/source-extraction/references/large-source-chunking.md` for thresholds and detailed structure.
- For chunked sources, `source.md` remains the canonical extracted-source entrypoint. It may contain the full extracted text when practical. If the full text is too large, `source.md` may be an excerpt-type entrypoint that links to `chunks/index.md` and states that the complete review surface is split under `chunks/`.

Before treating an intake folder as complete, check that `digest.md`, `summary.md`, and `manifest.md` are not all repeating the same source information, quality caveats, value judgment, or processing recommendations. Pick one primary location for each kind of information and link to it from the others only when needed.

#### Excerpt-Type `source.md`

Use excerpt-type `source.md` only when the full extracted source is not the right ingest surface. Every excerpt block must still stand on its own. Do not promote naked keyword hits, isolated table rows, or reordered snippets into `intake/processed/`.

Each excerpt block must include:

1. Source document title.
2. Original source path and extracted Markdown path.
3. Full heading context.
4. For tables: table title, full header, relevant full row or rows, and any notes or footnotes needed to read them correctly.
5. A short note saying why the block was kept.

Missing heading context or required table context means the excerpt is incomplete and must not be ingested.

After intake, move each original file from `inbox/` into exactly one state directory: `raw/digested/`, `raw/needs-review/`, `raw/ignored/`, or `raw/unsupported/`, preserving the path below `inbox/`. `inbox/` must not retain files that were already handled once. Record every move in `intake/logs/YYYY-MM-DD.md` with complete filenames, file types, source paths, and final destinations.

Treat `raw/needs-review/` as a queue, not a final archive. Each file moved there must have a recorded review question in `reviews/source-review/YYYY-MM-DD.md` or `intake/logs/YYYY-MM-DD.md`. When the user or a later agent resolves the question, restart intake from that original file in its current raw state directory, preserve the path below `raw/needs-review/`, extract again to `intake/tmp/` if needed, then finish with `digested`, `ignored`, or `unsupported`. Do not leave a file in `raw/needs-review/` after a final decision exists.

### Reprocessing and State Correction

When a source previously marked `ignored`, `unsupported`, or `needs-review` is later resolved and accepted as `digested`, close the old state in the same pass:

1. Move or remove the old raw state entry so the same source-relative path does not remain in two raw state directories.
2. Update `intake/logs/YYYY-MM-DD.md` for the new handling pass.
3. Update or append `reviews/source-review/YYYY-MM-DD.md` so the latest decision is visible.
4. Write or update the accepted folder's `source.md`, `summary.md`, and `manifest.md`.
5. Update the source card, `wiki/index.md`, and `logs/wiki.md`.

Do not leave a final accepted source represented as both `raw/digested/` and `raw/unsupported/`, or as both `raw/digested/` and `raw/ignored/`.

### 5. Large File and Context Budget Policy

Use this policy whenever a raw file, extracted `source.md`, or generated chunk is too large to read comfortably in the current context.

1. Inspect metadata before reading full content: exact filename, file type, file size, line count, page or slide count, table dimensions, archive listing, headings, extraction warnings when available, and the source-extraction intake file audit alert if `source.md` has already been produced.
2. Do not load a very large original file or `source.md` into context in one pass. Work from `summary.md`, `manifest.md`, and `chunks/index.md` first.
3. When extracted `intake/tmp/.../source.md` is too large to review or ingest as one file, create `intake/tmp/.../chunks/` before Source Review Gate. Use source-defined headings or other reliable boundaries when they exist; do not invent generic chapter names. Run the chunk audit on the temporary intake folder after chunks are created. If the source is accepted, promote the chunked folder to `intake/processed/.../`; if it is not accepted, clean the temporary folder with the rest of `intake/tmp/`.
4. For large sources, create `chunks/` before ingest. Each chunk must be a coherent unit small enough to read and summarize independently. Prefer semantic boundaries such as headings, chapters, subchapters, slides, page ranges, sections, tables, or archive members. Follow `.agents/skills/source-extraction/references/large-source-chunking.md` for detailed chunk structure and chunk audit behavior.
5. Write or update `summary.md` progressively from chunk summaries. The summary should capture the source topic, processing value, extraction caveats, low-value regions, noisy regions, and recommended ingest scope. Do not use `summary.md` as the detailed source synthesis; move durable claims and core viewpoints into `wiki/` during ingest.
6. During ingest, read only the chunks needed for the current wiki update. Do not read all chunks unless the user explicitly asks for a full-source pass and the available context can support it.
7. If a large source cannot be fully reviewed in the current pass, move the original out of `inbox/` to `raw/needs-review/`, record the review question, and clean `intake/tmp/`.
8. If the source is mostly boilerplate, duplicate text, extraction errors, generated logs, raw data dumps, or other noise, do not expand it into the wiki. Record the issue in the review report and move the original to `raw/ignored/`, `raw/needs-review/`, or `raw/unsupported/` according to the blocker.

### 6. Ingest

When a source is ready to become wiki knowledge:

1. Confirm the source path exists.
2. Read `summary.md`, `manifest.md`, and `chunks/index.md` first when available.
3. Read the original source only when accuracy or extraction quality needs verification.
4. Extract durable knowledge: main thesis, key claims, evidence, counterevidence, named entities, important concepts, decisions, recommendations, contradictions, and open questions.
5. Verify Obsidian Markdown before writing wiki pages. Use the local `obsidian-markdown` skill as the syntax contract and run `obsidian-wiki-lint` as the deterministic lint gate.
6. Create or update exactly one content-rich source card under `wiki/sources/<source-relative-parent>/original-source-base-filename.md`.
7. For long books, manuals, standards, reports, or other sources that need a structured reading surface, create or update a source-specific wiki entry only when useful. Put full-source detailed summaries, core viewpoints, knowledge flow, chapter navigation, and chapter-level digests there, for example under `wiki/books/source-relative-parent/original-source-base-filename/`.
8. Create or update relevant pages in `wiki/entities/`, `wiki/concepts/`, `wiki/claims/`, or `wiki/syntheses/` only when useful.
9. Create or update `questions/` only when an unresolved investigation thread is worth tracking separately.
10. Update `wiki/overview.md` only when the source changes the overall synthesis.
11. Update `wiki/index.md`, `wiki/home.md` when needed, and `logs/wiki.md`.
12. Update the intake `manifest.md` when intake outputs led to wiki, question, or artifact changes.

Do not flatten disagreement into false consensus. If sources conflict, preserve the disagreement and cite both sides.

### 7. Reflect

Use reflect for user-confirmed, discussion-derived knowledge. User ideas, preferences, workflow corrections, and architectural judgments are not source-derived knowledge; treat them as reflection sources.

1. Preserve only durable user-confirmed ideas: corrections, preferences, workflow rules, architectural decisions, arguments, comparisons, conclusions, or cross-page links that are likely to matter later.
2. Do not preserve one-off instructions, temporary reactions, unresolved brainstorming, or unconfirmed ideas as wiki knowledge.
3. If the user did not explicitly ask to reflect, propose the small update list first and wait for confirmation.
4. Write the confirmed discussion source record to `reviews/reflection/YYYY-MM-DD.md`, including the confirmed idea, date, scope, affected pages, and any open follow-up.
5. Add confirmed insights to relevant pages in a `> [!reflect] YYYY-MM-DD` callout.
6. Add `reviews/reflection/YYYY-MM-DD.md` to the page's `sources` list and update the `updated` field when frontmatter exists.
7. Route the update by content: knowledge judgments update `wiki/concepts/`, `wiki/claims/`, or `wiki/syntheses/`, and unresolved research threads update `questions/`.
8. Create a new synthesis page only when the discussion produced a standalone argument worth preserving.
9. Update `wiki/index.md` and `logs/wiki.md` when pages change.

Never use a reflect callout for source-derived content.

## Workflow: Use Knowledge

Use this mode when the user asks a question, asks what the wiki says, asks for evidence, asks for a synthesis, or asks for a deliverable.

1. Locate the relevant scope with `wiki/index.md`, `wiki/overview.md`, search,
   headings, or linked indexes when they exist. Treat `wiki/index.md` and
   `wiki/overview.md` as navigation and synthesis surfaces: read only the
   relevant entry or section unless the user asks for a whole-wiki review.
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
