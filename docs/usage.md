<h1 align="center"><b>📖 Usage Guide</b></h1>

<p align="center">
  <b><i><font size="4">How to install, initialize, and operate LLM Wiki Agent.</font></i></b>
</p>

<p align="center">
  <a href="usage.zh-CN.md">🇨🇳 中文</a> ·
  <a href="usage.md">🇬🇧 English</a>
</p>

<p align="center">
  <a href="../README.md">🏠 Back to Home</a> · <a href="../AGENTS.md">🤖 Agent Rules</a> · <a href="../WIKI.md">🧠 Wiki Rules</a> · <a href="../PROJECT.md">⚙️ Project Context</a>
</p>

---

> **Note:** [AGENTS.md](../AGENTS.md) is the agent entrypoint. [PROJECT.md](../PROJECT.md) holds your workspace's specific configuration. [WIKI.md](../WIKI.md) is the core operating guide. Keep `WIKI.md` stable, and edit `PROJECT.md` for day-to-day personalization.

## 🎯 1. Use Cases

**LLM Wiki Agent is perfect for:**
- Research notes, articles, papers, and clipped web pages.
- Project knowledge, decisions, meeting notes, and technical investigations.
- Personal knowledge bases, reading notes, and topic archives.
- Source-backed questions where traceability, claims, uncertainty, and contradictions matter.

It is **not** meant for one-off chatting. Its true value lies in durable accumulation: preserving sources, judgments, and contradictions as reusable wiki knowledge.

---

## ⚙️ 2. Requirements

Before you start, ensure you have:
- [uv](https://docs.astral.sh/uv/) for Python environment management (the init scripts run `uv sync`).
- PowerShell (Windows) or Bash (macOS/Linux) for initialization scripts.
- Node.js/npm or an installed Defuddle CLI when you want the default webpage extraction provider.
- Obsidian, or any standard Markdown editor.
- An AI Agent that reads repository instructions (e.g., Codex, Claude Code, Gemini CLI, OpenCode).

---

## 🚀 3. Install & Initialize

```bash
cd llm-wiki-agent

# Windows
.\scripts\init.ps1 -VaultRoot .

# macOS / Linux
./scripts/init.sh -VaultRoot .
```

To create the structure inside an existing separate Obsidian vault:
```bash
# Windows
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"

# macOS / Linux
./scripts/init.sh -VaultRoot "/path/to/your/vault"
```

After external-vault initialization, open or run the agent from the initialized vault root. The target vault receives the package-managed entrypoint files, local skills, scripts, docs, runtime directories, and project environment. Existing package-managed files in the target vault are replaced by the package copy; keep vault-specific preferences in `PROJECT.md`.

**What this does:**
1. Installs package-managed entrypoint files, local skills, scripts, and docs into the target root.
2. Creates `PROJECT.md` when it is missing and leaves source extraction preferences there for the agent to confirm when they matter, including whether to configure MinerU, which MinerU profile to use for API mode, and whether to prefer MinerU when it is available.
3. Creates missing workflow directories and default wiki files (`inbox/`, `raw/`, `intake/`, `reviews/`, `logs/`, `wiki/`, etc.) without overwriting existing runtime content.
4. Runs `uv sync` in the initialized root to create or update the `.venv/` runtime state.

### Optional Scenario Packages

Scenario packages under `scenarios/` provide optional initialization guidance for specialized workspaces. They do not activate during base initialization. After the normal init script finishes, ask the agent to apply a scenario explicitly, for example:

```text
Initialize this workspace according to scenarios/exam-study/.
Read the scenario README first, ask me for any missing PROJECT.md fields,
then use starter-pages.md to create the smallest useful starter pages.
```

Scenario initialization should update `PROJECT.md` only with confirmed project-specific values, create only the smallest useful starter pages, and leave `WIKI.md` and `AGENTS.md` unchanged.

### Upgrade Package Files

Use the upgrade scripts when applying a newer package release to an existing workspace:

```bash
# Windows
.\scripts\upgrade.ps1 -TargetRoot "C:\path\to\your\workspace"

# macOS / Linux
./scripts/upgrade.sh -TargetRoot "/path/to/your/workspace"
```

The upgrade covers entries listed in `scripts/upgrade-manifest.txt`, creates `PROJECT.md` when it is missing, reconciles missing runtime directories and default wiki files, and runs `uv sync` in the target root. Listed files are overwritten. Listed directories, including `scenarios/`, are merged by overwriting package-managed files while leaving additional target entries in place. Keep workspace-specific configuration in `PROJECT.md`.

### Local Service Secrets

When a provider needs local credentials or deployment-specific endpoints, copy `.env.example` to `.env` in the initialized root and fill only the variables required by the selected provider profile.

After configuring a provider profile that needs a smoke check, run that check before the first extraction. The profile defines what the check verifies and what local variables are required.

During the first project-context confirmation, or when source-extraction preferences are still unconfirmed, the agent asks whether you want to configure MinerU, which MinerU profile to use for API mode, and whether MinerU should be preferred for supported documents when it is available. If you choose the MinerU preference, the agent records MinerU as the document default in `PROJECT.md`. If you decline, MarkItDown remains the ordinary document default and MinerU stays available for explicitly chosen or complex document extraction.

The real `.env` file is local runtime configuration. It is ignored by Git and must not be written into `PROJECT.md`, `WIKI.md`, manifests, logs, review notes, wiki pages, source cards, or prompts. Agent commands that depend on `.env` must run from the project root with `uv run --env-file .env ...`, or with `UV_ENV_FILE=.env` set in the current shell for repeated `uv run` commands.

Initialization and upgrade scripts install the non-secret `.env.example` template. They do not create or overwrite your real `.env`.

---

## 📂 4. Directory Structure

| Directory | Responsibility |
| --- | --- |
| `inbox/` | 📥 Only entrypoint for user-submitted original files. |
| `raw/` | 🗄️ Final state area for original files, preserving their source-relative paths. (Does not store agent-generated Markdown). |
| `intake/tmp/` | ⚙️ Temporary Markdown after extraction and before source review. |
| `intake/processed/` | ✅ Accepted Markdown ready for wiki ingestion. |
| `reviews/` | 📝 Source review and discussion reflection records. |
| `logs/` | ⏱️ High-level wiki operation history (`logs/wiki.md`). |
| `wiki/` | 🧠 Durable knowledge pages. |
| `questions/` | ❓ Open questions and investigation trails. |
| `artifacts/` | 📦 Reports, briefs, drafts, templates, and user-facing deliverables. |

---

## 📥 5. First File Intake Workflow

For exact lifecycle rules, follow [WIKI.md](../WIKI.md). A first small intake normally looks like this:

1. **Drop File:** Put an original file into `inbox/` (e.g., `inbox/example.md`).
2. **Prompt Agent:** Ask the agent: *"Process the files in inbox/ according to AGENTS.md, PROJECT.md, and WIKI.md."*
3. **Expected Result:**
    - For this example, temporary Markdown appears at `intake/tmp/example/source.md`. Nested input paths preserve their source-relative parents.
    - The **Source Review Gate** determines the final source state.
    - The original file moves to a `raw/` state subfolder while preserving its path below `inbox/`.
    - Only `digested` content moves to `intake/processed/` and updates `wiki/`.

For a batch walkthrough with intermediate and final directory states, see [Source Lifecycle Example](source-lifecycle.md).

Plain English requests are valid. You can ask for tasks such as:

- *"Process raw files"*
- *"Review sources"*
- *"Ingest this source"*
- *"What does the wiki say about this topic?"*
- *"Create an artifact"*
- *"Health-check the wiki"*

---

## 🔍 6. Source Review Gate Outcomes

This is a quick reference. The authoritative Source Review Gate rules live in [WIKI.md](../WIKI.md).

| Outcome | Destination | Next Action |
| --- | --- | --- |
| **`digested`** | `raw/digested/<source-relative-path>` | Promote to `intake/processed/`, create source card, update wiki. |
| **`needs-review`**| `raw/needs-review/<source-relative-path>`| Record review question. (e.g., requires human judgment or image processing). Do not update wiki yet. |
| **`ignored`** | `raw/ignored/<source-relative-path>` | Record reason. Do not update wiki. |
| **`unsupported`** | `raw/unsupported/<source-relative-path>` | Record blocker. Do not update wiki. |

> [!WARNING]
> A successful extraction does **not** mean automatic acceptance. Empty, substantially garbled, structurally broken, or highly image-dependent files become `needs-review`. If roughly half or more of the main body is unreadable, it must not be treated as good-quality input.

---

## 📜 7. Text-First Boundary

LLM Wiki Agent is designed around a text-first intake path:
- All readable documents (HTML, PDF, Word, PPT, Excel, etc.) become Markdown before ingestion.
- Scans, images, audio, and video stay as original sources in `raw/` but are **not** first-class wiki content unless extraction is explicitly configured and approved.
- Keep images out of wiki pages unless image handling is explicitly configured.

---

## 🧠 8. Use Existing Knowledge

To use the knowledge base, just ask your agent:
*"What does the wiki say about <topic>?"*

The agent will search:
1. `wiki/index.md` & `wiki/overview.md`
2. `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/claims/`, `wiki/syntheses/`
3. `questions/` and `artifacts/`

Generated deliverables such as reports, templates, and drafts belong in the `artifacts/` directory.

---

## 🪞 9. Reflect Discussion Knowledge

You can ask the agent to "Reflect" on durable discussion knowledge, such as:
- Confirmed user preferences
- Architecture judgments
- Reusable conclusions

These are written to `reviews/reflection/YYYY-MM-DD.md`.

---

## 🧹 10. Maintain the Wiki

Run periodic maintenance by asking:
- *"Health-check the wiki"*
- *"Find broken links"*
- *"Clean up duplicates"*
- *"Check claims without sources"*

---

## ❓ 11. FAQ

<details>
<summary><b>What if `uv` is missing?</b></summary>
Run the initialization script first. If it fails, install <code>uv</code> manually and rerun the init script.
</details>

<details>
<summary><b>What if Defuddle is missing?</b></summary>
The default webpage provider is Defuddle. Install it with npm or ask the agent to follow <code>.agents/skills/source-extraction/references/providers/defuddle/setup.md</code>.
</details>

<details>
<summary><b>What if a file is already in <code>raw/</code>?</b></summary>
New user-submitted originals must enter through <code>inbox/</code>. Files already in <code>raw/&lt;state&gt;/</code> may be reprocessed from their current state directory because they have already entered the lifecycle. Reprocessing must preserve the path after <code>raw/&lt;state&gt;/</code>, and when a source moves to a new state, the old state entry must be removed.
</details>

<details>
<summary><b>Can extracted Markdown go straight into <code>wiki/</code>?</b></summary>
No. Extracted Markdown first goes to <code>intake/tmp/</code>, then the Source Review Gate. Only accepted material goes to <code>intake/processed/</code> and then into <code>wiki/</code>.
</details>

<details>
<summary><b>Should personal wiki content be committed to GitHub?</b></summary>
No. The default <code>.gitignore</code> ignores local runtime directories like <code>inbox/</code>, <code>raw/</code>, <code>intake/</code>, and <code>wiki/</code>.
</details>

---

## 💡 12. Recommended Habits

- Process sources in small batches and check one intake cycle before scaling up.
- For large files, ask the agent to inspect metadata or chunk indexes first.
- Preserve counterevidence and uncertainty for disputed claims.
- Run **Maintain Wiki** periodically.
- Put user-facing deliverables in `artifacts/` and durable knowledge in `wiki/`.
