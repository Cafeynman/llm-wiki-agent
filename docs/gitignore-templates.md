# Git Ignore Templates

The repository default protects local workspace data. Refer to the versioned
wiki template only when this checkout is the user's own wiki project and the
user intends to commit wiki content.

In both templates, keep `.env`, `.venv/`, caches, and local tool state such as
`.claude/`, `.claudian/`, and `.codex/` ignored. Only replace the
`# Local wiki runtime content.` block in `.gitignore`.
Init and upgrade scripts seed the default `.gitignore` when it is missing. When
an existing `.gitignore` has no wiki runtime policy, they append the default
private runtime block without overwriting the rest of the file.

## Private Local Runtime

This is the package default. It keeps source files, extracted material, wiki
pages, questions, logs, reviews, and artifacts local.

```gitignore
# Local wiki runtime content.
/inbox/*
!/inbox/.gitkeep
/raw/
/intake/
/reviews/
/logs/
/questions/
/artifacts/
/wiki/
```

## Versioned Wiki Project

Use this when the repository is a personal or team wiki project and durable
wiki content should be tracked. This template still keeps the transient inbox,
preserved original files, and temporary extraction output local by default.

```gitignore
# Local source intake and temporary extraction state.
/inbox/*
!/inbox/.gitkeep
/raw/
/intake/tmp/
```

This version tracks `intake/processed/`, `intake/logs/`, `reviews/`, `logs/`,
`questions/`, `artifacts/`, and `wiki/`. If original source files under `raw/`
also need to be versioned, remove `/raw/` only after reviewing privacy, size,
copyright, and licensing constraints. Init and upgrade scripts still recognize
the versioned wiki policy when `/raw/` is intentionally removed. They also
recognize `/intake/` in place of `/intake/tmp/` when all intake output should
remain local.
