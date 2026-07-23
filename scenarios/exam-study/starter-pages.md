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

Default path:

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

# Wrong-Question Topic Index

## Topics

Keep this table as a thin current-state index. Store the included questions,
objective explanations, knowledge-point connections, and any dated review notes
in the linked topic page.

Adjust the columns to the project's actual review needs.

| Topic | Knowledge Focus | Questions | Review State | Next Action |
| --- | --- | --- | --- | --- |
```

## Wrong-Question Topic Page

Default path:

```text
wiki/syntheses/<subject>/wrong-questions/<NNN>-<knowledge-topic>.md
```

`<NNN>` is a three-digit subject-local sequence such as `001`. Do not reuse or
renumber it. The description names the central knowledge topic, not one source
question.

Localize the visible headings to the language and preferred terms confirmed in
the root `PROJECT.md`.

This is a loose framework. It has only two required visible headings: `错题材料`
and `知识点`. Keep only the optional sections that help the current topic, and
merge, rename, or extend them when the material calls for a different shape. A
useful topic page must preserve understandable wrong-question material and
explain the knowledge needed for similar questions.

Skeleton:

```markdown
---
type: synthesis
status: draft
confidence: low
sources: []
---

# <NNN> - <知识主题>

## 错题材料

### <题目标签>

**题目**

<题目内容。选择题、简答题、案例题和开放题均可。>

**解析**

<客观说明正确判断、关键条件、边界、例外和易混点。>

**答案 / 参考作答**

<选择题写最终答案；开放题写参考作答、作答要点或评分逻辑。>

## 知识点

<围绕本专题，较完整说明解决同类题所需的规则、条件、边界、例外、
比较关系和判断方法。内容以能做同类题为止，不扩写成整章教材。>
```

Use a `### <题目标签>` block only when the page has multiple questions or a
label helps navigation. Keep the material order as `题目` -> `解析` -> `答案 /
参考作答`. Do not add a default `我的作答` or `错误原因` field. If the user
explicitly reports a personal error reason or repeat-review result, put it in a
dated optional `复习备注` entry instead of inferring it from the answer.

Optional additions include `关联知识`, `复习备注`, source basis, boundary or
comparison tables, reusable decision paths, memory summaries, and open
questions. Add them only when they help. Related knowledge should explain its
relationship rather than becoming a bare link list. A memory summary is an
accurate compressed review note, not a rhyme, slogan, or mnemonic; omit it
unless it preserves the conditions, exceptions, and accuracy that matter.

For a choice question, keep an option-by-option table inside `答案 / 参考作答`
only when it makes the distinctions clearer:

```markdown
**答案 / 参考作答**

C。

| 选项 | 判断 | 说明 |
| --- | --- | --- |
| A | 不正确 | <原因> |
| B | 不正确 | <原因> |
| C | 正确 | <原因> |
| D | 不正确 | <原因> |
```

For dated user-provided review information, use:

```markdown
## 复习备注

- YYYY-MM-DD｜<题目标签>：<用户明确提供的错误原因、复做结果或下一步。>
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
page when they become accepted question samples, completed topic material,
rejected items, or stage review notes.

## Missing Answers

Items here must not enter formal question samples. A wrong-question topic may
preserve the available material as `待补充`, but it must not invent the missing
answer or use unresolved content as settled knowledge.

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

## Wrong-Question Topic Signals

| Topic ID | Subject | Knowledge Topic | Signal | Linked Topic | Next Action |
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
