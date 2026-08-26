# Maintainer Feedback Report Template

Render the report in the user's requested or source language. Translate headings when useful, but preserve the field meanings and state values below. Remove instructional text from the delivered report.

```markdown
# Wiki Maintenance Feedback: <concise title>

## Summary
- Report object: package root | initialized vault | external integration
- Existing finding owner / identifier / severity: <original value or none>
- Finding confirmation: confirmed | unconfirmed
- Disposition snapshot: not-established | fixed-in-worktree | fixed-in-commit | mitigated | unresolved
- Reproduction state: reproduced | observed-only | blocked
- Root-cause confidence: confirmed | probable | unknown
- Continuing tracking record: existing issue | knowledge question | user-specified tracker | none
- Implementation evidence: diff | commit | pull request | none
- Verification evidence: tests | deterministic check | inspection | none

## Discovery Context
- Original task and triggering operation:
- Report-object version or commit, when known:
- Relevant tool/runtime versions:
- Existing owning-workflow fixture: <sanitized reference or none>
- Discovery boundary:

Do not copy the full conversation.

## Expected And Actual
- Observable contract:
- Minimal input or precondition:
- Expected result:
- Actual result:

## Impact
- Confirmed:
- Potential:
- Unassessed:

## Reproduction Or Blocking Evidence
- Execution state: executed | not-executed | blocked
- Evidence-producing owner / authorization, when applicable:
- Executed steps and results:
- Unexecuted steps:
- Blocking reason:
- Nearest verifiable observation:

For executed evidence, include sanitized prerequisites, commands, output summaries, and exit state. Execution state records whether an attempt ran: `executed` maps to `reproduced` only when the target failure was observed and otherwise maps to `observed-only`; `not-executed` (including no attempt) maps to `observed-only`; an attempt stopped by a missing prerequisite maps to `blocked`. Reproduction state does not by itself establish or negate finding confirmation; an independently confirmed finding must name that basis, and an unconfirmed finding remains unconfirmed.

## Evidence And Cause
- Confirmed facts:
- Hypotheses:
- Earliest confirmed owning boundary:

## Disposition
- Net current state:
- Changes made in this task:
- Pre-existing changes:
- Mitigation or reversal history:
- Intentionally unchanged scope:

## Verification
- Before-change reproduction:
- After-change result:
- Focused checks:
- Broader checks:
- Unrun checks:

## Authorization Ledger
- Repair authorization:
- Persistence authorization:
- Tracking create/update authorization:
- External-transmission authorization (destination, audience, reviewed payload, attachments):

## Next Action And Owner
- Continuing owner or none:
- First executable next action:

## Redaction And Attachment Scope
- Removed or replaced sensitive categories:
- Allowed attachments:
- Reviewed payload identifier or description:
```

Add migration, recovery, rollback, compatibility, data-scan, external-dependency, attachment, or release-line sections only when relevant. A scope that was not verified is `unassessed`, not unaffected.
