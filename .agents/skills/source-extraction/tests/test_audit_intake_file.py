import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import audit_intake_file


class TestAuditIntakeFile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_source(self, text: str) -> Path:
        path = self.root / "source.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_content_unit_constant_is_used(self):
        self.assertEqual(audit_intake_file.CONTENT_UNIT_BYTES, 3)
        self.assertEqual(audit_intake_file.DEFAULT_LARGE_SOURCE_THRESHOLD, 10000)
        self.assertEqual(audit_intake_file.UNITS_ALGO, "utf8-normalized-ceil-div3-v1")
        self.assertEqual(
            audit_intake_file.normalize_markdown_text("\ufeffa\r\nb\rc\n"),
            "a\nb\nc\n",
        )
        self.assertEqual(audit_intake_file.content_units("abcd"), 2)

    def test_normal_file_is_quiet_by_default(self):
        path = self.write_source(
            "# Overview\n\nThis source contains enough substantive text for a reviewer to assess reliably.\n"
        )
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = audit_intake_file.main([str(path)])

        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "")

    def test_json_output_for_alert_uses_schema_two(self):
        path = self.write_source(
            "\n".join(
                [
                    "# Overview",
                    "Short source.",
                    "## One",
                    "## Two",
                    "## Three",
                    "## Four",
                    "## Five",
                    "## Six",
                ]
            )
        )
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = audit_intake_file.main([str(path), "--json", "--threshold", "1"])

        self.assertEqual(result, 0)
        stats = json.loads(stdout.getvalue())
        self.assertEqual(stats["schema"], 2)
        self.assertEqual(stats["status"], "warn")
        self.assertEqual(stats["thresholds"]["large_source"], 1)
        self.assertEqual(stats["thresholds"]["units_algo"], audit_intake_file.UNITS_ALGO)
        self.assertEqual(stats["heading_count"], 7)
        self.assertEqual(stats["sample_headings"], ["Overview", "One", "Two", "Three", "Four"])
        self.assertIn("large_source", [item["code"] for item in stats["warnings"]])
        self.assertGreaterEqual(stats["summary"]["warnings"], 1)

    def test_normal_file_always_returns_json_in_json_mode(self):
        path = self.write_source(
            "# Overview\n\nThis source contains enough substantive text for a reviewer to assess reliably.\n"
        )
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = audit_intake_file.main([str(path), "--json"])

        self.assertEqual(result, 0)
        stats = json.loads(stdout.getvalue())
        self.assertEqual(stats["status"], "pass")
        self.assertEqual(stats["errors"], [])
        self.assertEqual(stats["warnings"], [])

    def test_large_file_warns_with_source_derived_heading_names(self):
        path = self.write_source("# Abschnitt 1: Überblick\n\n" + ("Body text.\n" * 20))
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = audit_intake_file.main([str(path), "--threshold", "10"])

        output = stdout.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("large_source:", output)
        self.assertIn("Abschnitt 1: Überblick", output)
        self.assertIn("source_headings: Abschnitt 1: Überblick", output)

    def test_setext_heading_names_are_detected(self):
        path = self.write_source("Source Title\n============\n\n" + ("Body text.\n" * 20))
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = audit_intake_file.main([str(path), "--threshold", "10"])

        output = stdout.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("source_headings: Source Title", output)

    def test_frontmatter_closing_rule_is_not_reported_as_setext_heading(self):
        path = self.write_source(
            "---\n"
            "title: Captured Page\n"
            "url: https://example.com/page\n"
            "---\n\n"
            + ("Body paragraph without a Markdown heading. " * 10)
        )

        result, stats, _ = self.run_json(path, "--threshold", "10")

        self.assertEqual(result, 0)
        self.assertEqual(stats["heading_count"], 0)
        self.assertIn("no_headings", [item["code"] for item in stats["warnings"]])

    def test_large_file_without_headings_reports_no_reliable_headings(self):
        path = self.write_source("Body text.\n" * 20)
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = audit_intake_file.main([str(path), "--threshold", "10"])

        output = stdout.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("large_source:", output)
        self.assertIn("no reliable Markdown headings detected", output)

    def test_missing_file_returns_error(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            result = audit_intake_file.main([str(self.root / "missing.md")])

        self.assertEqual(result, 2)
        self.assertIn("missing file:", stderr.getvalue())

    def run_json(self, path: Path, *args: str) -> tuple[int, dict, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = audit_intake_file.main([str(path), "--json", *args])
        return result, json.loads(stdout.getvalue()), stderr.getvalue()

    def test_blank_source_is_hard_failure_without_cascade(self):
        path = self.write_source("\ufeff \r\n\t\r\n")

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 1)
        self.assertEqual(stats["status"], "fail")
        self.assertEqual([item["code"] for item in stats["errors"]], ["empty_source"])
        self.assertEqual(stats["warnings"], [])

    def test_image_only_source_has_no_reviewable_text(self):
        path = self.write_source("# Scans\n\n![](images/page-001.png)\n![[images/page-002.png]]\n")

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 1)
        self.assertEqual([item["code"] for item in stats["errors"]], ["no_reviewable_text"])

    def test_known_navigation_stub_is_hard_failure(self):
        path = self.write_source(
            "# source\n\n"
            "完整评审面已按标题语义分块（12 块），见 [chunks/index.md](chunks/index.md)。\n\n"
            "- 原始文件与提供方元数据：见 [[intake/processed placeholder|manifest]]（晋升后回填）\n"
        )

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 1)
        self.assertEqual([item["code"] for item in stats["errors"]], ["navigation_stub_source"])

    def test_known_navigation_stub_with_real_manifest_link_is_still_hard_failure(self):
        path = self.write_source(
            "# source\n\n"
            "完整评审面已按标题语义分块（12 块），见 [chunks/index.md](chunks/index.md)。\n\n"
            "- 原始文件与提供方元数据：见 [[manifest]]\n"
        )

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 1)
        self.assertEqual([item["code"] for item in stats["errors"]], ["navigation_stub_source"])

    def test_known_placeholder_is_hard_failure(self):
        path = self.write_source("# Extracted source\n\n[PLACEHOLDER: extraction pending]\n")

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 1)
        self.assertEqual([item["code"] for item in stats["errors"]], ["placeholder_source"])

    def test_table_code_and_math_are_reviewable_payload(self):
        fixtures = (
            "# Table\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n",
            "# Code\n\n```python\nprint('meaningful result')\n```\n",
            "# Math\n\n$$E = mc^2$$\n",
        )
        for index, text in enumerate(fixtures):
            with self.subTest(index=index):
                path = self.root / f"source-{index}.md"
                path.write_text(text, encoding="utf-8")
                result, stats, _ = self.run_json(path)
                self.assertEqual(result, 0)
                self.assertNotIn(
                    "no_reviewable_text",
                    [item["code"] for item in stats["errors"]],
                )

    def test_setext_heading_and_image_only_has_no_reviewable_text(self):
        path = self.write_source("Scanned pages\n=============\n\n![](images/page-001.png)\n")

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 1)
        self.assertEqual([item["code"] for item in stats["errors"]], ["no_reviewable_text"])

    def test_reference_and_html_image_only_sources_have_no_reviewable_text(self):
        fixtures = (
            "# Pages\n\n" + ("![page][scan]\n" * 7) + "\n[scan]: images/page.png\n",
            "# Pages\n\n" + ("<img src=\"images/page.png\" alt=\"page\">\n" * 7),
            "# Pages\n\n<picture>\n<source srcset=\"page.webp\">\n<img src=\"page.png\">\n</picture>\n",
        )
        for index, text in enumerate(fixtures):
            with self.subTest(index=index):
                path = self.root / f"image-only-{index}.md"
                path.write_text(text, encoding="utf-8")

                result, stats, _ = self.run_json(path)

                self.assertEqual(result, 1)
                self.assertEqual([item["code"] for item in stats["errors"]], ["no_reviewable_text"])

    def test_image_markup_with_real_text_remains_reviewable(self):
        path = self.write_source(
            "# Pages\n\n![page][scan]\n\n"
            "The accompanying analysis explains the observed result in enough detail for review.\n\n"
            "[scan]: images/page.png\n"
        )

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 0)
        self.assertNotIn("no_reviewable_text", [item["code"] for item in stats["errors"]])

    def test_fenced_html_example_counts_as_reviewable_code(self):
        path = self.write_source("# Example\n\n```html\n<img src=\"example.png\">\n```\n")

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 0)
        self.assertNotIn("no_reviewable_text", [item["code"] for item in stats["errors"]])

    def test_fenced_html_comment_counts_as_reviewable_code(self):
        path = self.write_source(
            "# Example\n\n````html\n```\n<!-- meaningful configuration marker -->\n````\n"
        )

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 0)
        self.assertNotIn("no_reviewable_text", [item["code"] for item in stats["errors"]])

    def test_sparse_source_is_warning_only(self):
        path = self.write_source("# Scope\n\nShort but meaningful.\n")

        result, stats, _ = self.run_json(path)

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "warn")
        self.assertIn("sparse_reviewable_text", [item["code"] for item in stats["warnings"]])

    def test_invalid_utf8_returns_machine_readable_input_error(self):
        path = self.root / "source.md"
        path.write_bytes(b"\xff\xfe\xfa")

        result, stats, stderr = self.run_json(path)

        self.assertEqual(result, 2)
        self.assertEqual(stats["status"], "fail")
        self.assertEqual([item["code"] for item in stats["errors"]], ["unreadable_input"])
        self.assertEqual(stderr, "")

    def test_json_mode_argument_errors_always_return_schema_two_json(self):
        cases = (
            ["--json", "--threshold", "not-an-integer"],
            ["--json"],
        )
        for args in cases:
            with self.subTest(args=args):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = audit_intake_file.main(args)

                stats = json.loads(stdout.getvalue())
                self.assertEqual(result, 2)
                self.assertEqual(stats["schema"], 2)
                self.assertEqual([item["code"] for item in stats["errors"]], ["invalid_arguments"])
                self.assertEqual(stderr.getvalue(), "")

    def test_missing_file_returns_machine_readable_input_error(self):
        result, stats, _ = self.run_json(self.root / "missing.md")

        self.assertEqual(result, 2)
        self.assertEqual([item["code"] for item in stats["errors"]], ["missing_input"])

    def test_invalid_threshold_returns_two(self):
        path = self.write_source("# Source\n\nReviewable body text.\n")

        result, stats, _ = self.run_json(path, "--threshold", "0")

        self.assertEqual(result, 2)
        self.assertEqual([item["code"] for item in stats["errors"]], ["invalid_threshold"])


if __name__ == "__main__":
    unittest.main()
