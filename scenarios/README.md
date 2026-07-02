# Scenario Packages

Scenario packages are optional initialization guides for specialized wiki uses.
They do not activate by themselves. Use one only when the user explicitly asks
to initialize or adapt a workspace from a specific scenario.

## How to Use

After running the normal package initialization, ask the agent to apply a
scenario package, for example:

```text
Initialize this workspace according to scenarios/exam-study/.
Read the scenario README first, then ask me for any missing PROJECT.md fields.
```

The agent should then:

1. Read `scenarios/<name>/README.md`.
2. Use `PROJECT.template.md` only as a source for project-specific context.
3. Use `starter-pages.md` only to create the smallest useful initial pages.
4. Leave `WIKI.md` and `AGENTS.md` unchanged.
5. Preserve the core source lifecycle: `inbox/` -> `raw/` -> `intake/` -> `wiki/`.

## Scenario Directory Contract

Each scenario should start with these files:

```text
scenarios/<name>/
  README.md
  PROJECT.template.md
  starter-pages.md
```

`README.md` is the scenario entrypoint. It explains when to use the scenario,
what to confirm, and which extra structure, if any, is allowed.

`PROJECT.template.md` contains fields that can be copied or merged into the
workspace root `PROJECT.md`. It should contain project preferences, naming
rules, scope, and open questions, not reusable workflow rules.

`starter-pages.md` contains page and record skeletons that the agent may use
during scenario initialization. It is not a complete knowledge base.

If a scenario becomes complex, its own `README.md` may define additional files
or folders. Do not add extra structure speculatively.
