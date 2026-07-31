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
        self.assertIn("explicitly approves findings", wiki)

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


if __name__ == "__main__":
    unittest.main()
