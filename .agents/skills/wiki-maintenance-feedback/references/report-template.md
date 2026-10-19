# Maintainer Feedback Report Template

Render the report in the user's requested or source language. Keep the six core sections below concise; add optional details only when they help a maintainer act. Remove instructional placeholders from the delivered report.

```markdown
# Wiki Maintenance Feedback: <concise title>

## Problem
<Expected and actual behavior, affected path/version, and confirmation basis.
Identify an unconfirmed observation as such.>

## Impact
<Confirmed impact, potential impact, and material unassessed scope.>

## Evidence
<Existing observations, sanitized evidence references, and hypotheses clearly separated.
Include reproduction steps only when already available; do not run them for this report.>

## Current Disposition
<Net current state and changes, distinguishing task-owned and pre-existing work.
Use not-established for an unconfirmed defect.>

## Verification
<Checks actually run and their results; material unrun or blocked checks.>

## Next Action
<Concrete next step and existing tracking owner or none.
State any unresolved decision or permission that blocks that step.>
```

Use the state definitions in `SKILL.md` when relevant. Finding confirmation is
independent of reproduction; a static finding can be confirmed without a runtime
reproduction. Do not add a second execution-state field alongside reproduction
state. A reverted fix is reported by its net current disposition.

Optional details:

- Discovery or reproduction: relevant versions, minimal preconditions, existing
  owning-workflow fixture reference, executed steps/results, or blocking reason.
- Cause or recovery: confirmed boundary, hypotheses, mitigation/reversal history,
  migration and compatibility limits.
- Authorization: repair, persistence, tracking create/update, or external
  transmission only when relevant to the requested next action. Reuse applicable
  authorization; drafting alone does not authorize those actions.
- Transmission: concrete destination, audience, reviewed payload, allowed
  attachments, and redaction scope when a send action is authorized.

No fixture, tracker, saved report, attachment, or new investigation is required
to fill this template. Unknown scope stays unassessed rather than unaffected.
