# LLM Wiki Operating Guide

This file is the compact operating contract for an agent-maintained Markdown LLM Wiki.

## Conversation Start

Every conversation in a knowledge workspace begins by locating the active workspace root and reading that root's complete `WIKI.md` and `PROJECT.md`. Programming, debugging, questions, research, file operations, resumed conversations, and delegated conversations all use this same start before planning, searching, answering, or writing.

## Core Goal

Maintain a persistent, source-traceable knowledge base that compounds over time. The human sets priorities and confirms material judgments. The agent handles source review, intake, extraction, ingestion, synthesis, artifacts, and routine maintenance through the shortest applicable workflow.

## Directory Contract

```text
.
├── inbox/             New submitted files and generated live-URL source captures.
├── raw/
│   ├── digested/       Accepted lifecycle source artifacts.
│   ├── needs-review/   Source artifacts awaiting judgment.
│   ├── ignored/        Reviewed source artifacts not selected for ingest.
│   └── unsupported/    Source artifacts that cannot currently be processed.
├── intake/
│   ├── tmp/            Temporary reviewable Markdown.
│   ├── processed/      Accepted intake Markdown.
│   └── logs/           Daily source-handling logs.
├── reviews/
│   ├── source-review/  Source Review Gate records.
│   └── reflection/     Confirmed discussion-derived source records.
├── logs/wiki.md        Append-only high-level operation history.
├── questions/          Open investigation and pending-decision records.
├── artifacts/          User-facing deliverables.
└── wiki/
    ├── home.md         Human-facing entrypoint.
    ├── index.md        Thin navigation catalog.
    ├── overview.md     Concise whole-wiki synthesis.
    ├── sources/        One substantive card per digested source.
    ├── entities/       People, organizations, projects, tools, files, datasets.
    ├── concepts/       Reusable ideas, methods, terms, and patterns.
    ├── claims/         Claims with evidence, counterevidence, and uncertainty.
    └── syntheses/      Durable answers, comparisons, timelines, and briefs.
```

Create only the directories needed by confirmed work. Detailed source records belong in their owning pages; indexes, dashboards, queues, and catalogs remain thin projections.

## Core Invariants

1. **Local knowledge first.** Before external search, locate the relevant local index entry, page, source card, and cited source. Do not start external research when local knowledge can answer the request. State the gap before expanding the search.
2. **Lifecycle source truth.** User-submitted files enter through `inbox/` unchanged. Generated live-URL captures follow the deterministic rule in `source-extraction`. Lifecycle source artifacts under `inbox/` and `raw/` remain unedited unless the user explicitly requests a source edit.
3. **One final raw state.** Every handled source ends under exactly one of `raw/digested/`, `raw/needs-review/`, `raw/ignored/`, or `raw/unsupported/`. `raw/needs-review/` is an active queue.
4. **Traceable paths.** Preserve the source-relative parent path and the original source-language base filename under `intake/tmp/`, `intake/processed/`, and `wiki/sources/`. Omit only the original extension. Processing dates belong in records, not intake path components.
5. **Temporary output closes.** Agent-generated extraction, normalization, chunk, and summary files stay under `intake/`; completed handling leaves no source folder in `intake/tmp/`.
6. **Evidence-backed knowledge.** Factual wiki claims cite an original source, accepted intake output, substantive source card, another evidence-bearing wiki page, or a confirmed reflection record. Unsupported but useful claims remain questions or low-confidence claims.
7. **Text-first intake.** Material becomes reviewable Markdown before entering `intake/processed/` or `wiki/`. Passive provider attachments travel with their intake folder; active OCR, transcription, or visual interpretation follows `PROJECT.md`.
8. **Stable names.** Preserve source-derived language and text. Direct chunk files and directories use numeric path components; exact source titles and order tokens remain in headings and the nearest chunk index. Project-specific cross-source naming follows `PROJECT.md`.
9. **No secrets in knowledge.** Credentials, tokens, private endpoints, and local secret values belong only in the project-root `.env`.
10. **Project gate.** Before creating a project-specific subject, category, path, name, acceptance state, or source policy, use confirmed `PROJECT.md` values. When a missing decision changes the write, confirm it and update `PROJECT.md` first.
11. **One owner per state.** Detailed maintained records are canonical. `wiki/index.md`, `wiki/home.md`, dashboards, queues, and catalogs show only the state they independently own and link to the canonical record.
12. **Append-only operation history.** `logs/wiki.md` receives one concise entry per completed operation or coherent batch. Historical entries remain historical records.

## Markdown and Page Contract

Use the local `obsidian-markdown` skill for exact YAML, wikilink, table, callout, embed, and footnote syntax. Use `obsidian-wiki-lint` as the deterministic Markdown gate.

- Vault-internal traceability uses wikilinks. Frontmatter `sources:` entries are quoted wikilink strings; external URLs are quoted plain strings.
- Page-level `sources:` does not replace citations beside source-dependent facts, numbers, quotations, or contested judgments.
- For canonical knowledge pages under `wiki/`, `type` is one of `source`, `entity`, `concept`, `claim`, or `synthesis`. Work products may use `type: artifact` and `type: question`.
- `status` is `draft`, `reviewed`, `verified`, `stale`, or `archived`: respectively unfinished, reviewed but not fully verified, accepted against its evidence and checks, no longer current, or retained only as history.
- `confidence` is `low`, `medium`, or `high`: respectively weak or incomplete support, supported with a material limitation, or strong direct support without a known material contradiction.
- Use `docs/wiki-page-templates.md` for final page shapes.

Every `raw/digested/` source has exactly one substantive source card under the matching `wiki/sources/` path. A valid source card contains a summary, key points, supported claims, scope, limitations, and links through the source review and intake records to the lifecycle source.

## Workflow Router

There are three workflows:

```text
Add Knowledge
Use Knowledge
Maintain Wiki
```

Select the smallest workflow that produces the requested result.

## Add Knowledge

Use this workflow for submitted sources, intake processing, ingestion, confirmed reflection, and explicit requests to record knowledge.

### Source Intake

Use the local `source-extraction` skill. Its `references/intake-lifecycle.md` owns the detailed intake sequence, deterministic live-URL name, extraction-quality thresholds, archive member handling, provider side outputs, cleanup, and reprocessing. `references/large-source-chunking.md` owns detailed chunk mechanics.

The stable lifecycle is:

1. Establish one lifecycle source and its source-relative identity.
2. Produce reviewable Markdown under `intake/tmp/` with the provider and approval policy from `PROJECT.md`.
3. Run the intake-file audit and, when needed, semantic chunking and chunk audit.
4. Run Source Review Gate against readable temporary output, not the filename or provider exit code.
5. Apply one outcome, move the lifecycle source to its matching raw state, record the decision, and close temporary output.
6. For `digested`, promote the intake folder and continue to ingest.

| Outcome | Raw state | Next action |
| --- | --- | --- |
| `digested` | `raw/digested/` | Promote accepted intake output and ingest. |
| `needs-review` | `raw/needs-review/` | Record the concrete question and await resolution. |
| `ignored` | `raw/ignored/` | Record the reviewed reason and stop. |
| `unsupported` | `raw/unsupported/` | Record the processing blocker and stop. |

Each accepted intake folder contains `source.md`, `summary.md`, and `manifest.md`; optional `digest.md`, `chunks/`, and provider side outputs retain distinct roles defined by the source-extraction lifecycle reference.

### Ingest

1. Read `summary.md`, `manifest.md`, and `chunks/index.md` when available, then inspect only the source regions required for accuracy.
2. Create or update the one source card and only the entity, concept, claim, synthesis, or question pages that improve reuse or traceability.
3. Preserve disagreement, uncertainty, limitations, and claim-level evidence.
4. Run `obsidian-wiki-lint` on each changed Markdown file or the smallest affected scope. Use the whole `wiki/` scope for migrations, navigation-wide changes, and whole-wiki maintenance.
5. Update the intake manifest, navigation projections, and operation log only where the content change requires them.

### Reflect

Persist discussion-derived corrections, preferences, decisions, or arguments only when the user explicitly asks or confirms. Record the confirmed discussion under `reviews/reflection/YYYY-MM-DD.md`, update the owning knowledge or question page with that source, then update required projections and `logs/wiki.md`.

## Use Knowledge

Use this workflow for questions, explanations, evidence checks, synthesis, comparisons, drafts, and other deliverables.

1. Locate the smallest relevant scope through the index, overview, exact search, or linked pages.
2. Read the most relevant knowledge pages and cited evidence.
3. Answer from compiled local knowledge. Separate direct answer, evidence, counterevidence, uncertainty, and open questions when they matter.
4. Write a requested deliverable under `artifacts/`; save a durable synthesis or question only when the user asks or confirms.
5. When this workflow writes Markdown, lint the written file or the smallest affected scope.

A request to answer, explain, check, or correct an answer is not by itself a
request to write the wiki. A request to record a wrong question, correction,
source, or synthesis supplies write permission and routes to its owning Add
Knowledge path. When an already persisted answer is corrected within an
authorized scope, update the owning page, evidence, affected projections, and
`logs/wiki.md` together.

## Maintain Wiki

Use this workflow for lint, cleanup, health checks, broken links, duplicates, stale claims, contradictions, source-card quality, evidence support, source-to-wiki coverage, construction opportunities, and ownership consistency.

1. For a whole-wiki health or lint review, run `obsidian-wiki-lint` first for deterministic Markdown, link, footnote, frontmatter, traceability-path, and orphan diagnostics. A focused validator may reuse the same parser and resolver and run only the smallest relevant lint scope.
2. Use `wiki-quality-review` for evidence support, counterevidence, contradictions, stale or duplicate knowledge, circular source chains, source-to-wiki coverage of accepted material, construction opportunities, canonical-record mismatches, and project-defined acceptance states.
3. Use `wiki-contract-review` for package files, entrypoint contracts, skills, scripts, initialization, upgrades, and runtime-structure drift.
4. Use `wiki-maintenance-feedback` for an explicitly requested maintainer-ready report, or when a brief disclosure cannot preserve the evidence needed to hand off a confirmed reusable foundation defect. The skill packages existing evidence; its detailed report fields and states stay in that skill. Routine findings need only a concise disclosure.

A review, audit, or health-check request is read-only unless the user also asks for fixes. Existing repair authorization remains valid: complete authorized fixes and report their evidence without requiring another approval solely because the work includes judgment. Ask only for unresolved material choices, changed scope, or missing permissions. A report request alone does not authorize repair, persistence, tracker updates, or external transmission. Reuse any authorization already given for those actions.

## Growing Surfaces

- Locate a relevant heading, date range, exact identifier, or tail window before reading a growing index, overview, log, dashboard, or queue.
- Update only the affected entry or current section. Detailed content remains on its canonical record.
- `wiki/index.md` changes only when navigation, page identity, or a page's one-line purpose changes.
- `wiki/home.md` changes only when the wiki purpose, main topics, current artifacts, or major open questions change.
- Resolved detail leaves current-state dashboards and queues for its owning record, artifact, question, or log.

## Completion

A completed write has traceable evidence, valid Markdown, closed temporary state, updated canonical records, only the projections whose displayed state changed, and one concise operation-log entry. Report failed or unrun checks and remaining uncertainty plainly.
