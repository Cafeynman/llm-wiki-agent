# Intake Lifecycle and Source Review

Use this reference after `source-extraction` has selected a provider. It owns the detailed source-artifact movement, temporary-output handling, Source Review Gate, accepted intake files, archive handling, and reprocessing procedure. `WIKI.md` retains the short lifecycle and write boundary that every conversation reads.

## Source Identity and Output Path

For a submitted file, preserve the original file unchanged. Its intake directory is:

```text
intake/tmp/source-relative-parent/original-source-base-filename/
```

Remove only the extension from the base filename. Preserve language, case, whitespace, punctuation, and other valid characters. The source-relative path is the path below `inbox/` for first intake or below the current `raw/<state>/` directory for reprocessing. Omit `source-relative-parent/` when the source is directly under that root.

For a submitted live URL, Defuddle first materializes:

```text
inbox/web/<source-language-page-title>--<url-hash>.md
```

`<url-hash>` is the first eight lowercase hexadecimal characters of SHA-256 over the exact submitted URL encoded as UTF-8. Percent-encode only Windows-invalid filename characters and control characters in the title segment. Preserve the exact page title and submitted URL in frontmatter; use Defuddle's domain value when the page has no title. This generated capture is the lifecycle source artifact and the sole exception to original-file naming and to the rule that generated Markdown does not enter `raw/`.

Source-relative paths are traceability, not taxonomy. A collision between distinct source artifacts becomes `needs-review`; record the question instead of inventing a suffix.

## Intake Procedure

1. Choose the lifecycle source. A new submitted file starts under `inbox/`. A reprocessed source starts in its current `raw/<state>/` path. A live URL first becomes the deterministic Defuddle capture above.
2. Record the complete source path or submitted URL, exact filename, source kind or file type, size, and basic readability.
3. Apply the OCR, transcription, or frame-OCR approval rule from `PROJECT.md` before enabling that operation.
4. Extract or stage reviewable Markdown as `source.md` under the temporary intake folder. Stage a Defuddle capture unchanged and do not run Defuddle against it again. For ordinary extraction and provider-part assembly, `source.md` keeps the complete extracted text; only the Excerpt-Type contract below permits a narrower review surface.
5. Run `audit_intake_file.py` against the new `source.md`. Resolve hard reviewability failures before continuing. When it reports `large_source`, use `large-source-chunking.md`; generate derived chunks while preserving `source.md` prose and order, run `audit_chunks.py`, and record an accepted size reason directly in the nearest index row only after explicit review. The chunk audit recomposes the hard reviewability checks against the current `source.md`, so a later placeholder, navigation stub, or empty replacement cannot pass the final chunk gate.
6. Classify extraction quality separately from source value. A provider exit code is not an acceptance decision.
7. Run Source Review Gate against the temporary Markdown, chunks, optional `digest.md`, and relevant provider side outputs. An undersized warning remains visible until the reviewer improves the split or records an accepted reason; the audit does not decide mergeability. Unrelated warnings remain review evidence rather than automatic rejection.
8. For `digested`, promote the complete temporary folder to `intake/processed/`, write `summary.md` and the thin `manifest.md` defined below, and run focused Obsidian lint against the final intake folder or each final changed Markdown file. The focused lint and final closeout share the same page-rule boundary: preserved source text, chunk leaves, and provider text are checked for links; authored summaries, manifests, digests, and chunk indexes also receive page-level rules. Closeout additionally checks frontmatter intake traceability links that focused lint excludes from navigation diagnostics. Keep this pre-ingest check and the post-ingest closeout: they detect failures at different stages. Resolve broken links before moving the source artifact to `raw/digested/`, removing the temporary folder, and continuing to ingest.
9. For `needs-review`, move the source artifact to `raw/needs-review/`, preserve useful review notes and the unresolved question, and keep useful extraction, chunks, and side outputs in the matching temporary folder for continued review. A temporary folder is optional when extraction produced nothing useful.
10. For `ignored`, move the source artifact to `raw/ignored/`, log the reason, then delete the temporary folder and side outputs.
11. For `unsupported`, move the source artifact to `raw/unsupported/`, log the blocker, then delete the temporary folder and side outputs.
12. Record one short event per handled source in `intake/logs/YYYY-MM-DD.md`: source identity, outcome, final raw and intake paths when present, and the canonical review link. Keep detailed acceptance reasons and quality judgments in the review record; normal batches may use a compact table. No handled source remains in `inbox/`, and only `needs-review` may retain its matching folder under `intake/tmp/`. One writer owns a source transition; serialize writes to shared intake logs and wiki projections.

## Extraction Quality

| Quality | Standard | Intake effect |
| --- | --- | --- |
| `good` | Main text is readable and the structure supports reliable interpretation. | May continue to source-value review. |
| `usable-with-caveats` | Most content is readable, with local garbling, missing text, broken tables, or structural damage. | May continue; record the caveat. |
| `poor` | Important paragraphs, tables, conclusions, claims, or evidence cannot be judged reliably. | `needs-review`. |
| `unreadable` | Most main content is empty, truncated, garbled, or meaningless. | `needs-review`, unless the lifecycle source itself is damaged or unsupported. |

If roughly 5-20% of the main body is garbled, the best quality is usually `usable-with-caveats`; 20-50% is usually `poor`; more than half is `unreadable`. Critical missing definitions, conclusions, tables, or evidence override those proportions.

## Source Review Gate

Each lifecycle source receives one outcome:

| Outcome | Raw destination | Intake result |
| --- | --- | --- |
| `digested` | `raw/digested/<source-relative-path>` | Promote accepted Markdown and ingest. |
| `needs-review` | `raw/needs-review/<source-relative-path>` | Preserve the question, useful review notes, and useful temporary output when available. |
| `ignored` | `raw/ignored/<source-relative-path>` | Preserve the decision; no accepted intake output. |
| `unsupported` | `raw/unsupported/<source-relative-path>` | Preserve the blocker; no accepted intake output. |

Use `digested` for readable, relevant material that adds reusable evidence, concepts, contradictions, decisions, examples, or stronger support. Use `needs-review` when value cannot be judged reliably. Use `ignored` only after the content can be judged. Use `unsupported` when the source cannot currently be extracted or trusted enough to review.

Write the detailed acceptance reason, quality judgment, limitations, and unresolved decisions once in `reviews/source-review/YYYY-MM-DD.md`. Other records link to this decision. Source review does not update wiki knowledge pages.

## Archives

A submitted archive is one lifecycle source with one Source Review Gate outcome and one raw-state destination. Before extraction, create a member listing. Record every inspected member and its disposition, and extract useful members only as temporary units inside the archive's intake folder.

For `digested`, keep the full listing in `manifest.md`. For other outcomes, preserve the listing in the source review or intake log before cleanup. An essential member that still needs judgment makes the archive `needs-review`; an unsupported essential archive structure makes it `unsupported`. Irrelevant members may be skipped and recorded without creating separate raw-state entries.

## Provider Side Outputs

Provider-returned images and attachments remain under the same intake folder as `source.md`, normally under `images/`. Promote them with a `digested` intake folder, retain useful output with `needs-review`, and delete temporary output for `ignored` or `unsupported`. Record the retained path or deleted disposition on the existing review or intake record.

Passive preservation does not authorize OCR, visual interpretation, summaries, or wiki knowledge derived from those files. Active use follows the configured `PROJECT.md` policy.

Reuse existing project or batch authorization when reviewing images. Confirmed decorative icons with no information may be removed; preserve informative status, warning, operation, and legend symbols, and retain uncertain images. Record explicit image renaming or removal in the existing manifest and regenerate affected chunks consistently. The `build_chunks.py` procedure in `large-source-chunking.md` preserves surrounding prose and the lifecycle original, checks retained references before optional physical attachment deletion, and reports shared or uncertain attachments that remain. No per-image approval is needed when the existing authorization covers the decision.

## Accepted Intake Folder

Every accepted folder contains:

```text
source.md
summary.md
manifest.md
```

It may also contain `digest.md`, `chunks/`, and provider side outputs.

- `source.md` is the Source Review Gate's canonical accepted Markdown extraction. Chunking, indexing, promotion, and rebuilding preserve its prose and order. Explicit image decisions below may update only affected image markup.
- `summary.md` gives a concise content summary and recommended ingest scope, highlighting only limitations needed to use the text and linking to the canonical review for detailed acceptance and quality reasoning.
- `manifest.md` is a thin traceability and replay directory. Record the canonical raw source link; original filename, kind, and byte size; submitted URL when applicable; provider, profile or mode, and only result-affecting options; OCR, transcription, and frame-OCR state; `source.md`, chunk index and count, and provider side-output paths or counts; Source Review outcome and canonical review link; resulting wiki, question, or artifact paths; and the intake-log link. Record a provider/model version or run/task ID only when it is available and affects reproducibility. Archive member inventory remains archive-specific.
- `digest.md` is optional review support, not a second summary or result ledger.
- `chunks/index.md` owns chunk navigation, source ranges, and visible reviewed size decisions; `large-source-chunking.md` owns its detailed structure.

Do not copy chunk mapping, summary prose, caveat prose, quality judgment, or the lifecycle timeline into `manifest.md`. Avoid repeating the same summary, caveat, decision, or inventory across these files. Choose one owner and link to it where another file needs the information.

## Excerpt-Type `source.md`

Use excerpt form only when bounded evidence, rather than the full extraction, is the intended review surface. Do not describe an Excerpt-Type `source.md` as a complete extraction. State the included and excluded scope in `summary.md` and the replay boundary in `manifest.md`. Each retained block includes the source title, original and extracted paths, full heading context, and the reason it was kept. A table excerpt also includes the table title, full header, relevant complete rows, and required notes or footnotes. Isolated keyword hits, naked rows, or reordered snippets are incomplete.

## Reprocessing

Use the lifecycle source in its current raw state as the identity. For `needs-review`, continue from useful existing output in its matching temporary folder after checking that it belongs to the current original and addresses the pending question. Re-extract only when output is absent, invalid, or insufficient for the resolved review scope. When a source becomes `digested` after an earlier `ignored`, `unsupported`, or `needs-review` state:

1. Close the old raw state so the same source-relative path exists in only one state.
2. Append the new intake log and source-review decision.
3. Write the accepted `source.md`, `summary.md`, and `manifest.md`.
4. Update the source card and affected wiki pages.
5. Update navigation only when it changed, then append one `logs/wiki.md` operation entry.

`raw/needs-review/` is an active queue. A resolved item finishes as `digested`, `ignored`, or `unsupported` rather than remaining in two states.

## Scoped Closeout and Delegation

After the final source transition and, for `digested`, ingest, run the read-only `.agents/skills/source-extraction/scripts/audit_source_closeout.py` on that one final raw path:

```powershell
uv run --no-project .agents/skills/source-extraction/scripts/audit_source_closeout.py raw/digested/manual.pdf --vault . --json
```

The checker verifies the selected source's raw state, inbox and temporary residue, accepted files and source card, and outbound wikilinks and inline Markdown links from the accepted intake folder and source card; it reuses intake and chunk audits. Page-level lint applies to authored summaries, manifests, digests, chunk indexes, and the source card; preserved source text and chunk leaves retain source fidelity. It reads no unrelated source content and makes no repairs. A structural pass does not establish semantic completeness, acceptance reasoning, or operation-log accuracy: the source owner still verifies these against the existing review and log. Keep diagnostics in the response or task's temporary work; do not create a second completion ledger. JSON uses schema 1; exit 0 means no structural errors, 1 means unfinished or inconsistent output, and 2 means invalid or unreadable input. Warnings remain visible for the existing review. Reference-style Markdown and HTML links are outside this checker. Check such links when they carry evidence actually used in new knowledge or target files being moved or removed; do not require a whole-source syntax cleanup. A same-stem pending original makes temporary-output ownership uncertain; confirm ownership before cleaning that folder. Same-stem sources in different states remain an ownership warning; two digested sources sharing one intake path are an error.

Delegate only independently checkable units when that helps. Different sources may have different writers. For one large source, delegates review complete chapters or produce disjoint temporary range plans; one source owner reconciles full coverage and publishes. Give each delegate the root, canonical `AGENTS.md` entrypoint, relevant local references, exact input/output scope, and authorization boundary. Delegates return paths, completed scope, checks, and unresolved issues instead of pasting the source into the main conversation. The source owner verifies integration and performs the final transition; serialize writes to each shared manifest, attachment, log, index, or cross-source page while independent source folders remain parallel. Simple work stays direct, and a failed unit does not authorize cleanup of another unit's files.
