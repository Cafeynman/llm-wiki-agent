from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = ROOT / "scenarios/exam-study"
SCENARIO_SKILL = SCENARIO_ROOT / "skills/exam-study"


class ScenarioContractTest(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_project_selects_one_active_scenario_without_a_cli_parameter(self) -> None:
        project = self.read("PROJECT.md")
        template = self.read("scenarios/exam-study/PROJECT.template.md")
        agents = self.read("AGENTS.md")
        agents_text = " ".join(agents.split())

        self.assertEqual(project.splitlines().count("- Active scenario:"), 1)
        self.assertEqual(
            template.splitlines().count("- Active scenario: exam-study"), 1
        )
        self.assertIn("only source of active-scenario selection", agents_text)
        self.assertIn("scenarios/<name>/skills/<name>/SKILL.md", agents_text)
        self.assertIn("current request is relevant to that scenario", agents_text)
        self.assertIn("A scenario directory does not activate itself", agents_text)
        self.assertIn("Do not read skills from inactive scenarios", agents_text)
        self.assertIn("universal package skills", agents_text)
        self.assertIn("report the missing name and path", agents_text)
        self.assertIn("Do not guess", agents_text)

        init_scripts = self.read("scripts/init.ps1") + self.read("scripts/init.sh")
        upgrade_scripts = self.read("scripts/upgrade.ps1") + self.read("scripts/upgrade.sh")
        scripts = init_scripts + upgrade_scripts
        for scenario_parameter in (
            r"(?i)(?:^|\s)-Scenario\b",
            r"(?i)(?:^|\s)--scenario\b",
            r"(?i)\$Scenario\b",
        ):
            self.assertIsNone(re.search(scenario_parameter, scripts))

    def test_exam_study_workflow_exists_only_in_the_active_scenario_skill(self) -> None:
        readme = self.read("scenarios/exam-study/README.md")
        skill = self.read("scenarios/exam-study/skills/exam-study/SKILL.md")
        contract = self.read(
            "scenarios/exam-study/skills/exam-study/references/workflow-contract.md"
        )
        starter_pages = self.read("scenarios/exam-study/starter-pages.md")
        skill_text = " ".join(skill.split())

        self.assertFalse((ROOT / ".agents/skills/exam-study").exists())
        self.assertIn("Active scenario: exam-study", readme)
        self.assertIn("PROJECT.template.md", readme)
        self.assertIn("starter-pages.md", readme)
        self.assertIn("skills/exam-study/SKILL.md", readme)
        for daily_heading in (
            "## Wrong-Question Topic Layout and Naming",
            "## Formal Question Acceptance",
            "## Study Planning Loop",
            "### Structural Audit",
        ):
            self.assertNotIn(daily_heading, readme)

        self.assertIn("name: exam-study", skill)
        self.assertIn("references/workflow-contract.md", skill_text)
        self.assertIn("WIKI.md", skill_text)
        self.assertIn(".agents/skills/source-extraction/SKILL.md", skill_text)
        self.assertIn("Source Review Gate", skill_text)
        self.assertIn("Do not infer", skill_text)
        self.assertIn("Do not create a parallel queue", skill_text)
        self.assertIn("Do not modify `AGENTS.md` or `WIKI.md`", skill_text)
        self.assertIn(
            "Update `PROJECT.md` only with explicitly confirmed project-specific values",
            skill_text,
        )
        self.assertIn("ordinary single-question work", skill_text)

        self.assertIn("## Wrong-Question Topic Layout and Naming", contract)
        self.assertIn("## Formal Question Acceptance", contract)
        self.assertIn("## Study Planning Loop", contract)
        self.assertIn("### Structural Audit", contract)
        self.assertIn("search the relevant subject pages", contract)
        self.assertIn("is the only detailed wrong-question", contract)
        self.assertIn("scan both filenames and the canonical", contract)
        self.assertIn("old-to-new path map", contract)
        self.assertIn("writes only the explicitly requested report file", contract)

        self.assertIn("# Exam Study Starter Pages", starter_pages)
        self.assertNotIn("## Acceptance Rules", starter_pages)
        self.assertNotIn("## Adjustment Rules", starter_pages)
        self.assertNotIn("## Pending Decisions", starter_pages)
        self.assertNotIn("Use direct concepts, causal reasoning", starter_pages)

    def test_scenario_skill_and_script_are_package_owned(self) -> None:
        new_paths = (
            "scenarios/exam-study/skills/exam-study/SKILL.md",
            "scenarios/exam-study/skills/exam-study/references/workflow-contract.md",
            "scenarios/exam-study/skills/exam-study/scripts/audit_wrong_questions.py",
        )
        old_path = "scenarios/exam-study/" + "scripts/audit_wrong_questions.py"
        inventory_lines = self.read("scripts/package-files.txt").splitlines()

        for path in new_paths:
            self.assertTrue((ROOT / path).is_file(), path)
            self.assertIn(f"active {path}", inventory_lines)
        self.assertFalse((ROOT / old_path).exists())

    def test_contract_review_and_skill_creator_cover_scenario_skills(self) -> None:
        contract_review = self.read(".agents/skills/wiki-contract-review/SKILL.md")
        skill_creator = self.read(".agents/skills/skill-creator/SKILL.md")
        skill_creator_text = " ".join(skill_creator.split())

        self.assertIn("scenarios/*/skills/*/SKILL.md", contract_review)
        self.assertIn("active scenario recorded in `PROJECT.md`", contract_review)
        self.assertIn("<skill-directory>", skill_creator)
        self.assertIn(
            "scenario-specific skills under `scenarios/<name>/skills/`",
            skill_creator_text,
        )


if __name__ == "__main__":
    unittest.main()
