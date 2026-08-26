# Exam Study Scenario

This optional scenario initializes one workspace for one professional
qualification exam or a similar subject-based study project. Merely having this
directory does not activate the scenario.

## Initialization Flow

When the user explicitly asks to initialize or adapt the workspace from this
scenario:

1. Read this file and `PROJECT.template.md`.
2. Confirm only the project fields that materially affect the requested starter
   pages, beginning with the subject names. Leave unrelated fields blank until
   a task needs them.
3. Write `Active scenario: exam-study` and the other confirmed project-specific
   values into the root `PROJECT.md`.
4. Preserve existing source-extraction preferences unless the user explicitly
   confirms a change.
5. Read `starter-pages.md` and create only the smallest useful set for the
   confirmed subjects and current scope. Merge useful missing sections into an
   existing page instead of overwriting study records.
6. Leave `WIKI.md` and `AGENTS.md` unchanged. Do not copy the scenario skill to
   `.agents/skills/`.

Initialization does not run the daily exam-study workflow. In later
conversations, `AGENTS.md` routes a relevant request to
`skills/exam-study/SKILL.md` only while the root `PROJECT.md` keeps this scenario
active.

## Typical Prompt

```text
Initialize this workspace according to scenarios/exam-study/.
Read the scenario README first. Ask only for PROJECT.md fields needed by the
requested starter pages, then create the smallest useful set.
```
