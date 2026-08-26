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

> **Note:** [AGENTS.md](../AGENTS.md) is the agent entrypoint. [PROJECT.md](../PROJECT.md) holds your workspace's specific configuration. [WIKI.md](../WIKI.md) is the core operating guide. At the beginning of every conversation, the agent reads the active workspace's complete `WIKI.md` and `PROJECT.md` before planning, searching, answering, delegating, or writing. Programming and resumed conversations use the same start. Conversation history and earlier reads are not substitutes. Keep `WIKI.md` stable, and edit `PROJECT.md` for day-to-day personalization.

## 🎯 1. Use Cases

**LLM Wiki Agent is perfect for:**
- Research notes, articles, papers, and clipped web pages.
- Project knowledge, decisions, meeting notes, and technical investigations.
- Personal knowledge bases, reading notes, and topic archives.
- Source-backed questions where traceability, claims, uncertainty, and contradictions matter.

Its core value is durable accumulation: preserving sources, judgments, and contradictions as reusable wiki knowledge.

---

## ⚙️ 2. Requirements

Before you start, ensure you have:
- [uv](https://docs.astral.sh/uv/) for Python environment management. Install it before initialization; the scripts run `uv sync --locked` against the lockfile's official PyPI index but do not install machine-level tools.
- PowerShell (Windows) or Bash (macOS/Linux) for initialization scripts.
- Node.js/npm when you want the default webpage extraction provider. If Defuddle CLI is missing, the agent explains the pinned global npm installation, requests approval, then installs and verifies it automatically.
- Any standard Markdown editor. Obsidian is optional.
- An agent runtime that can read repository instructions, edit files, and run the required commands.

### Recommended Agent Runtime

The package does not depend on a specific agent platform. For the default setup, this guide recommends [OpenCode](https://opencode.ai/docs/). Install and configure OpenCode using its current documentation, then run it from the initialized working root. Other compatible agent runtimes remain supported.

```bash
opencode auth login
opencode
```

---

## 🚀 3. Install & Initialize

```bash
cd llm-wiki-agent

# Windows
.\scripts\init.ps1 -VaultRoot .

# macOS / Linux
./scripts/init.sh -VaultRoot .
```

To create the structure inside a separate working directory, including an existing Obsidian vault:
```bash
# Windows
.\scripts\init.ps1 -VaultRoot "C:\path\to\your\vault"

# macOS / Linux
./scripts/init.sh -VaultRoot "/path/to/your/vault"
```

After external-root initialization, open or run the agent from the initialized root. The target receives the package-owned entrypoint files, local skills, scripts, docs, runtime directories, and project environment. Initialization uses the same ownership reconciliation as upgrade. A newly claimed path is created when missing, adopted when byte-identical, and rejected when different; when both old metadata files are absent, the initial-adoption gate applies that rule to every candidate path. A marked complete inventory may stand alone as an interruption checkpoint; a lone manifest, an unmarked lone inventory, or invalid metadata stops before target writes. Keep workspace-specific preferences in `PROJECT.md`.

**What this does:**
1. Installs package-managed entrypoint files, local skills, scripts, and docs into the target root.
2. Creates `PROJECT.md` when it is missing and leaves source extraction preferences there for the source task that needs them.
3. Creates missing workflow directories and default wiki files (`inbox/`, `raw/`, `intake/`, `reviews/`, `logs/`, `wiki/`, etc.) without overwriting existing runtime content.
4. Seeds the default private `.gitignore` whenever the target has no
   `.gitignore`. An existing `.gitignore` keeps its target-owned domain policy
   and receives only missing secret and technical-cache rules.
5. Runs `uv sync --locked --default-index https://pypi.org/simple` in the initialized root to create or update the `.venv/` runtime state from the committed lockfile.

### Optional Obsidian and Claudian Interface

Obsidian and Claudian are not required. The package works through the filesystem with any compatible agent runtime. If you want an embedded agent interface inside Obsidian, follow the current installation instructions in the [YishenTu/claudian repository](https://github.com/YishenTu/claudian) or on the [Claudian website](https://claudian.xyz/zh/), then review the [provider documentation](https://claudian.xyz/zh/docs/providers/).

For this optional Claudian path, this package recommends OpenCode as the default provider choice. This is a package-level recommendation, not a claim that OpenCode is Claudian's only provider. Other providers supported by Claudian remain valid.

### Optional Scenario Packages

Scenario packages under `scenarios/` provide optional initialization guidance for specialized workspaces. They do not activate during base initialization. After the normal init script finishes, ask the agent to apply a scenario explicitly, for example:

```text
Initialize this workspace according to scenarios/exam-study/.
Read the scenario README first, ask only for PROJECT.md fields needed by the
requested starter pages, then create the smallest useful set.
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

The upgrade reads the target's old `scripts/upgrade-manifest.txt` and `scripts/package-files.txt`, then compares them with the same two files in the current package. The current manifest declares `inventory all`; the inventory declares `# inventory-format: complete` and uses `active <path>` and `remove <path>` records to activate every direct file, directory-expanded file, and retired path together with its ownership class. These two files are the only package ownership state; target Git history is not consulted. Older targets without the inventory marker remain readable in their directory-only format. After dependency synchronization, that legacy inventory is first replaced atomically by a complete snapshot of the same old ownership. A target with no old metadata receives a complete-inventory checkpoint that claims only the inventory control file just created by the upgrade. A later interruption therefore leaves a marked typed inventory containing the authoritative old paths and classes, whether the manifest is old, new, or temporarily absent. A path owned by both versions is created, left unchanged, or replaced with the current package copy. A newly claimed path is created or adopted when byte-identical, but a differing existing path is a conflict. A path dropped from active ownership must have an explicit `remove` entry before it can be removed. A new retirement may delete an existing file only when the old metadata already classified that path as active or retired; otherwise it conflicts and preserves the file. A lone manifest, an unmarked lone inventory, malformed, duplicate, or escaping metadata blocks the upgrade before target writes. Only when both old metadata files are absent does the legacy-adoption gate apply; existing differing package paths and existing retirement paths remain conflicts until ownership is resolved. The same preflight rejects links or reparse points in package sources, existing ancestors of the target root, the target root itself, or write paths, and rejects wrong file types at `PROJECT.md`, `.gitignore`, `.venv`, or fixed runtime paths. Other target files inside package directories remain in place, `PROJECT.md`, `.env`, and runtime knowledge content are preserved.

Run the upgrade once, review its create/replace/remove/unchanged summary and the resulting files, then run the relevant checks. If the target happens to use version control, its normal branch and review workflow remains optional operator evidence rather than package ownership state. The script itself does not create branches, commits, or merges. It reconciles missing runtime structure, preserves an existing `.gitignore` domain policy while adding missing secret and cache rules, and runs `uv sync --locked --default-index https://pypi.org/simple` before advancing ownership metadata. After synchronization, a legacy path-only inventory is atomically normalized without changing ownership, or a typed checkpoint owning only the newly created inventory control file is written when no old metadata exists. The new manifest is then committed first and the final typed inventory last, each through a same-directory temporary file. The final inventory activates direct files, directory files, and tombstones with their classes, so every metadata interruption window remains conservative and resumable. Use PowerShell on Windows; the Bash entrypoint supports macOS and Linux and rejects Windows runtimes.

### Local Service Secrets

When a provider needs local credentials or deployment-specific endpoints, copy `.env.example` to `.env` in the initialized root and fill only the variables required by the selected provider profile.

After configuring a provider profile that needs a smoke check, run that check before the first extraction. The profile defines what the check verifies and what local variables are required.

When a source task selects MinerU and a required choice is still unconfirmed, the agent asks only for that choice: the API profile, local credential setup, or whether MinerU should be preferred for supported documents. A confirmed preference is recorded in `PROJECT.md`; otherwise MarkItDown remains the ordinary document default and MinerU stays available for explicitly chosen or complex document extraction.

The real `.env` file is local runtime configuration. It is ignored by Git and must not be written into `PROJECT.md`, `WIKI.md`, manifests, logs, review notes, wiki pages, source cards, or prompts. Agent commands that depend on `.env` must run from the project root with `uv run --env-file .env ...`, or with `UV_ENV_FILE=.env` set in the current shell for repeated `uv run` commands.

Initialization and upgrade scripts install the non-secret `.env.example` template. They do not create or overwrite your real `.env`.

---

## 📂 4. Directory Structure

| Directory | Responsibility |
| --- | --- |
| `inbox/` | 📥 Entry point for submitted original files and generated live-URL source captures. |
| `raw/` | 🗄️ Final state area for lifecycle source artifacts, preserving their source-relative paths. Defuddle URL captures are the only generated source artifacts allowed here. |
| `intake/tmp/` | ⚙️ Temporary Markdown after extraction and before source review. |
| `intake/processed/` | ✅ Accepted Markdown ready for wiki ingestion. |
| `reviews/` | 📝 Source review and discussion reflection records. |
| `logs/` | ⏱️ High-level wiki operation history (`logs/wiki.md`). |
| `wiki/` | 🧠 Durable knowledge pages. |
| `questions/` | ❓ Open questions and investigation trails. |
| `artifacts/` | 📦 Reports, briefs, drafts, templates, and user-facing deliverables. |

---

## 📥 5. First Source Intake Workflow

For the core lifecycle, follow [WIKI.md](../WIKI.md); detailed intake mechanics live in `source-extraction/references/intake-lifecycle.md`. A first small intake normally looks like this:

1. **Submit Source:** Put original files into `inbox/`, or give the agent a live URL.
2. **Prompt Agent:** Ask the agent: *"Process these sources according to AGENTS.md, PROJECT.md, and WIKI.md."*
3. **Expected Result:**
    - A live URL is converted once by Defuddle into `inbox/web/<page-title>--<url-hash>.md`; that capture then follows the same lifecycle as a submitted Markdown file.
    - Temporary Markdown appears at `intake/tmp/<source-relative-parent>/<source-base-filename>/source.md`. Nested input paths preserve their source-relative parents.
    - The **Source Review Gate** determines the final source state.
    - The lifecycle source artifact moves to a `raw/` state subfolder while preserving its path below `inbox/`.
    - Only `digested` content moves to `intake/processed/` and updates `wiki/`.

For a batch walkthrough with intermediate and final directory states, see [Source Lifecycle Example](source-lifecycle.md).

Plain English requests are valid. You can ask for tasks such as:

- *"Process raw files"*
- *"Review sources"*
- *"Ingest this source"*
- *"Capture and ingest this URL"*
- *"What does the wiki say about this topic?"*
- *"Create an artifact"*
- *"Health-check the wiki"*

---

## 🔍 6. Source Review Gate Outcomes

This is a quick reference. The core outcomes live in [WIKI.md](../WIKI.md), and detailed quality and handling rules live in `source-extraction/references/intake-lifecycle.md`.

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
- Images already returned by a selected provider may be preserved automatically under the same intake folder as `source.md`; they are promoted or deleted with that folder.
- Keep images out of wiki pages, and do not OCR or interpret them, unless image handling is explicitly configured and approved.

---

## 🧠 8. Use Existing Knowledge

To use the knowledge base, just ask your agent:
*"What does the wiki say about <topic>?"*

The agent will first locate the relevant scope with `wiki/index.md`,
`wiki/overview.md`, search, headings, or linked indexes, then read only the
relevant pages or sections:
1. navigation entries in `wiki/index.md` and relevant synthesis sections in `wiki/overview.md`
2. relevant pages under `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/claims/`, `wiki/syntheses/`
3. related investigations and deliverables in `questions/` and `artifacts/`

This local scope is checked before external research. If it is insufficient, the
agent states the gap before expanding the search. Ordinary answers and
corrections are returned in the conversation without changing files. The agent
writes only when you explicitly ask or confirm; requested reports, templates,
and drafts belong in `artifacts/`.

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

If the agent confirms a material, reusable foundation defect outside your original request, it reports the finding, impact, disposition, and verification instead of handling it silently, whether the defect was fixed, mitigated, or left unresolved. Ask for *"maintainer-ready feedback"* when a brief disclosure is not enough for another maintainer or agent. The detailed report is response only by default; saving it, updating a tracker, or sending it externally each requires its own authorization.

---

## ❓ 11. FAQ

<details>
<summary><b>What if `uv` is missing?</b></summary>
Install <code>uv</code> from its official documentation, then rerun the initialization script. The script reports a missing executable after completing its target-path preflight.
</details>

<details>
<summary><b>What if Defuddle is missing?</b></summary>
The default live-URL capture provider is Defuddle. The agent follows <code>.agents/skills/source-extraction/references/providers/defuddle/setup.md</code>, tells you the exact pinned global npm change, and requests approval. After approval, the agent installs and verifies the CLI automatically; you do not need to run the commands manually. A live URL is not sent directly to <code>intake/tmp/</code>; Defuddle first creates its source capture under <code>inbox/web/</code>.
</details>

<details>
<summary><b>What if a file is already in <code>raw/</code>?</b></summary>
New source artifacts must enter through <code>inbox/</code>. Submitted files enter unchanged; a live URL enters as its deterministic Defuddle source capture. Artifacts already in <code>raw/&lt;state&gt;/</code> may be reprocessed from their current state directory because they have entered the lifecycle. Reprocessing must preserve the path after <code>raw/&lt;state&gt;/</code>, and when a source moves to a new state, the old state entry must be removed.
</details>

<details>
<summary><b>Can extracted Markdown go straight into <code>wiki/</code>?</b></summary>
No. Extracted Markdown first goes to <code>intake/tmp/</code>, then the Source Review Gate. Only accepted material goes to <code>intake/processed/</code> and then into <code>wiki/</code>.
</details>

<details>
<summary><b>Should personal wiki content be committed to GitHub?</b></summary>
Not by default. The package default keeps local runtime directories private. If this checkout is a personal or team wiki project and durable wiki content should be versioned, refer to <a href="gitignore-templates.md">Git Ignore Templates</a>.
</details>

---

## 💡 12. Recommended Habits

- Process sources in small batches and check one intake cycle before scaling up.
- For large files, ask the agent to inspect metadata or chunk indexes first.
- Preserve counterevidence and uncertainty for disputed claims.
- Run **Maintain Wiki** periodically.
- Put user-facing deliverables in `artifacts/` and durable knowledge in `wiki/`.
