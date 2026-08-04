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
4. Extract or stage reviewable Markdown as `source.md` under the temporary intake folder. Stage a Defuddle capture unchanged and do not run Defuddle against it again.
5. Run `audit_intake_file.py` against the new `source.md`. When it reports `large_source`, use `large-source-chunking.md`; when chunks exist, run `audit_chunks.py` before Source Review Gate.
6. Classify extraction quality separately from source value. A provider exit code is not an acceptance decision.
7. Run Source Review Gate against the temporary Markdown, chunks, optional `digest.md`, and relevant provider side outputs.
8. For `digested`, promote the complete temporary folder to `intake/processed/`, write `summary.md` and `manifest.md`, move the source artifact to `raw/digested/`, remove the temporary folder, and continue to ingest.
9. For `needs-review`, move the source artifact to `raw/needs-review/`, preserve useful review notes and the unresolved question, then delete the temporary folder and disposable side outputs.
10. For `ignored`, move the source artifact to `raw/ignored/`, log the reason, then delete the temporary folder and side outputs.
11. For `unsupported`, move the source artifact to `raw/unsupported/`, log the blocker, then delete the temporary folder and side outputs.
12. Record every handled source in `intake/logs/YYYY-MM-DD.md`, including its complete identity, source path or submitted URL, final raw destination, and generated Markdown path. No handled source remains in `inbox/`, and no completed source leaves a folder under `intake/tmp/`.

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
| `needs-review` | `raw/needs-review/<source-relative-path>` | Preserve the question and useful review notes. |
| `ignored` | `raw/ignored/<source-relative-path>` | Preserve the decision; no accepted intake output. |
| `unsupported` | `raw/unsupported/<source-relative-path>` | Preserve the blocker; no accepted intake output. |

Use `digested` for readable, relevant material that adds reusable evidence, concepts, contradictions, decisions, examples, or stronger support. Use `needs-review` when value cannot be judged reliably. Use `ignored` only after the content can be judged. Use `unsupported` when the source cannot currently be extracted or trusted enough to review.

Write decisions to `reviews/source-review/YYYY-MM-DD.md`. Source review does not update wiki knowledge pages.

## Archives

A submitted archive is one lifecycle source with one Source Review Gate outcome and one raw-state destination. Before extraction, create a member listing. Record every inspected member and its disposition, and extract useful members only as temporary units inside the archive's intake folder.

For `digested`, keep the full listing in `manifest.md`. For other outcomes, preserve the listing in the source review or intake log before cleanup. An essential member that still needs judgment makes the archive `needs-review`; an unsupported essential archive structure makes it `unsupported`. Irrelevant members may be skipped and recorded without creating separate raw-state entries.

## Provider Side Outputs

Provider-returned images and attachments remain under the same intake folder as `source.md`, normally under `images/`. Promote them with a `digested` intake folder or delete them with every other temporary outcome, and record the accepted path or deleted disposition on the durable record for that outcome.

Passive preservation does not authorize OCR, visual interpretation, summaries, or wiki knowledge derived from those files. Active use follows the configured `PROJECT.md` policy.

## Accepted Intake Folder

Every accepted folder contains:

```text
source.md
summary.md
manifest.md
```

It may also contain `digest.md`, `chunks/`, and provider side outputs.

- `source.md` is the canonical reviewable extraction entrypoint.
- `summary.md` records acceptance, extraction reliability, caveats, and recommended ingest scope.
- `manifest.md` records the source artifact, submitted URL when applicable, generated outputs, source review, and resulting wiki, question, or artifact paths.
- `digest.md` is optional review support, not a second summary or result ledger.
- `chunks/index.md` owns chunk navigation and source ranges; `large-source-chunking.md` owns its detailed structure.

Avoid repeating the same summary, caveat, decision, or inventory across these files. Choose one owner and link to it where another file needs the information.

## Excerpt-Type `source.md`

Use excerpt form only when the full extraction is not the right review surface. Each retained block includes the source title, original and extracted paths, full heading context, and the reason it was kept. A table excerpt also includes the table title, full header, relevant complete rows, and required notes or footnotes. Isolated keyword hits, naked rows, or reordered snippets are incomplete.

## Reprocessing

Restart from the lifecycle source in its current raw state. When a source becomes `digested` after an earlier `ignored`, `unsupported`, or `needs-review` state:

1. Close the old raw state so the same source-relative path exists in only one state.
2. Append the new intake log and source-review decision.
3. Write the accepted `source.md`, `summary.md`, and `manifest.md`.
4. Update the source card and affected wiki pages.
5. Update navigation only when it changed, then append one `logs/wiki.md` operation entry.

`raw/needs-review/` is an active queue. A resolved item finishes as `digested`, `ignored`, or `unsupported` rather than remaining in two states.
