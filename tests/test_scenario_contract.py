from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ScenarioContractTest(unittest.TestCase):
    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_project_owns_scenario_selection(self) -> None:
        for path, value in (("PROJECT.md", ""), ("scenarios/exam-study/PROJECT.template.md", "exam-study")):
            fields = re.findall(r"^- Active scenario:[ \t]*([^\n]*)$", self.read(path), re.MULTILINE)
            self.assertEqual([field.strip() for field in fields], [value])
        self.assertFalse((ROOT / ".agents/skills/exam-study").exists())
        for path in ("scripts/init.ps1", "scripts/init.sh", "scripts/upgrade.ps1", "scripts/upgrade.sh"):
            self.assertIsNone(re.search(r"(?i)(?:^|\s)--?Scenario\b|\$Scenario\b", self.read(path)))

    def test_scenario_files_are_owned_and_references_resolve(self) -> None:
        inventory = self.read("scripts/package-files.txt").splitlines()
        base = "scenarios/exam-study/skills/exam-study/"
        for relative in ("SKILL.md", "references/workflow-contract.md", "scripts/audit_wrong_questions.py"):
            self.assertTrue((ROOT / (base + relative)).is_file())
            self.assertIn("active " + base + relative, inventory)
        skill = self.read(base + "SKILL.md")
        for token in ("Active scenario: exam-study", "references/workflow-contract.md",
                      ".agents/skills/source-extraction/SKILL.md", "Source Review Gate"):
            self.assertIn(token, " ".join(skill.split()))

    def test_acceptance_vocabulary_and_unaccepted_starter(self) -> None:
        contract = self.read("scenarios/exam-study/skills/exam-study/references/workflow-contract.md")
        for value in ("accepted", "needs_enrichment", "enriched_pending_confirmation",
                      "needs_answer", "pending_decision", "rejected"):
            self.assertIn(f"`{value}`", contract)
        starter = self.read("scenarios/exam-study/starter-pages.md")
        self.assertIn("question_acceptance: needs_answer", starter)
        self.assertNotIn("question_acceptance: accepted", starter)
        self.assertIn("read-only", contract)
        self.assertIn("study-dashboard.md", contract)
        self.assertIn("study-plan.md", contract)


if __name__ == "__main__":
    unittest.main()
