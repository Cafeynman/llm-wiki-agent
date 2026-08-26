from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WikiQualityReviewContractTest(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_quality_review_is_a_read_only_maintain_wiki_procedure(self) -> None:
        wiki = self.read("WIKI.md")
        skill = self.read(".agents/skills/wiki-quality-review/SKILL.md")

        self.assertIn(
            "A review, audit, or health-check request is read-only", wiki
        )
        self.assertIn("explicitly approves a resolution", wiki)

        self.assertIn("`Maintain Wiki`", skill)
        self.assertIn("obsidian-wiki-lint", skill)
        self.assertIn("Source Review Gate", skill)
        self.assertIn("wiki-contract-review", skill)
        self.assertIn("### WQ-001", skill)
        self.assertIn("review, audit, or health check", skill)
        self.assertIn("original request also asks for fixes", skill)
        self.assertIn("clear mechanical findings", skill)
        self.assertIn("findings always require an approved resolution", skill)

    def test_quality_review_audits_source_to_wiki_coverage_without_mandating_optional_pages(
        self,
    ) -> None:
        wiki = self.read("WIKI.md")
        skill = self.read(".agents/skills/wiki-quality-review/SKILL.md")
        wiki_text = " ".join(wiki.split())
        skill_text = " ".join(skill.split())

        self.assertIn("source-to-wiki coverage", wiki_text)
        self.assertIn("construction opportunities", wiki_text)
        self.assertIn("## Source-to-Wiki Coverage", skill_text)
        self.assertIn("`raw/digested/`", skill_text)
        self.assertIn("recommended ingest scope", skill_text)
        self.assertIn("actual result pages", skill_text)
        self.assertIn("do not prove coverage", skill_text)
        self.assertIn("source card can be sufficient", skill_text)
        self.assertIn("not itself a defect", skill_text)
        self.assertIn("construction candidate", skill_text)
        self.assertIn("improve reuse or traceability", skill_text)
        self.assertIn("### KC-001", skill_text)
        self.assertIn("`no-material-gap-found`", skill_text)
        self.assertIn("`material-gap-found`", skill_text)
        self.assertIn("`indeterminate`", skill_text)
        self.assertIn("sampled", skill_text)
        self.assertIn("route the approved write through `Add Knowledge`", skill_text)
        self.assertIn("Do not generate an aggregate quality score", skill_text)

    def test_contract_review_excludes_page_level_content_quality(self) -> None:
        contract_review = self.read(
            ".agents/skills/wiki-contract-review/SKILL.md"
        )

        self.assertIn("wiki-quality-review", contract_review)
        self.assertIn("page-level factual accuracy", contract_review)
        self.assertIn(
            "runtime structure follows its declared ownership", contract_review
        )
        self.assertNotIn("only receipts", contract_review)
        self.assertNotIn("content-rich wiki summaries", contract_review)

    def test_quality_review_does_not_add_a_runtime_review_directory(self) -> None:
        surfaces = (
            self.read("AGENTS.md")
            + self.read("WIKI.md")
            + self.read(".agents/skills/wiki-quality-review/SKILL.md")
            + self.read("scripts/init.ps1")
            + self.read("scripts/init.sh")
            + self.read("scripts/upgrade.ps1")
            + self.read("scripts/upgrade.sh")
        )

        self.assertNotIn("reviews/wiki-quality", surfaces)

    def test_every_conversation_begins_with_local_context_and_answering_is_read_only(self) -> None:
        agents = self.read("AGENTS.md")
        agents_text = " ".join(agents.split())
        wiki = self.read("WIKI.md")
        usage = self.read("docs/usage.md")
        usage_zh = self.read("docs/usage.zh-CN.md")
        readme = self.read("README.md")
        readme_zh = self.read("README.zh-CN.md")
        contract_review = self.read(
            ".agents/skills/wiki-contract-review/SKILL.md"
        )

        self.assertIn("## Knowledge Workspace Bootstrap", agents)
        self.assertIn("At the beginning of every conversation", agents)
        self.assertIn("programming", agents.lower())
        self.assertIn("resumed conversation", agents)
        self.assertIn("complete `WIKI.md` and `PROJECT.md`", agents)
        self.assertIn("before planning", agents)
        self.assertIn("prior reads", " ".join(agents.split()))
        self.assertNotIn("For the first wiki task", agents)
        self.assertNotIn("Before handling any wiki task", agents)
        self.assertNotIn("At the start of every user task", agents)
        self.assertIn("before external search", agents_text)
        self.assertIn("sole owner of the", agents)
        self.assertIn("state and write boundaries", agents_text)
        self.assertIn("target-only skills", agents)
        self.assertIn("At the beginning of every conversation", usage)
        self.assertIn("所有对话一开始", usage_zh)
        self.assertIn("Every conversation in the initialized workspace", readme)
        self.assertIn("所有对话一开始", readme_zh)
        self.assertIn(
            "verify that every conversation begins by reading",
            " ".join(contract_review.lower().split()),
        )
        self.assertIn("Every conversation in a knowledge workspace begins", wiki)
        self.assertIn("Do not start external research", wiki)
        self.assertIn("is not by itself a\nrequest to write the wiki", wiki)
        self.assertIn("wiki-quality-review", wiki)
        self.assertIn("respectively unfinished", wiki)
        self.assertIn("strong direct support", wiki)

    def test_agents_points_to_wiki_without_repeating_its_detailed_contract(self) -> None:
        agents = self.read("AGENTS.md")
        agents_text = " ".join(agents.split())

        self.assertIn("`WIKI.md` is the sole owner", agents)
        self.assertIn("Use the smallest workflow it defines", agents_text)
        self.assertIn("assigns detailed procedures", agents_text)
        self.assertIn("use `.agents/skills/obsidian-markdown/`", agents_text)
        self.assertIn("use `.agents/skills/source-extraction/`", agents_text)

        for duplicated_heading in (
            "## Wiki Markdown and Frontmatter",
            "## Intake Output Names",
            "## Source Extraction Providers",
            "## Workflow Router",
            "## Wiki Agent Behavior",
            "## Large Sources",
        ):
            self.assertNotIn(duplicated_heading, agents)

        for wiki_owned_detail in (
            "Frontmatter `sources:` entries",
            "Use `Add Knowledge` when",
            "Use `Use Knowledge` when",
            "Use `Maintain Wiki` when",
            "Record one concise `logs/wiki.md` entry",
            "Update `wiki/index.md` only when",
            "Update `wiki/home.md` only when",
        ):
            self.assertNotIn(wiki_owned_detail, agents)

        owned_contracts = {
            "WIKI.md": (
                "Preserve the source-relative parent path",
                "Frontmatter `sources:` entries are quoted wikilink strings",
                "A review, audit, or health-check request is read-only",
                "`wiki/index.md` changes only when",
                "`wiki/home.md` changes only when",
                "one concise operation-log entry",
            ),
            ".agents/skills/source-extraction/references/intake-lifecycle.md": (
                "inbox/web/<source-language-page-title>--<url-hash>.md",
                "Source Review Gate",
            ),
            ".agents/skills/source-extraction/references/large-source-chunking.md": (
                "this file owns chunking mechanics",
                "## Splitting Rules",
            ),
            ".agents/skills/obsidian-markdown/references/PROPERTIES.md": (
                "quote",
                "wikilink",
            ),
        }
        for owner, markers in owned_contracts.items():
            content = self.read(owner)
            for marker in markers:
                self.assertIn(marker, content, f"{owner} no longer owns {marker!r}")

    def test_startup_wiki_routes_detailed_procedures_to_existing_skills(self) -> None:
        wiki = self.read("WIKI.md")

        self.assertLessEqual(len(wiki.splitlines()), 280)
        self.assertIn("source-extraction", wiki)
        self.assertIn("obsidian-markdown", wiki)
        self.assertIn("obsidian-wiki-lint", wiki)
        self.assertIn("wiki-quality-review", wiki)
        self.assertNotIn("The intake order is:", wiki)
        self.assertNotIn("If roughly 5-20%", wiki)
        self.assertNotIn("Check for:\n\n1. Broken wikilinks", wiki)
        self.assertIn("For a whole-wiki health or lint review", wiki)
        self.assertIn("A focused validator may reuse", wiki)

    def test_supporting_skills_keep_optional_process_conditional(self) -> None:
        extraction = self.read(".agents/skills/source-extraction/SKILL.md")
        lint = self.read(".agents/skills/obsidian-wiki-lint/SKILL.md")
        markdown = self.read(".agents/skills/obsidian-markdown/SKILL.md")
        creator = self.read(".agents/skills/skill-creator/SKILL.md")

        self.assertIn("Read `provider-registry.md` when", extraction)
        self.assertIn("read `contract.md` when", extraction)
        self.assertIn("focused scopes for ordinary writes", lint)
        self.assertNotIn("ALWAYS run this skill first", lint)
        self.assertIn("Add only required frontmatter", markdown)
        self.assertIn("when the user requests them", creator)

    def test_optional_configuration_and_validation_are_proportionate(self) -> None:
        agents = self.read("AGENTS.md")
        project = self.read("PROJECT.md")
        wiki = self.read("WIKI.md")
        scenario = self.read("scenarios/exam-study/README.md")

        self.assertIn("current source task needs a choice", agents)
        self.assertNotIn("During first project-context confirmation", agents)
        self.assertIn("confirmed source-extraction preferences", project)
        self.assertNotIn("when a source task needs", project)
        self.assertIn("smallest affected scope", wiki)
        self.assertIn("Use the whole `wiki/` scope", wiki)
        self.assertIn("Confirm only the project fields", scenario)

    def test_exam_scenario_uses_one_evidence_backed_wrong_question_inventory(self) -> None:
        scenario = self.read(
            "scenarios/exam-study/skills/exam-study/references/workflow-contract.md"
        )
        starter_pages = self.read("scenarios/exam-study/starter-pages.md")

        self.assertIn("search the relevant subject pages", scenario)
        self.assertIn("is the only detailed wrong-question", scenario)
        self.assertIn("scan both filenames and the canonical", scenario)
        self.assertIn("update `PROJECT.md` first", scenario)
        self.assertIn("literal canonical wrong-question topic basename", scenario)
        self.assertIn("The basename consists", scenario)
        self.assertIn("subject directory carries subject identity", scenario)
        self.assertIn("old-to-new path map", scenario)
        self.assertIn("writes only the explicitly requested report file", scenario)
        self.assertIn("Use the basename exactly as", starter_pages)
        self.assertIn("The parent directory carries the", starter_pages)
        self.assertIn("Use direct concepts, causal reasoning", scenario)
        self.assertIn("Explanation style:", self.read("scenarios/exam-study/PROJECT.template.md"))
        self.assertIn("question_acceptance: needs_answer", starter_pages)
        self.assertNotIn("question_acceptance: accepted", starter_pages)


if __name__ == "__main__":
    unittest.main()
