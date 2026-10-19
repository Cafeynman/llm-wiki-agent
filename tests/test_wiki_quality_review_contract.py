from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WikiQualityReviewContractTest(unittest.TestCase):
    """Static routing and vocabulary checks; prose behavior needs scenario review."""

    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_review_routes_and_report_vocabulary(self) -> None:
        wiki = self.read("WIKI.md")
        skill = self.read(".agents/skills/wiki-quality-review/SKILL.md")
        for route in ("wiki-quality-review", "wiki-contract-review", "obsidian-wiki-lint"):
            self.assertIn(route, wiki)
        for token in ("Maintain Wiki", "Add Knowledge", "Source Review Gate",
                      "wiki-contract-review", "obsidian-wiki-lint", "read-only"):
            self.assertIn(token, skill)
        for value in ("deep", "scoped", "sampled", "blocked",
                      "no-material-gap-found", "material-gap-found", "indeterminate"):
            self.assertIn(f"`{value}`", skill)
        for identifier in ("WQ-001", "KC-001"):
            self.assertIn(identifier, skill)

    def test_bootstrap_and_procedure_owners_are_reachable(self) -> None:
        agents = self.read("AGENTS.md")
        for path in ("WIKI.md", "PROJECT.md"):
            self.assertIn(path, agents)
            self.assertTrue((ROOT / path).is_file())
        for name in ("source-extraction", "obsidian-markdown", "obsidian-wiki-lint",
                     "wiki-quality-review", "wiki-contract-review", "wiki-maintenance-feedback"):
            self.assertIn(name, self.read("WIKI.md"))
            self.assertTrue((ROOT / ".agents/skills" / name / "SKILL.md").is_file())

    def test_review_does_not_install_an_extra_runtime_directory(self) -> None:
        for path in ("WIKI.md", "scripts/init.ps1", "scripts/init.sh",
                     "scripts/upgrade.ps1", "scripts/upgrade.sh"):
            self.assertNotIn("reviews/wiki-quality", self.read(path))

    def test_authorization_boundaries_are_present(self) -> None:
        for name in ("grill-decisions", "wiki-quality-review", "wiki-contract-review"):
            text = self.read(f".agents/skills/{name}/SKILL.md").lower()
            self.assertRegex(text, r"read-only|review-only")
            self.assertIn("authoriz", text)
            self.assertIn("unresolved", text)


if __name__ == "__main__":
    unittest.main()
