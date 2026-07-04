import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import audit_chunks


class TestAuditChunks(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write(self, relative_path: str, text: str = "Body\n") -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_json(self, *args: str) -> tuple[int, dict]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = audit_chunks.main([str(self.root), "--json", *args])
        return result, json.loads(stdout.getvalue())

    def test_missing_chunks_index_is_hard_failure(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        (self.root / "chunks").mkdir()

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertEqual(stats["status"], "fail")
        self.assertIn("missing_chunks_index", [item["code"] for item in stats["errors"]])

    def test_index_entries_must_resolve_inside_chunks(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [Missing](01-missing.md)\n- [Escape](../source.md)\n",
        )

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        codes = [item["code"] for item in stats["errors"]]
        self.assertIn("missing_index_target", codes)
        self.assertIn("index_target_outside_chunks", codes)

    def test_nested_index_entries_must_resolve(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Part](01-part/index.md)\n")
        self.write("chunks/01-part/index.md", "# Part\n\n- [Missing](01-missing.md)\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("missing_index_target", [item["code"] for item in stats["errors"]])

    def test_leaf_chunk_must_be_listed_in_nearest_index(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\nNo entries yet.\n")
        self.write("chunks/01-leaf.md", "# Leaf\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("leaf_not_listed_in_nearest_index", [item["code"] for item in stats["errors"]])

    def test_nested_chunk_directory_requires_local_index(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Part](01-part/index.md)\n")
        self.write("chunks/01-part/01-leaf.md", "# Leaf\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("missing_nested_index", [item["code"] for item in stats["errors"]])

    def test_oversized_leaf_requires_reason_in_nearest_index(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Part](01-part/index.md)\n")
        self.write("chunks/01-part/index.md", "# Part\n\n- [Large](01-large.md)\n")
        self.write("chunks/01-part/01-large.md", "# Large\n\n" + ("content\n" * 20))

        result, stats = self.run_json("--threshold", "10")

        self.assertEqual(result, 1)
        self.assertIn("oversized_chunk_without_reason", [item["code"] for item in stats["errors"]])

    def test_oversized_leaf_with_nearest_index_reason_passes(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Part](01-part/index.md)\n")
        self.write(
            "chunks/01-part/index.md",
            "# Part\n\n- [Large](01-large.md) - oversized: table cannot be split safely.\n",
        )
        self.write("chunks/01-part/01-large.md", "# Large\n\n" + ("content\n" * 20))

        result, stats = self.run_json("--threshold", "10")

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "pass")

    def test_unresolved_relative_image_is_warning_only(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Leaf](01-leaf.md)\n")
        self.write("chunks/01-leaf.md", "# Leaf\n\n![Figure](images/missing.png)\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "warn")
        self.assertIn("unresolved_local_image", [item["code"] for item in stats["warnings"]])

    def test_numbered_child_without_parent_is_warning_only(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Section](03-4.1-method.md)\n")
        self.write("chunks/03-4.1-method.md", "# 4.1 Method\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "warn")
        self.assertIn("possible_missing_numbered_parent", [item["code"] for item in stats["warnings"]])

    def test_repeated_source_heading_is_warning_only(self):
        self.write(
            "source.md",
            "# Contents\n\n## Module Alpha\n\n## Module Beta\n\n# Module Alpha\n\nBody\n",
        )
        self.write("chunks/index.md", "# Chunks\n\n- [Leaf](01-leaf.md)\n")
        self.write("chunks/01-leaf.md", "# Module Alpha\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "warn")
        self.assertIn("possible_repeated_source_heading", [item["code"] for item in stats["warnings"]])

    def test_final_metadata_before_passing_chunk_audit_is_hard_failure(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("summary.md", "Accepted summary.\n")
        self.write("manifest.md", "Accepted manifest.\n")
        (self.root / "chunks").mkdir()

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("final_metadata_before_chunk_audit_passed", [item["code"] for item in stats["errors"]])


if __name__ == "__main__":
    unittest.main()
