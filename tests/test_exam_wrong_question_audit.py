from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scenarios/exam-study/skills/exam-study/scripts/audit_wrong_questions.py"
)


class ExamWrongQuestionAuditTest(unittest.TestCase):
    def test_reuses_the_standard_wikilink_resolver(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("from lint_wiki import", source)
        self.assertNotIn("WIKILINK_RE = re.compile", source)

    def run_audit(
        self,
        vault: Path,
        subject: str,
        output: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--vault",
                str(vault),
                "--subject",
                subject,
                "--output",
                str(output),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    def snapshot(self, vault: Path) -> dict[str, str]:
        return {
            path.relative_to(vault).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(vault.rglob("*"))
            if path.is_file()
        }

    def test_reports_legacy_names_collisions_indexes_and_inbound_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vault = temp / "vault"
            subject = "建设工程经济"
            subject_root = vault / "wiki/syntheses" / subject
            wrong_root = subject_root / "wrong-questions"
            wrong_root.mkdir(parents=True)

            for name in (
                "001-现值.md",
                "错题002 - 设备磨损.md",
                "PM-WQ-002-资金时间价值.md",
                "003-碰撞.md",
                "错题003-碰撞.md",
                "００４-全角序号.md",
                "005-　.md",
                "待整理.md",
            ):
                (wrong_root / name).write_text(f"# {name[:-3]}\n", encoding="utf-8")

            (subject_root / "wrong-question-index.md").write_text(
                "\n".join(
                    (
                        "# 错题索引",
                        "- [[wiki/syntheses/建设工程经济/wrong-questions/001-现值]]",
                        "- [[wiki/syntheses/建设工程经济/wrong-questions/错题002 - 设备磨损]]",
                        "- [[wiki/syntheses/建设工程经济/wrong-questions/错题002 - 设备磨损]]",
                        "",
                    )
                ),
                encoding="utf-8",
            )
            reference = vault / "wiki/syntheses/reference.md"
            reference.write_text(
                "See [[wiki/syntheses/建设工程经济/wrong-questions/PM-WQ-002-资金时间价值]].\n"
                "`[[wiki/syntheses/建设工程经济/wrong-questions/错题003-碰撞]]`\n",
                encoding="utf-8",
            )
            log = vault / "logs/wiki.md"
            log.parent.mkdir(parents=True)
            log.write_text(
                "- historical [[wiki/syntheses/建设工程经济/wrong-questions/错题003-碰撞]]\n",
                encoding="utf-8",
            )

            before = self.snapshot(vault)
            first = temp / "first.json"
            second = temp / "second.json"
            result = self.run_audit(vault, subject, first)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(self.run_audit(vault, subject, second).returncode, 1)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(self.snapshot(vault), before)

            report = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(report["schema"], 1)
            self.assertEqual(report["subject"], subject)
            statuses = {Path(item["current_path"]).name: item["status"] for item in report["records"]}
            self.assertEqual(statuses["001-现值.md"], "canonical")
            self.assertEqual(statuses["错题002 - 设备磨损.md"], "legacy")
            self.assertEqual(statuses["PM-WQ-002-资金时间价值.md"], "legacy")
            self.assertEqual(statuses["００４-全角序号.md"], "unresolved")
            self.assertEqual(statuses["005-　.md"], "unresolved")
            self.assertEqual(statuses["待整理.md"], "unresolved")
            self.assertEqual(
                [item["sequence"] for item in report["duplicate_sequences"]],
                ["002", "003"],
            )
            self.assertEqual(
                report["target_collisions"][0]["target_path"],
                f"wiki/syntheses/{subject}/wrong-questions/003-碰撞.md",
            )
            legacy_record = next(
                item
                for item in report["records"]
                if item["current_path"].endswith("PM-WQ-002-资金时间价值.md")
            )
            self.assertEqual(legacy_record["inbound_links"][0]["path"], "wiki/syntheses/reference.md")
            log_record = next(
                item
                for item in report["records"]
                if item["current_path"].endswith("错题003-碰撞.md")
            )
            self.assertEqual(log_record["inbound_links"][0]["kind"], "historical_log")
            self.assertTrue(report["index_duplicates"])
            self.assertTrue(report["index_missing"])

    def test_clean_subject_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vault = temp / "vault"
            subject = "机电工程管理与实务"
            subject_root = vault / "wiki/syntheses" / subject
            wrong_root = subject_root / "wrong-questions"
            wrong_root.mkdir(parents=True)
            for name in ("001-管道试压.md", "002-起重能力.md"):
                (wrong_root / name).write_text(f"# {name[:-3]}\n", encoding="utf-8")
            (subject_root / "wrong-question-index.md").write_text(
                "# 错题索引\n"
                "- [[wiki/syntheses/机电工程管理与实务/wrong-questions/001-管道试压]]\n"
                "- [[wiki/syntheses/机电工程管理与实务/wrong-questions/002-起重能力]]\n",
                encoding="utf-8",
            )
            artifacts = vault / "artifacts"
            artifacts.mkdir()
            output = artifacts / "wrong-question-audit.json"
            before = self.snapshot(vault)
            result = self.run_audit(vault, subject, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "clean")
            self.assertFalse(report["duplicate_sequences"])
            self.assertFalse(report["target_collisions"])
            self.assertFalse(report["index_missing"])
            self.assertFalse(report["index_duplicates"])
            after = self.snapshot(vault)
            del after["artifacts/wrong-question-audit.json"]
            self.assertEqual(after, before)

    def test_missing_subject_path_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vault = temp / "vault"
            vault.mkdir()
            result = self.run_audit(vault, "不存在科目", temp / "missing.json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("Subject directory not found", result.stderr)

    def test_missing_output_parent_returns_two_without_creating_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vault = temp / "vault"
            subject_root = vault / "wiki/syntheses/建设工程经济"
            subject_root.mkdir(parents=True)
            (subject_root / "wrong-question-index.md").write_text(
                "# 错题索引\n\n当前暂无错题。\n",
                encoding="utf-8",
            )
            output = temp / "missing" / "audit.json"

            result = self.run_audit(vault, "建设工程经济", output)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Output parent directory not found", result.stderr)
            self.assertFalse(output.parent.exists())

    def test_confirmed_subject_without_wrong_questions_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vault = temp / "vault"
            subject = "机电工程管理与实务"
            subject_root = vault / "wiki/syntheses" / subject
            subject_root.mkdir(parents=True)
            (subject_root / "wrong-question-index.md").write_text(
                "# 错题索引\n\n当前暂无错题。\n",
                encoding="utf-8",
            )
            output = temp / "empty-subject.json"

            result = self.run_audit(vault, subject, output)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "clean")
            self.assertEqual(report["records"], [])
            self.assertFalse((subject_root / "wrong-questions").exists())

    def test_wrong_question_path_must_be_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vault = temp / "vault"
            subject = "机电工程管理与实务"
            subject_root = vault / "wiki/syntheses" / subject
            subject_root.mkdir(parents=True)
            (subject_root / "wrong-question-index.md").write_text(
                "# 错题索引\n",
                encoding="utf-8",
            )
            wrong_path = subject_root / "wrong-questions"
            wrong_path.write_text("not a directory\n", encoding="utf-8")
            output = temp / "wrong-type.json"
            before = self.snapshot(vault)

            result = self.run_audit(vault, subject, output)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Wrong-question path is not a directory", result.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(self.snapshot(vault), before)

    def test_missing_index_is_a_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            vault = temp / "vault"
            wrong_root = vault / "wiki/syntheses/建设工程经济/wrong-questions"
            wrong_root.mkdir(parents=True)
            (wrong_root / "001-现值.md").write_text("# 现值\n", encoding="utf-8")
            output = temp / "missing-index.json"

            result = self.run_audit(vault, "建设工程经济", output)

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["index_file_missing"])


if __name__ == "__main__":
    unittest.main()
