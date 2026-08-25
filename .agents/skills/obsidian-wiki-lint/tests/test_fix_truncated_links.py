import io
import sys
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fix_truncated_links


class TestFixTruncatedLinks(unittest.TestCase):
    def test_write_changes_active_link_and_preserves_code_examples(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("intake/processed/example")
            target_abs = vault / target_dir
            target_abs.mkdir(parents=True)
            (target_abs / "complete-source.md").write_text(
                "Target.", encoding="utf-8"
            )

            source_file = Path("wiki/source.md")
            source_abs = vault / source_file
            source_abs.parent.mkdir()
            source_abs.write_text(
                """Active [[intake/processed/example/complete]].
Inline `[[intake/processed/example/complete]]`.

```markdown
[[intake/processed/example/complete]]
[sample](intake/processed/example/complete)
```
""",
                encoding="utf-8",
            )

            with patch("builtins.print"):
                result = fix_truncated_links.fix_links(
                    vault, source_file, target_dir, write=True
                )

            self.assertEqual(result, 0)
            self.assertEqual(
                source_abs.read_text(encoding="utf-8"),
                """Active [[intake/processed/example/complete-source]].
Inline `[[intake/processed/example/complete]]`.

```markdown
[[intake/processed/example/complete]]
[sample](intake/processed/example/complete)
```
""",
            )

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("intake/processed/example")
            target_abs = vault / target_dir
            target_abs.mkdir(parents=True)
            (target_abs / "complete-source.md").write_text(
                "Target.", encoding="utf-8"
            )

            source_file = Path("wiki/source.md")
            source_abs = vault / source_file
            source_abs.parent.mkdir()
            original = "[[intake/processed/example/complete]]"
            source_abs.write_text(original, encoding="utf-8")

            with patch("builtins.print"):
                result = fix_truncated_links.fix_links(
                    vault, source_file, target_dir, write=False
                )

            self.assertEqual(result, 0)
            self.assertEqual(source_abs.read_text(encoding="utf-8"), original)

    def test_bracket_target_fix_preserves_fragment_alias_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("intake/processed/example")
            target_abs = vault / target_dir
            target_abs.mkdir(parents=True)
            (target_abs / "国家电网生[2009]133号-全文.md").write_text("Target.", encoding="utf-8")
            source_file = Path("wiki/source.md")
            source_abs = vault / source_file
            source_abs.parent.mkdir()
            source_abs.write_text(
                "[[intake/processed/example/国家电网生[2009]133号#范围|法规]]",
                encoding="utf-8",
            )

            with patch("builtins.print"):
                first = fix_truncated_links.fix_links(vault, source_file, target_dir, write=True)
                second = fix_truncated_links.fix_links(vault, source_file, target_dir, write=True)

            self.assertEqual(first, 0)
            self.assertEqual(second, 0)
            self.assertEqual(
                source_abs.read_text(encoding="utf-8"),
                "[[intake/processed/example/国家电网生[2009]133号-全文#范围|法规]]",
            )

    def test_fix_uses_original_link_text_and_preserves_backticks_in_alias(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("intake/processed/example")
            target_abs = vault / target_dir
            target_abs.mkdir(parents=True)
            (target_abs / "complete-source.md").write_text("Target.", encoding="utf-8")
            source_file = Path("wiki/source.md")
            source_abs = vault / source_file
            source_abs.parent.mkdir()
            source_abs.write_text(
                "[[intake/processed/example/complete#scope|alias `quoted` note]]",
                encoding="utf-8",
            )

            with patch("builtins.print"):
                result = fix_truncated_links.fix_links(vault, source_file, target_dir, write=True)

            self.assertEqual(result, 0)
            self.assertEqual(
                source_abs.read_text(encoding="utf-8"),
                "[[intake/processed/example/complete-source#scope|alias `quoted` note]]",
            )

    def test_unique_fuzzy_normalization_candidate_is_not_fixed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("intake/processed/example")
            target_abs = vault / target_dir
            target_abs.mkdir(parents=True)
            (target_abs / "complete source.md").write_text("Target.", encoding="utf-8")
            source_file = Path("wiki/source.md")
            source_abs = vault / source_file
            source_abs.parent.mkdir()
            original = "[[intake/processed/example/completesource]]"
            source_abs.write_text(original, encoding="utf-8")

            with patch("builtins.print"):
                result = fix_truncated_links.fix_links(vault, source_file, target_dir, write=True)

            self.assertEqual(result, 0)
            self.assertEqual(source_abs.read_text(encoding="utf-8"), original)

    def test_does_not_cross_into_descendant_or_directory_targets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("targets")
            target_abs = vault / target_dir
            target_abs.mkdir()
            (target_abs / "name-complete.md").write_text("Target.", encoding="utf-8")
            (target_abs / "targets-guide.md").write_text("Guide.", encoding="utf-8")
            source_file = Path("source.md")
            source_abs = vault / source_file
            original = "[[targets/sub/name]]\n[[targets/]]\n"
            source_abs.write_text(original, encoding="utf-8")

            with patch("builtins.print"):
                result = fix_truncated_links.fix_links(vault, source_file, target_dir, write=True)

            self.assertEqual(result, 0)
            self.assertEqual(source_abs.read_text(encoding="utf-8"), original)

    def test_rejects_source_or_target_outside_declared_vault(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            vault = base / "vault"
            vault.mkdir()
            outside_source = base / "outside.md"
            outside_source.write_text("[[targets/name]]", encoding="utf-8")
            outside_target = base / "targets"
            outside_target.mkdir()

            with self.assertRaisesRegex(ValueError, "source file must resolve inside"):
                fix_truncated_links.fix_links(
                    vault, Path("../outside.md"), Path("inside"), write=False
                )

            inside_source = vault / "source.md"
            inside_source.write_text("[[targets/name]]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "target directory must resolve inside"):
                fix_truncated_links.fix_links(
                    vault, Path("source.md"), Path("../targets"), write=False
                )

    def test_write_preserves_existing_crlf_line_endings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("intake/processed/example")
            target_abs = vault / target_dir
            target_abs.mkdir(parents=True)
            (target_abs / "complete-source.md").write_text("Target.", encoding="utf-8")
            source_file = Path("wiki/source.md")
            source_abs = vault / source_file
            source_abs.parent.mkdir()
            source_abs.write_bytes(
                b"First [[intake/processed/example/complete]].\r\nSecond line.\r\n"
            )

            with patch("builtins.print"):
                result = fix_truncated_links.fix_links(vault, source_file, target_dir, write=True)

            self.assertEqual(result, 0)
            self.assertEqual(
                source_abs.read_bytes(),
                b"First [[intake/processed/example/complete-source]].\r\nSecond line.\r\n",
            )

    def test_cli_reports_expected_input_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            stderr = io.StringIO()
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = fix_truncated_links.main(
                    [
                        "--vault",
                        str(vault),
                        "--source-file",
                        "missing.md",
                        "--target-dir",
                        "targets",
                    ]
                )

            self.assertEqual(result, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("link fix failed: source file is not a file", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
