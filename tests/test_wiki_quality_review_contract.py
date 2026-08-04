from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WikiQualityReviewContractTest(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_quality_review_is_a_read_only_maintain_wiki_procedure(self) -> None:
        agents = self.read("AGENTS.md")
        wiki = self.read("WIKI.md")
        skill = self.read(".agents/skills/wiki-quality-review/SKILL.md")

        self.assertIn("`wiki-quality-review` skill within `Maintain Wiki`", agents)
        self.assertIn("review-only request is read-only", agents)
        self.assertIn("explicitly approves", agents)
        self.assertIn("follow the write boundary in `WIKI.md`", agents)

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
        self.assertIn("Before external search", agents)
        self.assertIn("read-only by default", agents)
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
        self.assertIn("Focused project validators may reuse", lint)
        self.assertNotIn("ALWAYS run this skill first", lint)
        self.assertIn("Add only required frontmatter", markdown)
        self.assertIn("when the user requests them", creator)

    def test_exam_scenario_uses_one_evidence_backed_wrong_question_inventory(self) -> None:
        scenario = self.read("scenarios/exam-study/README.md")
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
        self.assertIn("Use direct concepts, causal reasoning", starter_pages)
        self.assertIn("Explanation style:", self.read("scenarios/exam-study/PROJECT.template.md"))
        self.assertIn("question_acceptance: needs_answer", starter_pages)
        self.assertNotIn("question_acceptance: accepted", starter_pages)


if __name__ == "__main__":
    unittest.main()
