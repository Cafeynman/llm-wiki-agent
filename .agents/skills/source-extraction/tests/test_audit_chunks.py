import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import audit_chunks


INDEX_HEADER = "| 块 | 标题与覆盖范围 | 内容说明 | 规模与尺寸裁决 | 内容评审 |"
INDEX_SEPARATOR = "| --- | --- | --- | --- | --- |"
LINK_RE = re.compile(r"^- \[([^]]+)\]\(([^)]+)\)(?:\s*-\s*(.*))?$")


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

    def write_raw(self, relative_path: str, text: str) -> Path:
        return self.write(relative_path, text)

    def write_index(self, relative_path: str, rows: list[tuple[str, str, str, str, str]]) -> Path:
        lines = ["# Chunks", "", INDEX_HEADER, INDEX_SEPARATOR]
        lines.extend(
            f"| [{Path(target).stem}]({target}) | {title} | {description} | {decision} | {review} |"
            for target, title, description, decision, review in rows
        )
        return self.write(relative_path, "\n".join(lines) + "\n")

    def canonicalize_indexes(self, minimum: int, maximum: int) -> None:
        for index_path in sorted((self.root / "chunks").rglob("index.md")):
            text = index_path.read_text(encoding="utf-8")
            if INDEX_HEADER in text or not text.strip():
                continue
            rows = []
            for line in text.splitlines():
                match = LINK_RE.match(line.strip())
                if not match:
                    continue
                label, target, trailing = match.groups()
                resolved = index_path.parent / target
                if target.endswith("index.md"):
                    decision = "— · group"
                elif resolved.is_file():
                    units = audit_chunks.content_units(resolved.read_text(encoding="utf-8"))
                    status = "undersized" if units < minimum else "oversized" if units > maximum else "normal"
                    decision = f"{units} · {status}"
                    if trailing and "oversized:" in trailing.lower():
                        reason = trailing.split(":", 1)[1].strip().rstrip(".")
                        decision = f"{units} · accepted-over — {reason}"
                else:
                    decision = "0 · normal"
                rows.append((target, label, "—", decision, "pending"))
            if rows:
                self.write_index(str(index_path.relative_to(self.root)), rows)

    def run_json(self, *args: str) -> tuple[int, dict]:
        minimum = 1
        maximum = 10000
        args_list = list(args)
        if "--min-threshold" in args_list:
            minimum = int(args_list[args_list.index("--min-threshold") + 1])
        else:
            args_list.extend(["--min-threshold", str(minimum)])
        if "--threshold" in args_list:
            maximum = int(args_list[args_list.index("--threshold") + 1])
        self.canonicalize_indexes(minimum, maximum)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = audit_chunks.main([str(self.root), "--json", *args_list])
        return result, json.loads(stdout.getvalue())

    def test_missing_chunks_index_is_hard_failure(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        (self.root / "chunks").mkdir()

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertEqual(stats["status"], "fail")
        self.assertIn("missing_chunks_index", [item["code"] for item in stats["errors"]])

    def test_missing_canonical_source_is_hard_failure(self):
        self.write("chunks/01.md", "# Scope\n\nBody.\n")
        units = audit_chunks.content_units((self.root / "chunks/01.md").read_text(encoding="utf-8"))
        self.write_index(
            "chunks/index.md",
            [("01.md", "Scope", "—", f"{units} · normal", "pending")],
        )

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("missing_source", [item["code"] for item in stats["errors"]])

    def test_chunk_audit_rechecks_current_source_reviewability(self):
        self.write(
            "source.md",
            "# source\n\n"
            "完整评审面已按标题语义分块（1 块），见 [chunks/index.md](chunks/index.md)。\n\n"
            "- 原始文件与提供方元数据：见 [[manifest]]\n",
        )
        self.write("chunks/01.md", "# Scope\n\nBody.\n")
        units = audit_chunks.content_units((self.root / "chunks/01.md").read_text(encoding="utf-8"))
        self.write_index(
            "chunks/index.md",
            [("01.md", "Scope", "—", f"{units} · normal", "pending")],
        )

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("navigation_stub_source", [item["code"] for item in stats["errors"]])

    def test_index_entries_must_resolve_inside_chunks(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [Leaf](01.md)\n- [Missing](02.md)\n- [Escape](../source.md)\n",
        )
        self.write("chunks/01.md", "# Leaf\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        codes = [item["code"] for item in stats["errors"]]
        self.assertIn("missing_index_target", codes)
        self.assertIn("index_target_outside_chunks", codes)

    def test_nested_index_entries_must_resolve(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Part](01/index.md)\n")
        self.write("chunks/01/index.md", "# Part\n\n- [Leaf](01.md)\n- [Missing](02.md)\n")
        self.write("chunks/01/01.md", "# Leaf\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("missing_index_target", [item["code"] for item in stats["errors"]])

    def test_leaf_chunk_must_be_listed_in_nearest_index(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\nNo entries yet.\n")
        self.write("chunks/01.md", "# Leaf\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("leaf_not_listed_in_nearest_index", [item["code"] for item in stats["errors"]])

    def test_nested_chunk_directory_requires_local_index(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Part](01/index.md)\n")
        self.write("chunks/01/01.md", "# Leaf\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("missing_nested_index", [item["code"] for item in stats["errors"]])

    def test_oversized_leaf_requires_accepted_exception(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Part](01/index.md)\n")
        self.write("chunks/01/index.md", "# Part\n\n- [Large](01.md)\n")
        self.write("chunks/01/01.md", "# Large\n\n" + ("content\n" * 20))

        result, stats = self.run_json("--threshold", "10")

        self.assertEqual(result, 1)
        self.assertIn("oversized_chunk_without_exception", [item["code"] for item in stats["errors"]])

    def test_visible_reviewed_over_acceptance_is_persistent(self):
        text = "# Large\n\n" + ("content\n" * 20)
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [
                (
                    "01.md",
                    "Large",
                    "—",
                    f"{units} · accepted-over — table cannot be split safely",
                    "reviewed",
                )
            ],
        )

        result, stats = self.run_json("--threshold", "10")

        self.assertEqual(result, 0, stats)
        self.assertEqual(stats["status"], "pass")
        self.assertEqual(
            stats["accepted_exceptions"],
            [
                {
                    "path": "01.md",
                    "kind": "over",
                    "content_units": units,
                    "reason": "table cannot be split safely",
                }
            ],
        )

    def test_unresolved_relative_image_is_warning_only(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Leaf](01.md)\n")
        self.write("chunks/01.md", "# Leaf\n\nReviewable figure discussion.\n\n![Figure](images/missing.png)\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "warn")
        self.assertIn("unresolved_local_image", [item["code"] for item in stats["warnings"]])

    def test_numbered_child_without_parent_is_warning_only(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Section 4.1 Method](01.md)\n")
        self.write("chunks/01.md", "# 4.1 Method\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "warn")
        self.assertIn("possible_missing_numbered_parent", [item["code"] for item in stats["warnings"]])

    def test_repeated_source_heading_is_warning_only(self):
        self.write(
            "source.md",
            "# Contents\n\n## Module Alpha\n\n## Module Beta\n\n# Module Alpha\n\nBody\n",
        )
        self.write("chunks/index.md", "# Chunks\n\n- [Module Alpha](01.md)\n")
        self.write("chunks/01.md", "# Module Alpha\n\nBody\n")

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

    def test_source_titles_are_kept_in_content_not_paths(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [第一章: 总则/A?](01.md)\n- [第二章 * 范围](02.md)\n",
        )
        self.write("chunks/01.md", "# 第一章: 总则/A?\n\nBody\n")
        self.write("chunks/02.md", "# 第二章 * 范围\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "pass")

    def test_non_numeric_chunk_paths_fail(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [Overview](overview.md)\n- [Scope](02-scope.md)\n",
        )
        self.write("chunks/overview.md", "# Overview\n\nBody\n")
        self.write("chunks/02-scope.md", "# Scope\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn(
            "invalid_chunk_path_component",
            [item["code"] for item in stats["errors"]],
        )

    def test_chunk_leaf_suffix_must_be_exact_lowercase_md(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.MD", "# Scope\n\nBody.\n")
        units = audit_chunks.content_units((self.root / "chunks/01.MD").read_text(encoding="utf-8"))
        self.write_index(
            "chunks/index.md",
            [("01.MD", "Scope", "—", f"{units} · normal", "pending")],
        )

        stats = audit_chunks.inspect_chunks(self.root, 1, 1000)

        self.assertIn("invalid_chunk_markdown_suffix", [item["code"] for item in stats["errors"]])

    def test_numeric_chunk_paths_form_one_sequence(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [Overview](01.md)\n- [Scope](02.md)\n",
        )
        self.write("chunks/01.md", "# Overview\n\nBody\n")
        self.write("chunks/02.md", "# Scope\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "pass")

    def test_gapped_numeric_chunk_paths_fail(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [Overview](01.md)\n- [Scope](03.md)\n",
        )
        self.write("chunks/01.md", "# Overview\n\nBody\n")
        self.write("chunks/03.md", "# Scope\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn(
            "non_sequential_chunk_path_components",
            [item["code"] for item in stats["errors"]],
        )

    def test_file_and_directory_share_one_sibling_sequence(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [Part](01/index.md)\n- [Appendix](02.md)\n",
        )
        self.write(
            "chunks/01/index.md",
            "# Part\n\n- [First](01.md)\n- [Second](02.md)\n",
        )
        self.write("chunks/01/01.md", "# First\n\nBody\n")
        self.write("chunks/01/02.md", "# Second\n\nBody\n")
        self.write("chunks/02.md", "# Appendix\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "pass")

    def test_file_and_directory_cannot_reuse_one_ordinal(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [Part](01/index.md)\n- [Appendix](01.md)\n",
        )
        self.write("chunks/01/index.md", "# Part\n")
        self.write("chunks/01.md", "# Appendix\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn(
            "non_sequential_chunk_path_components",
            [item["code"] for item in stats["errors"]],
        )

    def test_noncanonical_numeric_padding_fails(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        self.write("chunks/index.md", "# Chunks\n\n- [Only](001.md)\n")
        self.write("chunks/001.md", "# Only\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn(
            "invalid_chunk_path_component",
            [item["code"] for item in stats["errors"]],
        )

    def test_numeric_sequence_continues_from_99_to_100(self):
        self.write("source.md", "# Source\n\nSee [chunks](chunks/index.md).\n")
        entries = []
        for ordinal in range(1, 100):
            name = f"{ordinal:02d}"
            entries.append(f"- [Section {ordinal} Topic]({name}.md)")
            self.write(f"chunks/{name}.md", f"# Section {ordinal} Topic\n\nBody\n")
        entries.append("- [Section 100](100/index.md)")
        self.write("chunks/index.md", "# Chunks\n\n" + "\n".join(entries) + "\n")
        self.write("chunks/100/index.md", "# Section 100\n")
        self.write("chunks/100/01.md", "# Section 100 Detail\n\nBody\n")
        self.write("chunks/100/index.md", "# Section 100\n\n- [Detail](01.md)\n")

        result, stats = self.run_json()

        self.assertEqual(result, 0, stats)
        self.assertEqual(stats["status"], "pass")

    def test_empty_chunk_tree_is_one_primary_hard_failure(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/index.md", "")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertEqual([item["code"] for item in stats["errors"]], ["empty_chunk_tree"])

    def test_empty_root_index_with_leaf_is_hard_failure(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/index.md", "")
        self.write("chunks/01.md", "# Scope\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("empty_root_index", [item["code"] for item in stats["errors"]])

    def test_valid_root_table_without_targets_is_hard_failure(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/index.md", f"# Chunks\n\n{INDEX_HEADER}\n{INDEX_SEPARATOR}\n")
        self.write("chunks/01.md", "# Scope\n\nBody\n")

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("root_index_without_chunk_targets", [item["code"] for item in stats["errors"]])

    def test_group_decision_and_nested_index_target_must_agree(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", "# Scope\n\nBody.\n")
        self.write("chunks/02/index.md", "# Part\n\n" + INDEX_HEADER + "\n" + INDEX_SEPARATOR + "\n")
        leaf_units = audit_chunks.content_units((self.root / "chunks/01.md").read_text(encoding="utf-8"))
        self.write_index(
            "chunks/index.md",
            [
                ("01.md", "Scope", "—", "— · group", "pending"),
                ("02/index.md", "Part", "—", f"{leaf_units} · normal", "pending"),
            ],
        )

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        group_errors = [item for item in stats["errors"] if item["code"] == "invalid_chunk_group_decision"]
        self.assertEqual(len(group_errors), 2)

    def test_group_decision_rejects_self_and_non_direct_nested_index(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01/01/01.md", "# Deep leaf\n\nBody.\n")
        units = audit_chunks.content_units((self.root / "chunks/01/01/01.md").read_text(encoding="utf-8"))
        self.write_index(
            "chunks/index.md",
            [
                ("index.md", "Self", "—", "— · group", "pending"),
                ("01/01/index.md", "Deep", "—", "— · group", "pending"),
            ],
        )
        self.write_index(
            "chunks/01/index.md",
            [("01/index.md", "Deep", "—", "— · group", "pending")],
        )
        self.write_index(
            "chunks/01/01/index.md",
            [("01.md", "Deep leaf", "—", f"{units} · normal", "pending")],
        )

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        group_errors = [item for item in stats["errors"] if item["code"] == "invalid_chunk_group_decision"]
        self.assertEqual(len(group_errors), 2)

    def test_nested_asset_directories_are_not_treated_as_chunk_paths(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/images/icons/logo.png", "binary placeholder")
        self.write("chunks/01.md", "# Scope\n\nBody.\n")
        units = audit_chunks.content_units((self.root / "chunks/01.md").read_text(encoding="utf-8"))
        self.write_index(
            "chunks/index.md",
            [("01.md", "Scope", "—", f"{units} · normal", "pending")],
        )

        result, stats = self.run_json()

        self.assertEqual(result, 0, stats)
        self.assertNotIn("invalid_chunk_path_component", [item["code"] for item in stats["errors"]])

    def test_size_decision_grammar_rejects_noncanonical_spacing(self):
        for decision in ("7·normal", "—·group"):
            with self.subTest(decision=decision):
                self.temp_dir.cleanup()
                self.temp_dir = tempfile.TemporaryDirectory()
                self.root = Path(self.temp_dir.name)
                self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
                self.write("chunks/01.md", "# Scope\n\nBody.\n")
                self.write_index(
                    "chunks/index.md",
                    [("01.md", "Scope", "—", decision, "pending")],
                )

                result, stats = self.run_json()

                self.assertEqual(result, 1)
                self.assertIn("invalid_chunk_size_decision", [item["code"] for item in stats["errors"]])

    def test_accepted_size_without_reason_reports_only_its_primary_error(self):
        text = "# Shared table\n\n" + ("content\n" * 20)
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Shared table", "—", f"{units} · accepted-over", "reviewed")],
        )

        result, stats = self.run_json("--min-threshold", "1", "--threshold", "10")

        self.assertEqual(result, 1)
        self.assertEqual(
            [item["code"] for item in stats["errors"]],
            ["invalid_chunk_size_decision"],
        )
        self.assertEqual(stats["warnings"], [])

    def test_default_threshold_boundaries_are_exact(self):
        def text_with_units(units: int, title: str) -> str:
            prefix = f"# {title}\n\n"
            remaining = units * 3 - len(prefix.encode("utf-8"))
            self.assertGreaterEqual(remaining, 0)
            return prefix + ("a" * remaining)

        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        cases = (
            ("01.md", 1999, "Boundary 1999", "undersized"),
            ("02.md", 2000, "Boundary 2000", "normal"),
            ("03.md", 10000, "Boundary 10000", "normal"),
            ("04.md", 10001, "Boundary 10001", "oversized"),
        )
        rows = []
        for target, units, title, status in cases:
            text = text_with_units(units, title)
            self.assertEqual(audit_chunks.content_units(text), units)
            self.write(f"chunks/{target}", text)
            rows.append((target, title, "—", f"{units} · {status}", "pending"))
        self.write_index("chunks/index.md", rows)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = audit_chunks.main([str(self.root), "--json"])
        stats = json.loads(stdout.getvalue())

        self.assertEqual(result, 1)
        self.assertEqual(stats["thresholds"]["min"], 2000)
        self.assertEqual(stats["thresholds"]["max"], 10000)
        self.assertEqual(
            [(item["code"], item["path"]) for item in stats["warnings"]],
            [("undersized_chunk_without_exception", "chunks/01.md")],
        )
        self.assertIn(
            ("oversized_chunk_without_exception", "chunks/04.md"),
            [(item["code"], item["path"]) for item in stats["errors"]],
        )
        self.assertNotIn("index_size_mismatch", [item["code"] for item in stats["warnings"]])

    def test_empty_leaf_is_hard_failure_and_cannot_be_excepted(self):
        reason = "本块在原文中语义独立。"
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", "\ufeff\r\n\r\n")
        self.write_index(
            "chunks/index.md",
            [("01.md", "Empty", "—", f"0 · accepted-under — {reason}", "reviewed")],
        )

        result, stats = self.run_json("--min-threshold", "100", "--threshold", "1000")

        self.assertEqual(result, 1)
        self.assertIn("empty_leaf_chunk", [item["code"] for item in stats["errors"]])
        self.assertEqual(stats["accepted_exceptions"], [])

    def test_image_only_leaf_is_hard_failure_even_when_images_resolve(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/images/page.png", "binary placeholder")
        text = "# Scans\n\n" + ("![page](images/page.png)\n" * 400)
        self.write("chunks/01.md", text)
        units = audit_chunks.content_units(text)
        status = "undersized" if units < 2000 else "normal"
        self.write_index(
            "chunks/index.md",
            [("01.md", "Scans", "—", f"{units} · {status}", "pending")],
        )

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("no_reviewable_leaf_content", [item["code"] for item in stats["errors"]])

    def test_leaf_without_descriptive_heading_is_hard_failure(self):
        text = "Body without a Markdown heading but with enough reviewable content.\n"
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Scope", "—", f"{units} · normal", "pending")],
        )

        result, stats = self.run_json()

        self.assertEqual(result, 1)
        self.assertIn("chunk_without_descriptive_heading", [item["code"] for item in stats["errors"]])

    def test_every_undersized_leaf_warns_without_semantic_guessing(self):
        text = "# Independent terminology chapter\n\nShort text.\n"
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Independent terminology chapter", "—", f"{units} · undersized", "pending")],
        )

        result, stats = self.run_json("--min-threshold", "100")

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "warn")
        self.assertIn("undersized_chunk_without_exception", [item["code"] for item in stats["warnings"]])

    def test_valid_under_exception_suppresses_repeat_warning(self):
        reason = "本章虽短但语义独立；并入后章会破坏章节边界。"
        text = "# Terminology\r\n\r\nShort text.\r\n"
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        leaf = self.root / "chunks/01.md"
        leaf.parent.mkdir(parents=True, exist_ok=True)
        leaf.write_bytes(("\ufeff" + text).encode("utf-8"))
        self.write_index(
            "chunks/index.md",
            [("01.md", "Terminology", "—", f"{units} · accepted-under — {reason}", "reviewed")],
        )

        result, stats = self.run_json("--min-threshold", "100", "--threshold", "1000")

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "pass")
        self.assertEqual(stats["errors"], [])
        self.assertEqual(stats["warnings"], [])
        self.assertEqual(len(stats["accepted_exceptions"]), 1)
        self.assertEqual(stats["accepted_exceptions"][0]["path"], "01.md")
        self.assertEqual(stats["accepted_exceptions"][0]["reason"], reason)

    def test_under_acceptance_requires_reviewed_status(self):
        reason = "本章虽短但语义独立。"
        text = "# Terminology\n\nShort text.\n"
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Terminology", "—", f"{units} · accepted-under — {reason}", "pending")],
        )

        result, stats = self.run_json("--min-threshold", "100", "--threshold", "1000")

        self.assertEqual(result, 1)
        self.assertEqual(
            [item["code"] for item in stats["errors"]],
            ["accepted_size_requires_review"],
        )
        self.assertEqual(stats["warnings"], [])
        self.assertEqual(stats["accepted_exceptions"], [])

    def test_over_acceptance_requires_reviewed_status(self):
        reason = "连续表格不可拆。"
        text = "# Shared table\n\n" + ("content\n" * 20)
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Shared table", "—", f"{units} · accepted-over — {reason}", "pending")],
        )

        result, stats = self.run_json("--min-threshold", "1", "--threshold", "10")

        self.assertEqual(result, 1)
        self.assertEqual(
            [item["code"] for item in stats["errors"]],
            ["accepted_size_requires_review"],
        )
        self.assertEqual(stats["warnings"], [])
        self.assertEqual(stats["accepted_exceptions"], [])

    def test_accepted_status_must_match_recomputed_size_category(self):
        reason = "错误类别不应被接受。"
        text = "# Terminology\n\nShort text.\n"
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Terminology", "—", f"{units} · accepted-over — {reason}", "reviewed")],
        )

        result, stats = self.run_json("--min-threshold", "100", "--threshold", "1000")

        self.assertEqual(result, 1)
        self.assertEqual(
            [item["code"] for item in stats["errors"]],
            ["accepted_size_category_mismatch"],
        )
        self.assertEqual(stats["warnings"], [])
        self.assertEqual(stats["accepted_exceptions"], [])

    def test_valid_over_exception_suppresses_hard_error(self):
        reason = "连续表格共用表头和脚注，拆分后无法独立解释。"
        text = "# Shared table\n\n" + ("| A | B |\n| --- | --- |\n| 1 | 2 |\n" * 20)
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Shared table", "—", f"{units} · accepted-over — {reason}", "reviewed")],
        )

        result, stats = self.run_json("--min-threshold", "1", "--threshold", "10")

        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "pass")
        self.assertEqual(stats["errors"], [])
        self.assertEqual(stats["warnings"], [])
        self.assertEqual(len(stats["accepted_exceptions"]), 1)
        self.assertEqual(stats["accepted_exceptions"][0]["reason"], reason)

    def test_accepted_decision_requires_current_recomputed_units(self):
        reason = "连续表格不可拆。"
        text = "# Shared table\n\n" + ("content\n" * 20)
        units = audit_chunks.content_units(text)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Shared table", "—", f"{units - 1} · accepted-over — {reason}", "reviewed")],
        )

        result, stats = self.run_json("--min-threshold", "1", "--threshold", "10")

        self.assertEqual(result, 1)
        self.assertEqual(
            [item["code"] for item in stats["errors"]],
            ["accepted_size_measurement_mismatch"],
        )
        self.assertEqual(stats["warnings"], [])
        self.assertEqual(stats["accepted_exceptions"], [])

    def test_legacy_free_text_reason_is_migration_candidate_not_acceptance(self):
        text = "# Large table\n\n" + ("content\n" * 20)
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write(
            "chunks/index.md",
            "# Chunks\n\n- [Large table](01.md) - oversized: legacy reason.\n",
        )

        stats = audit_chunks.inspect_chunks(self.root, 1, 10)

        self.assertIn("legacy_chunk_index_format", [item["code"] for item in stats["errors"]])
        self.assertIn("oversized_chunk_without_exception", [item["code"] for item in stats["errors"]])

    def test_index_size_mismatch_is_warning(self):
        text = "# Scope\n\nBody with enough content.\n"
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", text)
        self.write_index(
            "chunks/index.md",
            [("01.md", "Scope", "—", "999 · normal", "pending")],
        )

        result, stats = self.run_json()

        self.assertEqual(result, 0)
        self.assertIn("index_size_mismatch", [item["code"] for item in stats["warnings"]])

    def test_output_is_deterministic(self):
        self.write("source.md", "# Source\n\nCanonical source text remains here.\n")
        self.write("chunks/01.md", "# One\n\nBody\n")
        self.write("chunks/02.md", "# Two\n\nBody\n")
        self.write_index(
            "chunks/index.md",
            [
                ("01.md", "One", "—", "999 · normal", "pending"),
                ("02.md", "Two", "—", "999 · normal", "pending"),
            ],
        )

        first_result, first = self.run_json()
        second_result, second = self.run_json()

        self.assertEqual(first_result, second_result)
        self.assertEqual(first, second)

    def test_json_mode_argument_errors_always_return_schema_two_json(self):
        cases = (
            ["--json", "--threshold", "not-an-integer"],
            ["--json"],
        )
        for args in cases:
            with self.subTest(args=args):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    result = audit_chunks.main(args)

                stats = json.loads(stdout.getvalue())
                self.assertEqual(result, 2)
                self.assertEqual(stats["schema"], 2)
                self.assertEqual([item["code"] for item in stats["errors"]], ["invalid_arguments"])


if __name__ == "__main__":
    unittest.main()
