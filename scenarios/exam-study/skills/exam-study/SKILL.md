---
name: exam-study
description: "Use only when the root PROJECT.md says `Active scenario: exam-study` and the current request concerns exam preparation, formal question samples, wrong-question topics, study planning, review, or the scenario's structural audit. Directory presence alone does not activate this skill; do not use it for scenario initialization."
---

# Exam Study

Use this skill for the daily learning workflow of an initialized exam-study
workspace. The root `PROJECT.md` must contain the exact active-scenario value
`exam-study`, and the current task must be relevant to that scenario. Otherwise
return to the workflow selected by `WIKI.md` without reading this skill's
reference.

## Core Workflow

1. Read the relevant confirmed subjects, naming preferences, and study context
   from `PROJECT.md`; ask rather than inventing a missing subject or other
   project-specific value that changes a path or classification.
2. Search the relevant local subject pages and reviewed sources before
   classifying, explaining, generating, or recording a question.
3. When the input is new source material, route it through the Add Knowledge
   workflow in `WIKI.md` and
   `.agents/skills/source-extraction/SKILL.md`. Do not bypass the Source Review
   Gate or treat a question bank as textbook authority.
4. Read `references/workflow-contract.md` when the task involves formal question
   acceptance, wrong-question topic pages or indexes, study planning or review,
   naming migration, collision review, or the structural audit.
5. Update the canonical record first, then only the thin index, dashboard, plan,
   question queue, or artifact whose independently owned state changed.
6. Verify the affected files and links in the smallest relevant scope. Run the
   structural audit only for a legacy import, collision review, or naming
   migration; ordinary single-question work uses the local filename-and-index
   scan defined in the reference.

## Boundaries

- Do not infer a subject, answer, personal error reason, weakness, or semantic
  classification that the user or evidence has not established.
- Do not create a parallel queue, inventory, dashboard, or question history.
  Use the canonical surfaces named in the workflow contract and `WIKI.md`.
- Do not modify `AGENTS.md` or `WIKI.md`. Update `PROJECT.md` only with explicitly
  confirmed project-specific values and only when the current task requires it.
- Do not treat unresolved question material as settled knowledge or as evidence
  for a knowledge-point conclusion.
- Do not rename or migrate pages from the audit report alone. Semantic
  correctness, formal eligibility, and a migration plan still require review.

## Structural Audit

From the active workspace root, run:

```powershell
uv run --no-project python scenarios/exam-study/skills/exam-study/scripts/audit_wrong_questions.py --vault . --subject "<subject>" --output artifacts/wrong-question-audit.json
```

The command reads the workspace and writes only the explicitly requested JSON
report. Exit code `0` means structurally clean, `1` means findings, and `2`
means the input could not be audited. Inspect the report before proposing any
write.

Validate this skill after package changes with:

```powershell
uv run --no-project python .agents/skills/skill-creator/scripts/quick_validate.py scenarios/exam-study/skills/exam-study
```
