# Exam Study Starter Pages

These are initialization shapes, not the daily workflow contract. Use only the
pages needed by the confirmed root `PROJECT.md`; omit unused pages and optional
sections. The active scenario skill owns later exam-study operations.

## Subject Concept Page

Suggested path: `wiki/concepts/<subject>/<knowledge-point>.md`

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

## Judgment Steps

## Open Questions
```

## Question Sample Index

Suggested path: `wiki/syntheses/<subject>/question-sample-index.md`

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# Question Sample Index

| ID | Record | Source | Knowledge Point | Question Type | Acceptance | Confidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
```

## Question Sample Record

Suggested path:
`wiki/syntheses/<subject>/question-samples/<question-id>.md`

```markdown
---
type: synthesis
status: draft
confidence: low
question_acceptance: needs_answer
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

Default path: `wiki/syntheses/<subject>/wrong-question-index.md`

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# Wrong-Question Topic Index

| Topic | Knowledge Focus | Questions | Review State | Next Action |
| --- | --- | --- | --- | --- |
```

## Wrong-Question Topic Page

Default path:
`wiki/syntheses/<subject>/wrong-questions/<NNN>-<knowledge-topic>.md`

Use the basename exactly as `<NNN>-<knowledge-topic>.md`: a three-digit local
sequence, one ASCII hyphen, and a concise topic. The parent directory carries the
confirmed subject identity. The two required visible headings are `错题材料` and
`知识点`; other sections are optional.

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# <NNN> - <知识主题>

## 错题材料

**题目**

<题目内容>

**解析**

<客观说明正确判断、关键条件、边界、例外和易混点。>

**答案 / 参考作答**

<最终答案、作答要点或评分逻辑。>

## 知识点

<说明解决同类题所需的规则、条件、边界、例外、比较关系和判断方法。>
```

## Pending Questions Page

Suggested path: `questions/<subject>/pending-questions.md`

```markdown
---
type: question
status: draft
confidence: low
sources: []
---

# Pending Questions

| ID | Source | Question Summary | Missing Field or Decision | Blocker | Next Action |
| --- | --- | --- | --- | --- | --- |
```

## Study Plan

Suggested path: `wiki/syntheses/study-plan.md`

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

## Open Constraints
```

## Study Dashboard

Suggested path: `wiki/syntheses/study-dashboard.md`

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# Study Dashboard

## Current Week

| Task | Subject | Source or Knowledge Point | Status | Notes |
| --- | --- | --- | --- | --- |

## Weak Knowledge Points

| Subject | Knowledge Point | Evidence | Priority | Next Review Action | Status |
| --- | --- | --- | --- | --- | --- |

## Next Actions
```

## Stage Review Artifact

Suggested path: `artifacts/<subject>/stage-review-YYYY-MM-DD.md`

```markdown
# Stage Review

## Focus

## Weak Knowledge Points

## Recent Error Patterns

## Review Questions

## Dashboard Updates

## Study Plan Updates

## Next Session
```
