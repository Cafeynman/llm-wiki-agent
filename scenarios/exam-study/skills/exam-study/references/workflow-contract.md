# Exam Study Workflow Contract

Read this reference only after the active `exam-study` scenario skill routes an
exam-learning task here. It owns the detailed operational rules for formal
question samples, wrong-question topics, study planning, and structural audits.

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
- Before answering, classifying, explaining, generating, or recording a
  question, search the relevant subject pages and reviewed foundational sources
  already in the wiki. External search fills a stated local gap; it does not
  replace available local evidence.
- A question origin, wrong-question index, queue, dashboard, or catalog is not
  evidence for the knowledge explanation. Keep the material's provenance clear
  and cite the reviewed textbook, source card, intake output, or other evidence
  that supports the explanation. Do not create a circular source chain between
  a record and the index that lists it.

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

The literal canonical wrong-question topic basename is
`<NNN>-<knowledge-topic>.md` in every subject directory. The basename consists
of a three-digit subject-local sequence, one ASCII hyphen, and the topic. The
subject directory carries subject identity. A project may use a different form
only when the user explicitly confirms it in the root `PROJECT.md`.

If the requested subject is not confirmed in the root `PROJECT.md`, do not
invent a directory or reuse the nearest subject. Ask the user to confirm the
project-specific subject name and whether it belongs to the current exam. After
confirmation, update `PROJECT.md` first, then create only that subject's required
starter pages and directories.

Apply these naming and grouping rules:

1. Treat one wrong-question topic page as one useful knowledge topic. It may
   contain one or more wrong questions.
2. Use a stable three-digit subject-local sequence for `<NNN>`, starting at
   `001`. Before allocating an identifier, scan both filenames and the canonical
   subject index. Use the next unused identifier and stop for review if the
   existing records already contain a collision. Do not renumber existing pages
   merely to close a gap.
3. Write `<knowledge-topic>` as a concise, human-readable description of the
   central knowledge theme. Follow the root `PROJECT.md` naming preferences and
   the cross-source naming rules in `WIKI.md`.
4. Do not put one source question number in the topic filename. Identify
   questions inside the page with their source locator or another clear local
   label appropriate to the material.
5. Combine or split questions when doing so makes future review clearer. A
   shared subject or chapter alone does not require either choice, and different
   error reasons do not by themselves require separate topics.
6. For an approved migration from a legacy filename, resolve duplicate
   identifiers first, prepare an old-to-new path map, rename each canonical page
   once, and update all inbound wikilinks and subject-index rows in the same
   batch. Do not preserve the old name by copying the page or creating a second
   maintained record.

The topic page is the maintained record. The subject
`wrong-question-index.md` and `study-dashboard.md` are thin current-state
projections. Update the topic page first, then update those projections only
when their displayed state changes.

The subject `wrong-question-index.md` is the only detailed wrong-question
inventory for that subject. Do not mirror its rows under `questions/`, the
global `wiki/index.md`, a dashboard, or another catalog. Those surfaces may link
to the canonical index and contain only the state they independently own.

### Structural Audit

For legacy imports, collision review, or a naming migration, run the structural
audit before changing paths:

```powershell
uv run --no-project python scenarios/exam-study/skills/exam-study/scripts/audit_wrong_questions.py --vault . --subject "<subject>" --output artifacts/wrong-question-audit.json
```

The report lists each current path, naming status, parsed sequence and topic,
suggested target, index entries, and wrong-question-page inbound wikilinks. It separately reports
duplicate sequences, target collisions, a missing index file, missing or
duplicate index entries, and unresolved index links. Exit code `0` means the structure is clean, `1` means
the report contains findings, and `2` means the input could not be audited. The
command writes only the explicitly requested report file; it does not rename or
edit source pages or indexes. A normal single-entry update
still uses the local filename-and-index scan above; it does not require a batch
audit when no legacy or collision risk is present.

An existing confirmed subject with no wrong-question topic pages may omit the
`wrong-questions/` directory; the audit treats that as an empty collection and
does not create a placeholder. A missing subject directory remains an input
error.

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

Option analysis, source basis, boundary tables, decision paths, related pages,
open questions, and review logs are optional. Use them only when
they improve understanding or future review. An option-by-option table belongs
inside `答案 / 参考作答` when it helps distinguish choices; it is not a required
section. When a related link is important, briefly explain the relationship
instead of leaving a bare link list.

Use direct concepts, causal reasoning, conditions, exceptions, and distinctions
for explanations and review notes. Apply the confirmed explanation style from
`PROJECT.md` consistently across wrong-question pages, indexes, concepts,
syntheses, and artifacts.

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
- A stage review alone is read-only; return its conclusions and proposed changes.
  Save a stage review artifact when requested. When updating learning state is
  authorized, write current-state conclusions to `study-dashboard.md` and
  schedule or priority changes to `study-plan.md`, reusing prior authorization.
- The agent updates the dashboard and plan from user-reported progress, reviewed
  sources, wrong-question topic pages, question sample indexes, and stage
  reviews. Completed work, delayed work, and resolved review history belong in
  dated stage review artifacts, not as permanent dashboard entries.
- If the user wants timed reminders, use an explicit automation outside the
  scenario package. Do not create reminders during scenario initialization.
