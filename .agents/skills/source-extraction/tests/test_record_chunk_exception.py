import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import audit_chunks
import record_chunk_exception
from chunk_contract import parse_registry_text


INDEX_HEADER = "| 块 | 标题与覆盖范围 | 内容说明 | 规模与尺寸裁决 | 内容评审 |"
INDEX_SEPARATOR = "| --- | --- | --- | --- | --- |"


class TestRecordChunkException(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "chunks").mkdir()
        (self.root / "source.md").write_text(
            "# Source\n\nCanonical source text remains unchanged.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def prepare_leaf(
        self,
        *,
        text: str,
        status: str,
        reason: str,
        review: str = "reviewed",
        recorded_units: int | None = None,
    ) -> int:
        leaf = self.root / "chunks/01.md"
        leaf.write_text(text, encoding="utf-8")
        units = audit_chunks.content_units(text)
        shown_units = units if recorded_units is None else recorded_units
        decision = f"{shown_units} · {status}"
        if reason:
            decision += f" — {reason}"
        (self.root / "chunks/index.md").write_text(
            "# Chunks\n\n"
            f"{INDEX_HEADER}\n{INDEX_SEPARATOR}\n"
            f"| [01](01.md) | Terminology | — | {decision} | {review} |\n",
            encoding="utf-8",
        )
        return units

    def audit(self, minimum: int, maximum: int) -> tuple[int, dict]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = audit_chunks.main(
                [
                    str(self.root),
                    "--json",
                    "--min-threshold",
                    str(minimum),
                    "--threshold",
                    str(maximum),
                ]
            )
        return result, json.loads(stdout.getvalue())

    def test_records_valid_under_exception_and_is_idempotent(self):
        reason = "本章虽短但语义独立；并入后章会破坏章节边界。"
        self.prepare_leaf(
            text="# Terminology\n\nShort text.\n",
            status="accepted-under",
            reason=reason,
        )
        review_ref = "reviews/source-review/2026-08-25.md#chunk-01"

        first = record_chunk_exception.record_exception(
            self.root, "01.md", review_ref, 100, 1000
        )
        first_text = (self.root / "chunks/index.md").read_text(encoding="utf-8")
        second = record_chunk_exception.record_exception(
            self.root, "chunks/01.md", review_ref, 100, 1000
        )
        second_text = (self.root / "chunks/index.md").read_text(encoding="utf-8")
        result, stats = self.audit(100, 1000)

        self.assertEqual(first, "recorded")
        self.assertEqual(second, "unchanged")
        self.assertEqual(first_text, second_text)
        self.assertEqual(result, 0)
        self.assertEqual(stats["status"], "pass")
        self.assertEqual(len(stats["accepted_exceptions"]), 1)

    def test_reason_change_realerts_until_explicit_rerecord(self):
        old_reason = "旧理由。"
        new_reason = "新理由。"
        self.prepare_leaf(
            text="# Terminology\n\nShort text.\n",
            status="accepted-under",
            reason=old_reason,
        )
        review_ref = "reviews/source-review/2026-08-25.md#chunk-01"
        record_chunk_exception.record_exception(self.root, "01.md", review_ref, 100, 1000)
        index_path = self.root / "chunks/index.md"
        index_path.write_text(
            index_path.read_text(encoding="utf-8").replace(old_reason, new_reason),
            encoding="utf-8",
        )

        stale_result, stale_stats = self.audit(100, 1000)
        rerecorded = record_chunk_exception.record_exception(
            self.root, "01.md", review_ref, 100, 1000
        )
        final_result, final_stats = self.audit(100, 1000)

        self.assertEqual(stale_result, 0)
        self.assertIn("stale_chunk_exception", [item["code"] for item in stale_stats["warnings"]])
        self.assertEqual(rerecorded, "recorded")
        self.assertEqual(final_result, 0)
        self.assertEqual(final_stats["status"], "pass")

    def test_refuses_empty_normal_pending_and_size_mismatch(self):
        cases = (
            ("\n", "accepted-under", "Reason.", "reviewed", None, "empty"),
            ("# Terminology\n\n" + ("Reviewable body text. " * 30), "normal", "", "reviewed", None, "within"),
            ("# Terminology\n\nShort.\n", "accepted-under", "Reason.", "pending", None, "reviewed"),
            ("# Terminology\n\nShort.\n", "accepted-under", "Reason.", "reviewed", 999, "records"),
        )
        for text, status, reason, review, units, expected in cases:
            with self.subTest(expected=expected):
                (self.root / "chunks/index.md").unlink(missing_ok=True)
                (self.root / "chunks/01.md").unlink(missing_ok=True)
                self.prepare_leaf(
                    text=text,
                    status=status,
                    reason=reason,
                    review=review,
                    recorded_units=units,
                )
                with self.assertRaisesRegex(ValueError, expected):
                    record_chunk_exception.record_exception(
                        self.root,
                        "01.md",
                        "reviews/source-review/2026-08-25.md#chunk-01",
                        100,
                        1000,
                    )

    def test_remove_deletes_last_registry_block(self):
        reason = "独立短章。"
        self.prepare_leaf(
            text="# Terminology\n\nShort text.\n",
            status="accepted-under",
            reason=reason,
        )
        record_chunk_exception.record_exception(
            self.root,
            "01.md",
            "reviews/source-review/2026-08-25.md#chunk-01",
            100,
            1000,
        )

        outcome = record_chunk_exception.record_exception(
            self.root, "01.md", None, 100, 1000, remove=True
        )
        registry, problems = parse_registry_text(
            (self.root / "chunks/index.md").read_text(encoding="utf-8")
        )

        self.assertEqual(outcome, "removed")
        self.assertIsNone(registry)
        self.assertEqual(problems, [])

    def test_policy_change_requires_reviewing_registry_as_one_set(self):
        reason = "独立短章。"
        self.prepare_leaf(
            text="# Terminology\n\nShort text.\n",
            status="accepted-under",
            reason=reason,
        )
        review_ref = "reviews/source-review/2026-08-25.md#chunk-01"
        record_chunk_exception.record_exception(self.root, "01.md", review_ref, 100, 1000)

        with self.assertRaisesRegex(ValueError, "policy differs"):
            record_chunk_exception.record_exception(self.root, "01.md", review_ref, 200, 1000)

    def test_review_reference_must_be_vault_root_relative(self):
        self.prepare_leaf(
            text="# Terminology\n\nShort text.\n",
            status="accepted-under",
            reason="独立短章。",
        )

        for review_ref in (
            "../../reviews/source-review/2026-08-25.md#chunk-01",
            "reviews\\source-review\\2026-08-25.md#chunk-01",
            "notes/2026-08-25.md#chunk-01",
            "reviews/source-review/2026-08-25.md#",
        ):
            with self.subTest(review_ref=review_ref):
                with self.assertRaisesRegex(ValueError, "vault-root-relative"):
                    record_chunk_exception.record_exception(
                        self.root, "01.md", review_ref, 100, 1000
                    )

    def test_writer_rejects_noncanonical_uppercase_markdown_suffix(self):
        reason = "独立短章。"
        self.prepare_leaf(
            text="# Terminology\n\nShort text.\n",
            status="accepted-under",
            reason=reason,
        )
        leaf = self.root / "chunks/01.md"
        uppercase_leaf = self.root / "chunks/01.MD"
        leaf.rename(uppercase_leaf)
        index_path = self.root / "chunks/index.md"
        index_path.write_text(
            index_path.read_text(encoding="utf-8").replace("01.md", "01.MD"),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Markdown leaf"):
            record_chunk_exception.record_exception(
                self.root,
                "01.MD",
                "reviews/source-review/2026-08-25.md#chunk-01",
                100,
                1000,
            )

    def test_writer_ignores_fenced_registry_example_and_preserves_bom_crlf(self):
        reason = "独立短章。"
        self.prepare_leaf(
            text="# Terminology\n\nShort text.\n",
            status="accepted-under",
            reason=reason,
        )
        index_path = self.root / "chunks/index.md"
        raw = index_path.read_text(encoding="utf-8").rstrip() + (
            "\n\n```html\n"
            "<!-- chunk-size-exceptions\n"
            "{\"schema\": \"example only\"}\n"
            "-->\n"
            "```\n"
        )
        index_path.write_bytes(("\ufeff" + raw.replace("\n", "\r\n")).encode("utf-8"))

        outcome = record_chunk_exception.record_exception(
            self.root,
            "01.md",
            "reviews/source-review/2026-08-25.md#chunk-01",
            100,
            1000,
        )
        written = index_path.read_bytes()
        decoded = written.decode("utf-8")
        registry, problems = parse_registry_text(decoded)

        self.assertEqual(outcome, "recorded")
        self.assertTrue(written.startswith("\ufeff".encode("utf-8")))
        self.assertNotIn(b"\n", written.replace(b"\r\n", b""))
        self.assertIsNotNone(registry)
        self.assertEqual(problems, [])

    def test_cli_reports_contract_rejection_without_writing(self):
        self.prepare_leaf(
            text="# Terminology\n\nShort text.\n",
            status="undersized",
            reason="",
        )
        before = (self.root / "chunks/index.md").read_bytes()
        stderr = io.StringIO()
        with redirect_stderr(stderr), redirect_stdout(io.StringIO()):
            result = record_chunk_exception.main(
                [
                    str(self.root),
                    "--chunk",
                    "01.md",
                    "--review-ref",
                    "reviews/source-review/2026-08-25.md#chunk-01",
                    "--min-threshold",
                    "100",
                    "--threshold",
                    "1000",
                ]
            )

        self.assertEqual(result, 1)
        self.assertIn("must first use", stderr.getvalue())
        self.assertEqual((self.root / "chunks/index.md").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
