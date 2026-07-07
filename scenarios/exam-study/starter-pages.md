# Exam Study Starter Pages

Use these skeletons only when they match the confirmed `PROJECT.md` context.
Create the smallest useful set of pages for the current initialization.

## Subject Concept Page

Suggested path:

```text
wiki/concepts/<subject>/<knowledge-point>.md
```

Skeleton:

```markdown
---
type: concept
status: draft
confidence: low
sources: []
---

# <Knowledge Point>

## Scope

## Core Understanding

## Exam Signals

## Common Traps

## Error Patterns

## Judgment Steps

## Related Question Indexes

## Open Questions
```

## Question Sample Index

Suggested path:

```text
wiki/syntheses/<subject>/question-sample-index.md
```

Skeleton:

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# Question Sample Index

## Acceptance Rules

- `accepted`: usable as a formal sample.
- `needs_enrichment`: classification can likely be enriched from digested foundational material.
- `enriched_pending_confirmation`: classification was enriched and should be checked.
- `needs_answer`: answer is missing and the item must stay out of accepted samples.
- `pending_decision`: needs user judgment.
- `rejected`: not suitable for this workspace.

Items with missing answers belong in the pending-questions page, not in the
accepted sample table.

## Accepted Samples

Keep this table as a thin index. Store full question text, answer, explanation,
classification evidence, and review notes in the linked record page.

| ID | Record | Source | Knowledge Point | Question Type | Acceptance | Confidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |

```

## Question Sample Record

Suggested path:

```text
wiki/syntheses/<subject>/question-samples/<question-id>.md
```

Skeleton:

```markdown
---
type: synthesis
status: draft
confidence: low
question_acceptance: accepted
sources: []
---

# <Question ID> - <Short Question Label>

## Question Text

## Source and Classification

## Correct Answer

## Explanation

## Classification Evidence

## Linked Concepts

## Review Notes
```

## Wrong-Question Index

Suggested path:

```text
wiki/syntheses/<subject>/wrong-question-index.md
```

Skeleton:

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# Wrong-Question Index

## Records

Keep this table as a thin index. Store the full question text, my answer,
correct answer, explanation, error cause, review notes, and linked concepts in
the linked record page.

| ID | Date | Record | Knowledge Point | Error Type | Review Status | Next Judgment Step |
| --- | --- | --- | --- | --- | --- | --- |
```

## Wrong-Question Record

Suggested path:

```text
wiki/syntheses/<subject>/wrong-questions/<wrong-question-id>.md
```

Skeleton:

```markdown
---
type: synthesis
status: draft
confidence: low
question_acceptance: accepted
sources: []
---

# <Wrong Question ID> - <Short Question Label>

## Question Text

## My Answer

## Correct Answer

## Explanation

## Error Cause

## Review Points

## Linked Concepts

## Next Judgment Step
```

## Pending Questions

Suggested path:

```text
questions/<subject>/pending-questions.md
```

Skeleton:

```markdown
---
type: question
status: draft
confidence: low
sources: []
---

# Pending Questions

Keep this page as the current unresolved queue. Move resolved items out of this
page when they become accepted records, rejected items, or stage review notes.

## Missing Answers

Items here must not enter formal question samples or wrong-question records.

| ID | Source | Question Summary | Missing Field | Blocker | Next Action |
| --- | --- | --- | --- | --- | --- |

## Pending Decisions

| ID | Source | Issue | Options | Needed Decision |
| --- | --- | --- | --- | --- |
```

## Study Plan

Suggested path:

```text
wiki/syntheses/study-plan.md
```

Skeleton:

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# Study Plan

## Exam Target

## Planning Assumptions

## Subject Priorities

| Subject | Priority | Reason | Current Confidence |
| --- | --- | --- | --- |

## Phases

| Phase | Date Range | Focus | Exit Criteria |
| --- | --- | --- | --- |

## Weekly Rhythm

| Day or Block | Planned Work | Review Hook |
| --- | --- | --- |

## Adjustment Rules

## Open Constraints
```

## Study Dashboard

Suggested path:

```text
wiki/syntheses/study-dashboard.md
```

Skeleton:

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# Study Dashboard

Use this as the first page when restarting or resuming review. Keep it limited
to the current week, current weak points, and next actions. Move completed work,
delayed work, and resolved history into dated stage review artifacts.

## Current Week

## Planned Tasks

| Task | Subject | Source or Knowledge Point | Status | Notes |
| --- | --- | --- | --- | --- |

## Weak Knowledge Points

| Subject | Knowledge Point | Evidence | Weak Reason | Priority | Next Review Action | Status |
| --- | --- | --- | --- | --- | --- | --- |

## Wrong-Question Signals

| ID | Subject | Knowledge Point | Signal | Linked Record | Next Action |
| --- | --- | --- | --- | --- | --- |

## Next Actions
```

## Stage Review Artifact

Suggested path:

```text
artifacts/<subject>/stage-review-YYYY-MM-DD.md
```

Skeleton:

```markdown
# Stage Review

## Focus

## Weak Knowledge Points

## Recent Error Patterns

## Review Questions

## Dashboard Updates

## Study Plan Adjustments

## Next Session
```
