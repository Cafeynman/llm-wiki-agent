# Exam Study Scenario

Use this scenario when one workspace is dedicated to one professional
qualification exam or similar subject-based exam preparation effort.

## Core Assumptions

- One workspace targets one exam. Do not add a multi-exam `exam_name` routing
  field.
- Subjects are the primary organization dimension.
- Foundational material comes first: syllabus, textbooks, official guidance, or
  other authoritative sources should be digested before formal question-bank
  classification.
- Question banks are source material and exam-point samples. They are not
  textbook authority by themselves.
- Wrong questions are personal learning records. They are not the question-bank
  source itself.
- Study planning is a planning and execution loop. It guides the pace of study,
  records progress, reviews deviations, and adjusts the next plan from actual
  learning evidence.

## Initialization Flow

When the user asks to initialize this scenario:

1. Read this file completely.
2. Read `PROJECT.template.md`.
3. Ask the user to confirm the subjects, naming preferences, classification
   level, and any open constraints that are still blank.
4. Update the root `PROJECT.md` with confirmed values only.
5. Preserve the root `PROJECT.md` source extraction preferences unless the user
   explicitly confirms a scenario-specific change.
6. Read `starter-pages.md`.
7. Create only the starter pages that are useful for the confirmed subjects and
   current scope. If a starter page already exists, merge useful missing
   sections instead of overwriting existing study records.
8. Do not change `WIKI.md` or `AGENTS.md`.

## Source and Learning Boundaries

Keep source handling aligned with the normal wiki lifecycle.

- Textbooks, syllabus documents, official guidance, and question banks enter
  through `inbox/` and follow the Add Knowledge workflow.
- Source cards under `wiki/sources/` preserve source-relative traceability.
  Subject grouping must not rewrite source-card paths.
- Durable concept knowledge may belong under `wiki/concepts/`, but do not create
  a concept page by default. Create one only when the knowledge is reused across
  multiple topics or needs independent maintenance.
- Subject-level question sample indexes and wrong-question topic indexes belong
  under `wiki/syntheses/` when they are canonical learning state.
- Keep question sample indexes thin. Each row should contain only identifiers,
  short classification fields, acceptance state, and a link to the
  single-question sample record page.
- Keep wrong-question topic indexes thin. Each row should contain only the topic
  identifier, knowledge-topic label, question count, current review state, next
  action, and a link to the topic page.
- Complete formal question-sample text, answers, explanation, classification
  evidence, and linked concepts belong in single-question sample record pages,
  not in the question sample index.
- Wrong-question topic pages collect one or more wrong questions around a useful
  knowledge topic. A topic may begin with one question and grow when additional
  questions make later review clearer. Each page preserves the available question
  material and a reusable explanation of the relevant knowledge points.
- Generated practice sets, mock exams, and stage reviews belong under
  `artifacts/`.
- Missing-answer items must not enter formal question samples. They may remain
  in a wrong-question topic page as material marked `待补充`; do not invent an
  answer, present an uncertain explanation as settled, or use the unresolved
  item as evidence for a knowledge-point conclusion. Track a separately useful
  unresolved item in `questions/` and close that queue entry when it is resolved
  or rejected.

## Wrong-Question Topic Layout and Naming

Unless the root `PROJECT.md` records an explicitly confirmed alternative, use
this subject-level layout:

```text
wiki/syntheses/<subject>/wrong-question-index.md
wiki/syntheses/<subject>/wrong-questions/<NNN>-<knowledge-topic>.md
```

Use the confirmed canonical subject directory name for `<subject>`. Subject
aliases must point to that canonical subject instead of creating parallel
directories.

Apply these naming and grouping rules:

1. Treat one wrong-question topic page as one useful knowledge topic. It may
   contain one or more wrong questions.
2. Use a stable three-digit subject-local sequence for `<NNN>`, starting at
   `001`. Do not renumber existing pages.
3. Write `<knowledge-topic>` as a concise, human-readable description of the
   central knowledge theme. Follow the root `PROJECT.md` naming preferences and
   the cross-source naming rules in `WIKI.md`.
4. Do not put one source question number in the topic filename. Identify
   questions inside the page with their source locator or another clear local
   label appropriate to the material.
5. Combine or split questions when doing so makes future review clearer. A
   shared subject or chapter alone does not require either choice, and different
   error reasons do not by themselves require separate topics.

The topic page is the maintained record. The subject
`wrong-question-index.md` and `study-dashboard.md` are thin current-state
projections. Update the topic page first, then update those projections only
when their displayed state changes.

Each topic page has two required headings: `错题材料` and `知识点`. The former
preserves enough question context for review; the latter explains the knowledge
needed to solve similar questions. All other headings are optional and may be
added, merged, renamed, or omitted according to the question type, available
evidence, and current study need.

Within each question, use the default review order `题目` -> `解析` ->
`答案 / 参考作答`. Keep `解析` objective: explain the correct judgment, relevant
conditions, boundaries, and common traps. Do not create a default `我的作答` or
`错误原因` field, and never infer a personal error reason from an answer. When a
user explicitly provides their error reason or a later review result, record it
only in a dated optional `复习备注` entry.

Option analysis, source basis, boundary tables, decision paths, memory summaries,
related pages, open questions, and review logs are optional. Use them only when
they improve understanding or future review. An option-by-option table belongs
inside `答案 / 参考作答` when it helps distinguish choices; it is not a required
section. When a related link is important, briefly explain the relationship
instead of leaving a bare link list.

When used, a memory summary is a concise and accurate review note. Preserve the
conditions and exceptions that matter. Do not turn it into a rhyme, slogan, or
mnemonic unless the user explicitly asks for that form.

## Formal Question Acceptance

Use a question-specific field such as `question_acceptance`, not the page-level
`status` field from `WIKI.md`. These values govern formal question samples; they
do not prohibit preserving incomplete material in a wrong-question topic page.

Recommended values:

| Value | Meaning |
| --- | --- |
| `accepted` | The question has enough information to be used as a formal sample. |
| `needs_enrichment` | Classification, chapter, or knowledge-point data can likely be filled from already digested foundational material. |
| `enriched_pending_confirmation` | The agent filled missing classification data and the result should be checked. |
| `needs_answer` | The answer is missing, so the item is barred from formal acceptance. |
| `pending_decision` | The issue needs user judgment and is not merely a missing answer. |
| `rejected` | The item is not suitable for this exam-study workspace. |

When classification is missing but foundational material exists, enrich the
question automatically and record the evidence and confidence. When the answer
is missing, keep it out of formal samples instead of guessing; a topic page may
still preserve the incomplete material as `待补充`.

If the answer exists but the explanation is missing, the item may be accepted
only when the question text, source, correct answer, and needed context are
present. Any agent-written explanation must be marked as derived reasoning or
pending source confirmation, not as an official explanation.

## Study Planning Loop

The study plan loop coordinates preparation over time. It does not replace the
source lifecycle or become hidden monitoring.

- `study-plan.md` records the overall exam preparation plan: exam date, phases,
  subject priorities, weekly rhythm, milestones, and review cadence.
- `study-dashboard.md` records current execution state: this week's active
  tasks, current weak knowledge points, and next actions. It is the first page
  to inspect when the user asks to restart or resume review. Do not let it
  become a long-term history page.
- Weak knowledge points must be evidence-backed. Use user-reported gaps,
  accepted wrong questions in topic pages, reviewed sources, question sample
  indexes, and stage reviews as evidence; do not invent weakness records from
  general impressions.
- When a wrong question is added or reviewed, identify or create its primary
  wrong-question topic page and add or update the question material there first.
  Update its knowledge points only as far as the available material and reviewed
  sources support them. Then update the subject `wrong-question-index.md` with a
  thin topic row and update the dashboard only when the current weak-knowledge
  or next-action state changes. Create or update a concept page only when the
  knowledge is useful across multiple topics; concept pages should not list
  complete question history.
- A later attempt or review of the same source question updates its existing
  entry. When the user reports a personal error reason or review result, append
  it to that topic's dated `复习备注`; do not create a duplicate entry or a new
  topic page merely because the answer was wrong again.
- Stage review artifacts summarize a period of work and propose plan
  adjustments. They belong under `artifacts/`.
- Stage review outputs must write their current-state conclusions back to
  `study-dashboard.md` and their schedule or priority changes back to
  `study-plan.md`.
- The agent updates the dashboard and plan from user-reported progress, reviewed
  sources, wrong-question topic pages, question sample indexes, and stage
  reviews. Completed work, delayed work, and resolved review history belong in
  dated stage review artifacts, not as permanent dashboard entries.
- If the user wants timed reminders, use an explicit automation outside the
  scenario package. Do not create reminders during scenario initialization.

## Typical Prompt

```text
Initialize this workspace according to scenarios/exam-study/.
Read the scenario README first. Then use PROJECT.template.md to ask me for the
missing project fields and use starter-pages.md to create the smallest useful
starter pages.
```
