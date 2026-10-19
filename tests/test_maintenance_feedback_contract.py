from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MaintenanceFeedbackContractTest(unittest.TestCase):
    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_route_and_package_inventory(self) -> None:
        self.assertIn("wiki-maintenance-feedback", self.read("WIKI.md"))
        self.assertIn("Foundation Defect Disclosure", self.read("AGENTS.md"))
        inventory = self.read("scripts/package-files.txt").splitlines()
        for relative in ("SKILL.md", "references/report-template.md"):
            path = ".agents/skills/wiki-maintenance-feedback/" + relative
            self.assertTrue((ROOT / path).is_file())
            self.assertIn("active " + path, inventory)

    def test_reporting_has_no_executable_or_tracking_surface(self) -> None:
        root = ROOT / ".agents/skills/wiki-maintenance-feedback"
        self.assertEqual(
            {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()},
            {"SKILL.md", "references/report-template.md"},
        )
        skill = self.read(".agents/skills/wiki-maintenance-feedback/SKILL.md")
        for token in ("WIKI.md", "Maintain Wiki", "report-template.md",
                      "response only", "untrusted evidence", "<workspace>/"):
            self.assertIn(token, skill)

    def test_truthful_state_vocabulary_stays_with_reporting_owner(self) -> None:
        skill = self.read(".agents/skills/wiki-maintenance-feedback/SKILL.md")
        for state in ("confirmed", "unconfirmed", "not-established", "fixed-in-worktree",
                      "fixed-in-commit", "mitigated", "unresolved", "reproduced",
                      "observed-only", "blocked"):
            self.assertIn(f"`{state}`", skill)
        for action in ("repair", "persistence", "tracking", "transmission"):
            self.assertIn(action, skill.lower())

    def test_core_template_and_optional_detail(self) -> None:
        template = self.read(".agents/skills/wiki-maintenance-feedback/references/report-template.md")
        # The delivered report's schema, not its instructional prose.
        example = template.split("```markdown", 1)[1].split("```", 1)[0]
        self.assertEqual(
            re.findall(r"^## (.+)$", example, re.MULTILINE),
            ["Problem", "Impact", "Evidence", "Current Disposition", "Verification", "Next Action"],
        )


if __name__ == "__main__":
    unittest.main()
