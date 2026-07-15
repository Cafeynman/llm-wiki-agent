from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills/skill-creator"
QUICK_VALIDATE = SKILL_ROOT / "scripts/quick_validate.py"
PACKAGE_SKILL = SKILL_ROOT / "scripts/package_skill.py"


class SkillCreatorTest(unittest.TestCase):
    def test_direct_validation_and_packaging(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            sample = temp / "sample-skill"
            (sample / "scripts").mkdir(parents=True)
            (sample / "evals").mkdir()
            (sample / "__pycache__").mkdir()
            (sample / "SKILL.md").write_text(
                """---
name: sample-skill
description: Use for a representative packaging check.
---

# Sample Skill
""",
                encoding="utf-8",
            )
            (sample / "scripts/helper.py").write_text(
                'print("helper")\n', encoding="utf-8"
            )
            (sample / "evals/results.json").write_text("{}", encoding="utf-8")
            (sample / "__pycache__/helper.pyc").write_bytes(b"cache")

            validation = subprocess.run(
                [sys.executable, str(QUICK_VALIDATE), str(sample)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(validation.returncode, 0, validation.stderr)

            output_dir = temp / "packages"
            packaging = subprocess.run(
                [sys.executable, str(PACKAGE_SKILL), str(sample), str(output_dir)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(packaging.returncode, 0, packaging.stderr)

            archive = output_dir / "sample-skill.skill"
            with zipfile.ZipFile(archive) as packaged:
                names = set(packaged.namelist())

            self.assertIn("sample-skill/SKILL.md", names)
            self.assertIn("sample-skill/scripts/helper.py", names)
            self.assertFalse(any("evals/" in name for name in names))
            self.assertFalse(any("__pycache__/" in name for name in names))
            self.assertFalse(any(name.endswith(".pyc") for name in names))

    def test_removed_evaluation_stack_has_no_retained_surface(self) -> None:
        removed_paths = (
            "agents",
            "assets",
            "eval-viewer",
            "references",
            "scripts/aggregate_benchmark.py",
            "scripts/generate_report.py",
            "scripts/improve_description.py",
            "scripts/run_eval.py",
            "scripts/run_loop.py",
            "scripts/utils.py",
            "scripts/__init__.py",
        )
        for relative_path in removed_paths:
            self.assertFalse((SKILL_ROOT / relative_path).exists(), relative_path)

        retained = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                SKILL_ROOT / "SKILL.md",
                QUICK_VALIDATE,
                PACKAGE_SKILL,
            )
        )
        for stale_reference in (
            "aggregate_benchmark",
            "generate_report",
            "improve_description",
            "run_eval",
            "run_loop",
            "eval-viewer",
        ):
            self.assertNotIn(stale_reference, retained)


if __name__ == "__main__":
    unittest.main()
