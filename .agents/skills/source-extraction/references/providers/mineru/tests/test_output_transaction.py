import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import api_parse
import fastapi_parse
import output_transaction as transaction


class Response:
    status_code = 200
    headers = {"content-type": "application/json"}
    def __init__(self, text):
        self.text = text
    def json(self):
        return {"md_content": self.text}


class OutputSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "out"
        self.source = self.root / "demo.pdf"
        self.source.write_bytes(b"fixture")

    def fastapi(self, text):
        return fastapi_parse.process_json_response(response=Response(text), output_dir=self.output,
            file_paths=[self.source], mode="sync", task_id="", backend="", parse_method="", keep_json_response=False)

    def public(self, text, image=False):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("full.md", text)
            if image:
                archive.writestr("images/figure.png", b"image")
        with patch.object(api_parse, "request_bytes", return_value=buffer.getvalue()):
            api_parse.process_results(output_dir=self.output, batch_id="fixture", file_specs=[
                {"path": self.source, "request": {"name": "demo.pdf", "data_id": "demo"}}],
                payload={}, items=[{"file_name": "demo.pdf", "data_id": "demo", "state": "done", "full_zip_url": "https://fixture.invalid/result"}],
                timeout=1, keep_result_zip=False, keep_all_extracted=False)

    def test_kept_json_response_has_one_owner_across_failure_and_success(self):
        for contents in (("", "# recovered"), ("# initial", "", "# recovered")):
            with self.subTest(contents=contents):
                self.output = self.root / str(len(contents))
                for content in contents:
                    results = fastapi_parse.process_json_response(response=Response(content), output_dir=self.output,
                        file_paths=[self.source], mode="sync", task_id="", backend="", parse_method="", keep_json_response=True)
                    self.assertEqual(results[0]["status"] == "completed", bool(content))
                self.assertEqual((self.output / "source.md").read_text(), "# recovered")
                owners = []
                for name in ("result.json", "batch.json", "last-failure.json"):
                    path = self.output / name
                    if path.exists() and "response.json" in json.loads(path.read_text()).get("owned_files", {}):
                        owners.append(name)
                self.assertEqual(owners, ["batch.json"])
                self.assertEqual(json.loads((self.output / "response.json").read_text())["md_content"], "# recovered")

    def test_conflict_does_not_discard_other_successful_source(self):
        class BatchResponse(Response):
            def json(self):
                return {"results": {"alpha.pdf": {"md_content": "# Alpha"}, "beta.pdf": {"md_content": "# Beta"}}}
        for conflict, other in (("alpha", "beta"), ("beta", "alpha")):
            with self.subTest(conflict=conflict):
                output = self.root / conflict
                (output / conflict).mkdir(parents=True)
                (output / conflict / "source.md").write_text("user content")
                with self.assertRaisesRegex(RuntimeError, "unowned output conflict"):
                    fastapi_parse.process_json_response(response=BatchResponse(""), output_dir=output,
                        file_paths=[self.root / "alpha.pdf", self.root / "beta.pdf"], mode="sync", task_id="", backend="", parse_method="", keep_json_response=False)
                self.assertEqual((output / conflict / "source.md").read_text(), "user content")
                self.assertEqual((output / other / "source.md").read_text(), "# " + other.capitalize())
                self.assertTrue(json.loads((output / "batch.json").read_text())["publication_errors"])

    def test_successful_rerun_removes_only_previously_owned_images(self):
        self.public("# first", image=True)
        (self.output / "images" / "user.png").write_bytes(b"keep")
        self.public("# second")
        self.assertEqual((self.output / "source.md").read_text(), "# second")
        self.assertFalse((self.output / "images/figure.png").exists())
        self.assertEqual((self.output / "images/user.png").read_bytes(), b"keep")

    def test_failed_rerun_preserves_successful_source_and_metadata(self):
        for provider in (self.fastapi, self.public):
            with self.subTest(provider=provider.__name__):
                provider("# previous")
                old_report = (self.output / "result.json").read_bytes()
                try:
                    provider("")
                except RuntimeError:
                    pass
                self.assertEqual((self.output / "source.md").read_text(), "# previous")
                self.assertEqual((self.output / "result.json").read_bytes(), old_report)
                self.assertTrue((self.output / "last-failure.json").is_file())

    def test_successful_retry_clears_owned_publication_failure_report(self):
        self.output.mkdir()
        conflict = self.output / "source.md"
        conflict.write_text("user content")
        with self.assertRaisesRegex(RuntimeError, "unowned output conflict"):
            self.fastapi("# first")
        self.assertTrue(json.loads((self.output / "batch.json").read_text())["publication_errors"])
        conflict.unlink()
        self.fastapi("# retry")
        report = json.loads((self.output / "batch.json").read_text())
        self.assertFalse(report["needs_review"])
        self.assertNotIn("publication_errors", report)
        self.assertEqual((self.output / "source.md").read_text(), "# retry")

    def test_success_without_batch_output_preserves_unowned_batch_report(self):
        self.output.mkdir()
        (self.output / "batch.json").write_text("unrelated report")
        self.fastapi("# success")
        self.assertEqual((self.output / "batch.json").read_text(), "unrelated report")

    def test_provider_and_publication_errors_are_both_reported(self):
        self.output.mkdir()
        (self.output / "source.md").write_text("user content")
        @transaction.staged_output
        def provider(*, output_dir, file_paths):
            (output_dir / "source.md").write_text("# staged")
            (output_dir / "result.json").write_text('{"status": "completed"}')
            raise RuntimeError("fixture provider failure")
        with self.assertRaisesRegex(RuntimeError, "provider failed: fixture provider failure; reporting/publication also failed:.*unowned output conflict"):
            provider(output_dir=self.output, file_paths=[self.source])

    def test_timeout_report_conflict_returns_failure_without_masking_timeout(self):
        self.output.mkdir()
        (self.output / "batch.json").write_text("unrelated report")
        stderr = io.StringIO()
        with patch.object(api_parse, "parse_env_file", return_value={}), patch.object(api_parse, "env_value", return_value=""), patch.object(api_parse, "create_upload_batch", return_value=("fixture", [])), patch.object(api_parse, "upload_files"), patch.object(api_parse, "poll_batch_until_terminal", side_effect=api_parse.BatchTimeoutError(batch_id="fixture", max_polls=1, items=[])), redirect_stderr(stderr):
            status = api_parse.main(["--file", str(self.source), "--output-dir", str(self.output), "--base-url", "https://fixture.invalid", "--env-file", str(self.root / "unused.env")])
        self.assertEqual(status, 1)
        self.assertIn("batch did not finish", stderr.getvalue())
        self.assertIn("unowned output conflict", stderr.getvalue())
        self.assertEqual((self.output / "batch.json").read_text(), "unrelated report")

    def test_zip_crc_failure_keeps_other_successful_batch_item(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("alpha/alpha.md", "# corrupt alpha")
            archive.writestr("beta/beta.md", "# valid beta")
        class ZipResponse:
            status_code = 200
            headers = {"content-type": "application/zip"}
            content = buffer.getvalue().replace(b"# corrupt alpha", b"# damaged alpha")
        results = fastapi_parse.process_zip_response(response=ZipResponse(), output_dir=self.output,
            file_paths=[self.root / "alpha.pdf", self.root / "beta.pdf"], mode="sync", task_id="", backend="", parse_method="", keep_result_zip=False, keep_all_extracted=False)
        self.assertEqual([item["status"] for item in results], ["failed", "completed"])
        self.assertIn("CRC", results[0]["error"])
        self.assertEqual((self.output / "beta/source.md").read_text(), "# valid beta")

    def test_case_collisions_fail_both_network_prechecks(self):
        files = [self.root / "alpha.pdf", self.root / "ALPHA.pdf"]
        with self.assertRaisesRegex(RuntimeError, "duplicate original base filename"):
            api_parse.require_unique_output_basenames(files)
        args = fastapi_parse.parse_args(["--file", "unused", "--output-dir", "unused"])
        with self.assertRaisesRegex(RuntimeError, "duplicate original base filename"):
            fastapi_parse.require_prechecks(args, files)

    def test_linked_platform_ancestor_does_not_reject_selected_root(self):
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda path: path == self.root or original(path)):
            self.fastapi("# success")
        self.assertEqual((self.output / "source.md").read_text(), "# success")

    def test_incomplete_backup_is_marked_and_leaves_outputs_unchanged(self):
        self.fastapi("# original")
        previous = {p.name: p.read_bytes() for p in self.output.iterdir() if p.is_file()}
        original = transaction.shutil.copy2
        count = 0
        def fail_copy(source, target):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("fixture backup failure")
            return original(source, target)
        with patch.object(transaction.shutil, "copy2", side_effect=fail_copy):
            with self.assertRaisesRegex(RuntimeError, "fixture backup failure"):
                self.fastapi("# new")
        self.assertEqual({name: (self.output / name).read_bytes() for name in previous}, previous)
        records = [json.loads(path.read_text()) for path in self.root.glob(".mineru-recovery-*/recovery.json")]
        self.assertTrue(any(record["phase"] == "preparing" for record in records))

    def test_unknown_conflict_preserves_bytes(self):
        self.output.mkdir()
        (self.output / "source.md").write_text("user content")
        with self.assertRaisesRegex(RuntimeError, "unowned output conflict.*source.md"):
            self.fastapi("# new")
        self.assertEqual((self.output / "source.md").read_text(), "user content")

    def test_modified_owned_file_is_not_overwritten(self):
        self.fastapi("# first")
        (self.output / "source.md").write_text("user edit")
        with self.assertRaisesRegex(RuntimeError, "modified owned output conflict"):
            self.fastapi("# second")
        self.assertEqual((self.output / "source.md").read_text(), "user edit")

    def test_replace_failure_restores_all_old_files(self):
        self.fastapi("# old")
        previous = {p.name: p.read_bytes() for p in self.output.iterdir() if p.is_file()}
        real_replace = os.replace
        count = 0
        def fail_second(source, target):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("fixture interruption")
            return real_replace(source, target)
        with patch.object(transaction.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(RuntimeError, "fixture interruption"):
                self.fastapi("# new")
        self.assertEqual({name: (self.output / name).read_bytes() for name in previous}, previous)
        self.assertTrue(json.loads((self.output / "batch.json").read_text())["publication_errors"])
        self.assertTrue(list(self.root.glob(".mineru-recovery-*/recovery.json")))

    def test_unsafe_owned_path_is_rejected(self):
        self.fastapi("# first")
        metadata = json.loads((self.output / "result.json").read_text())
        metadata["owned_files"]["../outside.md"] = "bad"
        (self.output / "result.json").write_text(json.dumps(metadata))
        with self.assertRaisesRegex(RuntimeError, "unsafe output path"):
            self.fastapi("# second")

    def test_linked_output_is_rejected(self):
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda path: path == self.output or original(path)):
            with self.assertRaisesRegex(RuntimeError, "linked output path"):
                self.fastapi("# new")
        self.assertFalse(self.output.exists())

    def test_zip_windows_paths_are_rejected(self):
        for path in ("../escape", "images\\..\\escape", "C:/escape", "images/file:stream"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(RuntimeError, "unsafe zip"):
                    api_parse.zip_member_path(path)


if __name__ == "__main__":
    unittest.main()
