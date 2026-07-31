---
name: wiki-quality-review
description: Use for a review, audit, or health check of an initialized wiki's runtime knowledge content, including evidence support, contradictions, stale or duplicate knowledge, and source-card quality. Do not use for source intake or package/workflow contract review.
---

# Wiki Quality Review

Use this skill as the content-quality review procedure inside the `Maintain Wiki`
workflow. It turns the stable checks in `WIKI.md` into an evidence-based review;
it does not create a fourth workflow or a second quality standard.

## Ownership and Boundaries

1. Read the working root's `AGENTS.md` and `WIKI.md` before reviewing. The
   `Maintain Wiki` checklist in `WIKI.md` is authoritative for what the wiki
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

Return numbered findings and concrete proposed changes. A later approval names
the findings that may be changed. If the original request also explicitly asks
for fixes, follow the write boundary in `WIKI.md`: clear mechanical fixes may be
made within the requested scope, while judgment-based changes still require an
approved resolution.

Treat semantic findings as review judgments, not deterministic facts. Each
finding must show enough local evidence for the user to evaluate it. Do not call
a claim false merely because its support is missing, and do not treat the
presence of a citation as proof that the citation supports the claim.

## Review Workflow

1. **Set the scope.** Identify the target root, requested pages or topic, and
   whether the user asked for a scoped or whole-wiki review. Use the Wiki
   Surface Budget Policy in `WIKI.md`; do not load growing indexes, overviews,
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
4. **Apply the `Maintain Wiki` checks.** Give particular attention to:
   claim-to-source support, unsupported inference presented as fact, missing
   counterevidence or limitations, contradictions, superseded or stale claims,
   duplicate knowledge, thin or inaccurate source summaries, repeated concepts
   without a useful home, and unresolved questions that should change current
   knowledge.
5. **Check whole-wiki quality proportionately.** For a whole-wiki request,
   inventory first and prioritize central pages, `draft` or `low`-confidence
   pages, stale claims, disputed topics, weakly sourced syntheses, and isolated
   clusters. Work in explicit batches when the corpus cannot be reviewed
   completely in one pass.
6. **Finish according to the authorized scope.** For a review-only request,
   report without writing. If the original request also asks for fixes, clear
   mechanical findings inside that requested scope are authorized; report and
   apply them, but leave judgment-based findings as proposals until the user
   approves a specific resolution. In either branch, state the inspected scope,
   excluded or sampled scope, lint result, findings, changes if any, and
   remaining uncertainty. Do not create a persistent review file unless the
   user explicitly requests one.

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

Use this workflow for clear mechanical findings covered by an original fix
request and for findings the user later approves by identifier. Judgment-based
findings always require an approved resolution.

1. Re-read each affected file and its evidence. If it changed materially after
   the report, stop on that finding and propose an updated resolution.
2. Apply only the authorized findings. Preserve unapproved findings and
   unrelated user changes.
3. Update `wiki/index.md`, `wiki/home.md`, intake manifests, questions, and
   `logs/wiki.md` only where the authorized content change requires it under
   `WIKI.md`.
4. Rerun `obsidian-wiki-lint` on every changed top-level scope and inspect the
   resulting pages or artifacts directly.
5. Report the applied identifiers, changed files, verification, and any
   authorized finding that could not be completed.

## Guardrails

- Do not edit lifecycle source artifacts under `raw/`.
- Do not invent facts, citations, project preferences, consensus, or missing
  source content to make a page look complete.
- Do not expand the review into external research by default. Report evidence
  gaps; when external verification is required, state the expanded scope and
  route any new source material through `Add Knowledge`.
- Do not generate an aggregate quality score, dashboard, or new review directory
  unless the user asks and the existing contract cannot represent the result.
- Do not automatically chain into `wiki-contract-review`; route package or
  contract questions there only when that is the requested object.
