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

**What this does:**
1. Runs `uv sync` to create or update the `.venv/` runtime state.
2. Creates all necessary workflow directories (`inbox/`, `raw/`, `intake/`, `wiki/`, etc.).

---

## 📂 4. Directory Structure

| Directory | Responsibility |
| --- | --- |
| `inbox/` | 📥 Only entrypoint for user-submitted original files. |
| `raw/` | 🗄️ Final state area for original files. (Does not store agent-generated Markdown). |
| `intake/tmp/` | ⚙️ Temporary Markdown after conversion and before source review. |
| `intake/processed/` | ✅ Accepted Markdown ready for wiki ingestion. |
| `reviews/` | 📝 Source review and discussion reflection records. |
| `logs/` | ⏱️ High-level wiki operation history (`logs/wiki.md`). |
| `wiki/` | 🧠 Durable knowledge pages. |
| `questions/` | ❓ Open questions and investigation trails. |
| `artifacts/` | 📦 Reports, briefs, drafts, templates, and user-facing deliverables. |

---

## 📥 5. First File Intake Workflow

Follow this lifecycle for adding new knowledge:

1. **Drop File:** Put an original file into `inbox/` (e.g., `inbox/example.md`).
2. **Prompt Agent:** Ask the agent: *"Process the files in inbox/ according to AGENTS.md, PROJECT.md, and WIKI.md."*
3. **Agent Action:** 
    - The agent converts content into `intake/tmp/YYYY-MM-DD/source.md`.
    - It runs the **Source Review Gate**.
    - Original file moves to a `raw/` subfolder.
    - Only `digested` (approved) content moves to `intake/processed/` and updates `wiki/`.

---

## 🔍 6. Source Review Gate Outcomes

The Source Review Gate is the strict boundary that decides whether a source deserves to enter the wiki.

| Outcome | Destination | Next Action |
| --- | --- | --- |
| **`digested`** | `raw/digested/` | Promote to `intake/processed/`, create source card, update wiki. |
| **`needs-review`**| `raw/needs-review/`| Record review question. (e.g., requires human judgment or image processing). Do not update wiki yet. |
| **`ignored`** | `raw/ignored/` | Record reason. Do not update wiki. |
| **`unsupported`** | `raw/unsupported/` | Record blocker. Do not update wiki. |

> [!WARNING]
> A successful conversion does **not** mean automatic acceptance. Empty, garbled, or highly image-dependent files become `needs-review`.

---

## 📜 7. Text-First Boundary

LLM Wiki Agent operates with a strict text-first mindset:
- All readable documents (HTML, PDF, Word, PPT, Excel, etc.) become Markdown before ingestion.
- Scans, images, and audio stay as original sources in `raw/` but are **not** first-class wiki content.
- Do not copy images directly into wiki pages unless image handling is explicitly configured.

> [!TIP]
> For OCR handling, refer to [markitdown-ocr.md](markitdown-ocr.md). OCR is optional and not enabled by default.

---

## 🧠 8. Use Existing Knowledge

To use the knowledge base, just ask your agent:
*"What does the wiki say about <topic>?"*

The agent will search:
1. `wiki/index.md` & `wiki/overview.md`
2. `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/claims/`
3. `questions/` and `artifacts/`

The agent should place all generated deliverables (reports, templates, drafts) into the `artifacts/` directory.

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
<summary><b>What if a file is already in <code>raw/</code>?</b></summary>
New user-submitted originals must enter through <code>inbox/</code>. <code>raw/</code> is a post-review state area, not an intake entrypoint.
</details>

<details>
<summary><b>Can converted Markdown go straight into <code>wiki/</code>?</b></summary>
No. Converted Markdown first goes to <code>intake/tmp/</code>, then the Source Review Gate. Only accepted material goes to <code>intake/processed/</code> and then into <code>wiki/</code>.
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
