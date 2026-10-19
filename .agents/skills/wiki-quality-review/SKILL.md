---
name: wiki-quality-review
description: Use for a review, audit, or health check of an initialized wiki's runtime knowledge content, including evidence support, contradictions, stale or duplicate knowledge, source-card quality, accepted-source coverage, and construction opportunities. Do not use for source intake or package/workflow contract review.
---

# Wiki Quality Review

Use this skill as the content-quality review procedure inside the `Maintain Wiki`
workflow. It turns the stable checks in `WIKI.md` into an evidence-based review;
it does not create a fourth workflow or a second quality standard.

## Ownership and Boundaries

1. Begin after the conversation-start read of the working root's complete
   `WIKI.md` and `PROJECT.md`; on first entry, `AGENTS.md` has also been read.
   The `Maintain Wiki` contract in `WIKI.md` is authoritative for what the wiki
   must satisfy.
2. Run the local `obsidian-wiki-lint` skill first for deterministic Markdown,
   link, footnote, and orphan diagnostics. Do not reimplement those checks here.
3. Source extraction quality and source admission belong to `source-extraction`
   and the Source Review Gate under `Add Knowledge`.
4. Package files, workflow contracts, skills, scripts, init/upgrade behavior,
   and initialized-vault contract conformance belong to
   `wiki-contract-review`.
5. Use `PROJECT.md` only for confirmed project-specific subject, terminology,
   structure, and naming preferences. Do not invent missing preferences.

## Review Contract

A review, audit, or health-check request is read-only unless the user also asks
for fixes. Do not treat the review request itself as permission to rewrite wiki
content, update indexes or logs, merge pages, or delete files.

Return numbered findings and concrete proposed changes. When fixes are also
authorized, apply resolutions supported by evidence and the confirmed target.
Ask only about unresolved material judgments, scope changes, or permissions;
reuse decisions and authorization already supplied by the user.

Treat semantic findings as review judgments, not deterministic facts. Each
finding must show enough local evidence for the user to evaluate it. Do not call
a claim false merely because its support is missing, and do not treat the
presence of a citation as proof that the citation supports the claim.

## Review Workflow

1. **Set the scope.** Identify the target root, requested pages or topic, and
   whether the user asked for a scoped or whole-wiki review. Use the Wiki
   `Growing Surfaces` policy in `WIKI.md`; do not load growing indexes, overviews,
   or logs in full when a bounded read can answer the question.
2. **Establish the static baseline.** From the working root, run:

   ```powershell
   uv run --no-project .agents/skills/obsidian-wiki-lint/scripts/lint_wiki.py --vault . --scope wiki
   ```

   Adapt the scope when the confirmed target is narrower. Record failures and
   deterministic diagnostics as evidence; do not apply lint fixes during a
   review-only task.
3. **Locate the knowledge and its evidence.** Start from the relevant
   `wiki/index.md` entry, `wiki/overview.md` section, exact search results, or
   linked pages. Read cited source cards and their supporting intake or original
   source only when needed to judge whether a claim, summary, quotation, number,
   or contested interpretation is actually supported.
4. **Audit accepted-source coverage when it is in scope.** For a source, topic,
   or whole-wiki health review, use the Source-to-Wiki Coverage procedure below
   to identify material ingest gaps and useful construction opportunities.
5. **Apply the `Maintain Wiki` checks.** Give particular attention to:
   claim-to-source support, unsupported inference presented as fact, missing
   counterevidence or limitations, contradictions, superseded or stale claims,
   duplicate knowledge, thin or inaccurate source summaries, repeated concepts
   without a useful home, and unresolved questions that should change current
   knowledge. Also check for catalogs, indexes, queues, or dashboards used as
   pseudo-sources; circular evidence chains; duplicate identifiers or detailed
   inventories; index rows that do not match canonical records; and
   project-defined acceptance states unsupported by the available question,
   answer, classification, or evidence.
6. **Check whole-wiki quality proportionately.** For a whole-wiki request,
   inventory first and prioritize central pages, `draft` or `low`-confidence
   pages, stale claims, disputed topics, weakly sourced syntheses, and isolated
   clusters. Work in explicit batches when the corpus cannot be reviewed
   completely in one pass.
7. **Finish according to the authorized scope.** For a review-only request,
   report without writing. When fixes are authorized, apply them within scope;
   leave only unresolved material decisions as proposals. In either branch, state the inspected scope,
   excluded or sampled scope, lint result, findings, changes if any, and
   remaining uncertainty. Do not create a persistent review file unless the
   user explicitly requests one.

## Source-to-Wiki Coverage

Use this procedure to judge whether accepted source material has been
represented well enough for the confirmed review scope and to recommend the
next useful knowledge construction. It audits ingest results; it does not
reopen Source Review Gate or define a fourth workflow.

1. For a whole-wiki review, inventory lifecycle sources under
   `raw/digested/`; for a narrower review, restrict the inventory to the
   confirmed sources or topic. Locate each matching processed intake folder,
   source card, and downstream knowledge pages. A missing required surface may
   block the semantic judgment and should be reported under its existing
   contract owner rather than silently reconstructed.
2. Compare `summary.md`'s recommended ingest scope, `manifest.md`'s resulting
   wiki, question, or artifact paths, the substantive source card, and the
   actual result pages. Manifest entries, citations, and links help locate
   representations but do not prove coverage; inspect the content that is
   supposed to carry the source point.
3. Record review depth as `deep`, `scoped`, `sampled`, or `blocked`. A pass that
   reads only summaries, manifests, and source cards is scoped or sampled and
   cannot establish that the original material was fully digested. To evaluate
   that question, inspect the relevant accepted `source.md`, `chunks/index.md`,
   and source regions or chunks. The source card may itself be incomplete.
4. Evaluate only material that is useful within the confirmed project scope:
   important claims, definitions, methods, decisions, evidence,
   counterevidence, limitations, examples, or unresolved questions. Do not use
   passage, heading, or chunk coverage as the goal. First reject any exact
   source-card template placeholders reported by the standard lint. Then judge
   whether the remaining text is actually source-specific and locates its
   evidence; static placeholder checks are not proof of semantic quality. Do
   not require a fixed number of bullets, clause numbers, or numeric boundaries.
   The source card can be
   sufficient representation. The absence of an optional entity, concept,
   claim, synthesis, or question page is not itself a defect.
5. Give the report-only coverage judgment `no-material-gap-found`,
   `material-gap-found`, or `indeterminate`. The first means only that no
   material omission was found in the inspected scope, not that the source or
   wiki is complete. Use `indeterminate` when extraction quality, source
   access, review depth, or unresolved project context prevents a reliable
   judgment.
6. Report an omission as a `WQ-*` finding only when it materially weakens
   correctness, trust, reuse, or navigation. Report a useful improvement that
   is not a defect separately as a construction candidate. Prefer enriching an
   existing source card or canonical page; suggest a new canonical page,
   synthesis, or question only when it would improve reuse or traceability.
   Suggest source reprocessing only when the accepted text cannot support the
   judgment.
7. State the inspected, sampled, excluded, and blocked scope, the source
   location for each judgment, the existing representation checked, and the
   remaining uncertainty. Review-only coverage work does not edit source
   cards, manifests, knowledge pages, indexes, or logs. When the user approves
   a construction candidate, re-read its evidence and route the approved write
   through `Add Knowledge`.

Use this shape for non-defect construction opportunities:

```markdown
### KC-001 Construction candidate title

- Review confidence: high | medium | low
- Source and locator: source identity plus the inspected heading, range, or chunk
- Existing representation: source card or knowledge pages already checked
- Opportunity: why the candidate would improve reuse, traceability, or synthesis
- Proposed construction: enrich an existing page, create a justified canonical page, open a question, or reprocess the source
- Decision needed: project context or user judgment required before writing
- Affected files: complete paths expected to change if approved
```

## Finding Standard

Lead with findings ordered by material risk. Give every actionable finding a
stable identifier for the current report:

```markdown
### WQ-001 [high] Short finding title

- Review confidence: high | medium | low
- Location: exact page and line or heading
- Evidence: observed text and the source or cross-page evidence checked
- Risk: why this weakens correctness, trust, reuse, or navigation
- Proposed change: the smallest concrete resolution
- Affected files: complete paths expected to change
```

Use severity for impact and review confidence for the strength of the audit
judgment; neither replaces the page's own `confidence` property. Separate
verified defects from plausible concerns and source gaps. Do not report prose
preferences, tone, or harmless variation as knowledge-quality defects.

If no actionable issue is found, say so plainly and report the inspected scope,
checks not performed, and residual risk. Never claim a full-wiki review when the
review sampled only part of the corpus.

## Applying Authorized Findings

Use this workflow for findings covered by the original fix request or a later
approval. Follow the confirmed target and preserve unresolved user decisions.

1. Re-read each affected file and its evidence. If it changed materially after
   the report, stop on that finding and propose an updated resolution.
2. Apply only the authorized findings. Preserve unapproved findings and
   unrelated user changes.
3. Update `wiki/index.md`, `wiki/home.md`, intake manifests, questions, and
   `logs/wiki.md` only where the authorized content change requires it under
   `WIKI.md`.
4. Rerun `obsidian-wiki-lint` on each changed Markdown file or the smallest
   affected scope and inspect the resulting pages or artifacts directly. Use
   the whole `wiki/` scope for a whole-wiki change or migration batch.
5. Report the applied identifiers, changed files, verification, and any
   authorized finding that could not be completed.

## Guardrails

- Do not edit lifecycle source artifacts under `raw/`.
- Do not invent facts, citations, project preferences, consensus, or missing
  source content to make a page look complete.
- Do not expand the review into external research by default. Report evidence
  gaps; when external verification is required, state the expanded scope and
  route any new source material through `Add Knowledge`.
- Do not equate adequate ingest with representing every source passage, heading,
  or chunk. Do not persist coverage judgments as source-card or manifest state;
  they are review-time conclusions that can become stale as the wiki changes.
- Do not generate an aggregate quality score, dashboard, or new review directory
  unless the user asks and the existing contract cannot represent the result.
- Do not automatically chain into `wiki-contract-review`; route package or
  contract questions there only when that is the requested object.
