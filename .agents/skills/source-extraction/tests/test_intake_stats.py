import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import intake_stats


class TestIntakeStats(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_source(self, text: str) -> Path:
        path = self.root / "source.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_normal_file_is_quiet_by_default(self):
        path = self.write_source("# Overview\n\nShort source.\n")
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = intake_stats.main([str(path)])

        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "")

    def test_json_output_for_alert_is_flat_and_minimal(self):
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
            result = intake_stats.main([str(path), "--json", "--threshold", "1"])

        self.assertEqual(result, 0)
        stats = json.loads(stdout.getvalue())
        self.assertEqual(
            set(stats),
            {"schema", "path", "content_units", "heading_count", "sample_headings", "alerts"},
        )
        self.assertEqual(stats["schema"], 1)
        self.assertEqual(stats["heading_count"], 7)
        self.assertEqual(stats["sample_headings"], ["Overview", "One", "Two", "Three", "Four"])
        self.assertEqual(stats["alerts"], ["large_source"])

    def test_normal_file_is_quiet_in_json_mode(self):
        path = self.write_source("# Overview\n\nShort source.\n")
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = intake_stats.main([str(path), "--json"])

        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "")

    def test_large_file_warns_with_source_derived_heading_names(self):
        path = self.write_source("# Abschnitt 1: Überblick\n\n" + ("Body text.\n" * 20))
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = intake_stats.main([str(path), "--threshold", "10"])

        output = stdout.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("large_source:", output)
        self.assertIn("Abschnitt 1: Überblick", output)
        self.assertIn("source_headings: Abschnitt 1: Überblick", output)

    def test_setext_heading_names_are_detected(self):
        path = self.write_source("Source Title\n============\n\n" + ("Body text.\n" * 20))
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = intake_stats.main([str(path), "--threshold", "10"])

        output = stdout.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("source_headings: Source Title", output)

    def test_large_file_without_headings_reports_no_reliable_headings(self):
        path = self.write_source("Body text.\n" * 20)
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            result = intake_stats.main([str(path), "--threshold", "10"])

        output = stdout.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("large_source:", output)
        self.assertIn("no reliable Markdown headings detected", output)

    def test_missing_file_returns_error(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            result = intake_stats.main([str(self.root / "missing.md")])

        self.assertEqual(result, 2)
        self.assertIn("missing file:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
