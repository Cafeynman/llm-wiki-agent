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
- Durable concept knowledge belongs under `wiki/concepts/`.
- Subject-level question sample indexes and wrong-question indexes may belong
  under `wiki/syntheses/` when they are canonical learning state. Keep these
  indexes thin: each row should contain only identifiers, short classification
  fields, current review state, next action, and a link to the single-question
  record page.
- Complete question text, answers, explanation, classification evidence, error
  analysis, review notes, and linked concepts belong in single-question record
  pages, not in the index.
- Generated practice sets, mock exams, and stage reviews belong under
  `artifacts/`.
- Missing-answer items must not enter formal question samples or wrong-question
  records. Put unresolved items in `questions/` as the current pending queue or
  reject them from formal acceptance. Move resolved items out of the queue in
  the same pass that accepts or rejects them.

## Question Acceptance

Use a question-specific field such as `question_acceptance`, not the page-level
`status` field from `WIKI.md`.

Recommended values:

| Value | Meaning |
| --- | --- |
| `accepted` | The question has enough information to be used as a formal sample or wrong-question record. |
| `needs_enrichment` | Classification, chapter, or knowledge-point data can likely be filled from already digested foundational material. |
| `enriched_pending_confirmation` | The agent filled missing classification data and the result should be checked. |
| `needs_answer` | The answer is missing, so the item is barred from formal acceptance. |
| `pending_decision` | The issue needs user judgment and is not merely a missing answer. |
| `rejected` | The item is not suitable for this exam-study workspace. |

When classification is missing but foundational material exists, enrich the
question automatically and record the evidence and confidence. When the answer
is missing, isolate or reject the item instead of guessing.

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
  accepted wrong-question records, reviewed sources, question sample indexes,
  and stage reviews as evidence; do not invent weakness records from general
  impressions.
- When a wrong-question record is accepted, create or update the
  single-question record page first. Then update the subject
  `wrong-question-index.md` with a thin row, update the linked concept page only
  with stable error patterns, common traps, or judgment steps, and update the
  dashboard only when the current weak-knowledge or next-action state changes.
  Concept pages should not list complete question history.
- Stage review artifacts summarize a period of work and propose plan
  adjustments. They belong under `artifacts/`.
- Stage review outputs must write their current-state conclusions back to
  `study-dashboard.md` and their schedule or priority changes back to
  `study-plan.md`.
- The agent updates the dashboard and plan from user-reported progress, reviewed
  sources, wrong-question records, question sample indexes, and stage reviews.
  Completed work, delayed work, and resolved review history belong in dated
  stage review artifacts, not as permanent dashboard entries.
- If the user wants timed reminders, use an explicit automation outside the
  scenario package. Do not create reminders during scenario initialization.

## Typical Prompt

```text
Initialize this workspace according to scenarios/exam-study/.
Read the scenario README first. Then use PROJECT.template.md to ask me for the
missing project fields and use starter-pages.md to create the smallest useful
starter pages.
```
