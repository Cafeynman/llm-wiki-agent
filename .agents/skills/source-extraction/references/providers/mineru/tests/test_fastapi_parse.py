import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch


scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import fastapi_parse


class FakeResponse:
    def __init__(self, *, status_code=200, headers=None, content=b"", json_payload=None, text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        self._json_payload = json_payload
        self.text = text

    def json(self):
        if self._json_payload is None:
            raise ValueError("no json")
        return self._json_payload


class PostSequence:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, *, data=None, files=None, headers=None, timeout=0):
        self.calls.append({"url": url, "data": list(data or []), "files": files, "headers": headers or {}, "timeout": timeout})
        if not self.responses:
            raise AssertionError("No more POST responses configured")
        return self.responses.pop(0)


class GetSequence:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, *, headers=None, timeout=0):
        self.calls.append({"url": url, "headers": headers or {}, "timeout": timeout})
        if not self.responses:
            raise AssertionError("No more GET responses configured")
        return self.responses.pop(0)


class TestFastApiParse(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_env(self, text: str = "MINERU_FASTAPI_BASE_URL=https://mineru.local\n") -> Path:
        path = self.root / ".env"
        path.write_text(text, encoding="utf-8")
        return path

    def write_file(self, name: str, content: bytes = b"pdf") -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def build_zip_bytes(self, members: dict[str, str | bytes]) -> bytes:
        zip_path = self.root / "fixture.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in members.items():
                zf.writestr(name, content)
        return zip_path.read_bytes()

    def test_sync_zip_response_writes_source_full_and_images(self):
        env_path = self.write_env()
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        zip_bytes = self.build_zip_bytes(
            {
                "demo/vlm-engine_auto/demo.md": "# Demo\n![](images/a.png)\n",
                "demo/vlm-engine_auto/images/a.png": b"image",
            }
        )
        post_sequence = PostSequence(
            [FakeResponse(headers={"content-type": "application/zip"}, content=zip_bytes)]
        )

        with patch("fastapi_parse.requests.post", post_sequence):
            result = fastapi_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--backend",
                    "vlm-engine",
                    "--lang-list",
                    "en",
                    "--formula-enable",
                    "--table-enable",
                    "--return-md",
                    "--return-images",
                    "--response-format-zip",
                ]
            )

        self.assertEqual(result, 0)
        self.assertTrue(post_sequence.calls[0]["url"].endswith("/file_parse"))
        self.assertIn(("backend", "vlm-engine"), post_sequence.calls[0]["data"])
        self.assertIn(("return_images", "true"), post_sequence.calls[0]["data"])
        self.assertIn(("lang_list", "en"), post_sequence.calls[0]["data"])
        self.assertEqual((output_dir / "source.md").read_text(encoding="utf-8"), "# Demo\n![](images/a.png)\n")
        self.assertTrue((output_dir / "full.md").exists())
        self.assertTrue((output_dir / "images" / "a.png").exists())
        self.assertFalse((output_dir / "result.zip").exists())
        metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["profile_id"], "fastapi")
        self.assertEqual(metadata["backend"], "vlm-engine")

    def test_async_task_polls_and_downloads_zip_result(self):
        env_path = self.write_env()
        input_file = self.write_file("paper.pdf")
        output_dir = self.root / "out"
        zip_bytes = self.build_zip_bytes({"paper/vlm-engine_auto/paper.md": "# Paper\n"})
        post_sequence = PostSequence([FakeResponse(status_code=202, json_payload={"task_id": "task-1", "status": "pending"})])
        get_sequence = GetSequence(
            [
                FakeResponse(json_payload={"task_id": "task-1", "status": "completed"}),
                FakeResponse(headers={"content-type": "application/zip"}, content=zip_bytes),
            ]
        )

        with patch("fastapi_parse.requests.post", post_sequence), patch("fastapi_parse.requests.get", get_sequence), patch(
            "fastapi_parse.time.sleep", lambda _: None
        ):
            result = fastapi_parse.main(
                [
                    "--mode",
                    "async",
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--backend",
                    "vlm-engine",
                    "--poll-interval",
                    "0.01",
                    "--max-wait",
                    "1",
                ]
            )

        self.assertEqual(result, 0)
        self.assertTrue(post_sequence.calls[0]["url"].endswith("/tasks"))
        self.assertTrue(get_sequence.calls[0]["url"].endswith("/tasks/task-1"))
        self.assertTrue(get_sequence.calls[1]["url"].endswith("/tasks/task-1/result"))
        self.assertEqual((output_dir / "source.md").read_text(encoding="utf-8"), "# Paper\n")
        batch_metadata = json.loads((output_dir / "batch.json").read_text(encoding="utf-8"))
        self.assertEqual(batch_metadata["task_id"], "task-1")

    def test_json_response_writes_markdown_and_optional_response_json(self):
        env_path = self.write_env()
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        post_sequence = PostSequence(
            [
                FakeResponse(
                    headers={"content-type": "application/json"},
                    json_payload={
                        "task_id": "sync-task",
                        "status": "completed",
                        "results": {
                            "demo.pdf": {
                                "md_content": "# JSON Demo\n",
                                "content_list": [{"type": "text"}],
                            }
                        },
                    },
                )
            ]
        )

        with patch("fastapi_parse.requests.post", post_sequence):
            result = fastapi_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--keep-json-response",
                ]
            )

        self.assertEqual(result, 0)
        self.assertEqual((output_dir / "source.md").read_text(encoding="utf-8"), "# JSON Demo\n")
        self.assertTrue((output_dir / "response.json").exists())
        metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["content_list_count"], 1)

    def test_batch_zip_response_writes_per_original_base_name_and_cleans_root_outputs(self):
        env_path = self.write_env()
        first = self.write_file("alpha.pdf")
        second = self.write_file("beta.pdf")
        output_dir = self.root / "out"
        output_dir.mkdir()
        for name in ("source.md", "full.md", "result.json", "response.json", "result.zip", "batch-result.zip", "batch.json"):
            (output_dir / name).write_text("stale", encoding="utf-8")
        (output_dir / "images").mkdir()
        (output_dir / "images" / "stale.png").write_bytes(b"stale")
        (output_dir / "extracted").mkdir()
        (output_dir / "extracted" / "stale.txt").write_text("stale", encoding="utf-8")
        zip_bytes = self.build_zip_bytes(
            {
                "alpha/vlm-engine_auto/alpha.md": "# Alpha\n",
                "beta/vlm-engine_auto/beta.md": "# Beta\n",
            }
        )
        post_sequence = PostSequence([FakeResponse(headers={"content-type": "application/zip"}, content=zip_bytes)])

        with patch("fastapi_parse.requests.post", post_sequence):
            result = fastapi_parse.main(
                [
                    "--file",
                    str(first),
                    "--file",
                    str(second),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )

        self.assertEqual(result, 0)
        self.assertEqual((output_dir / "alpha" / "source.md").read_text(encoding="utf-8"), "# Alpha\n")
        self.assertEqual((output_dir / "beta" / "source.md").read_text(encoding="utf-8"), "# Beta\n")
        self.assertTrue((output_dir / "alpha" / "result.json").exists())
        self.assertTrue((output_dir / "beta" / "result.json").exists())
        for name in ("source.md", "full.md", "result.json", "response.json", "result.zip", "batch-result.zip", "batch.json"):
            self.assertFalse((output_dir / name).exists(), name)
        self.assertFalse((output_dir / "images").exists())
        self.assertFalse((output_dir / "extracted").exists())

    def test_unsafe_zip_member_marks_review_without_writing_member(self):
        env_path = self.write_env()
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        zip_bytes = self.build_zip_bytes(
            {
                "demo/vlm-engine_auto/demo.md": "# Demo\n",
                "demo/vlm-engine_auto/images/..\\..\\evil.png": b"bad",
            }
        )
        post_sequence = PostSequence([FakeResponse(headers={"content-type": "application/zip"}, content=zip_bytes)])
        stderr = io.StringIO()

        with patch("fastapi_parse.requests.post", post_sequence), redirect_stderr(stderr):
            result = fastapi_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )

        self.assertEqual(result, 1)
        self.assertIn("need review", stderr.getvalue())
        metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["needs_review"])
        self.assertIn("unsafe zip member path", metadata["error"])
        self.assertFalse((self.root / "evil.png").exists())
        self.assertFalse((output_dir / "images").exists())

    def test_bad_zip_response_writes_failed_metadata(self):
        env_path = self.write_env()
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        post_sequence = PostSequence([FakeResponse(headers={"content-type": "application/zip"}, content=b"not a zip")])
        stderr = io.StringIO()

        with patch("fastapi_parse.requests.post", post_sequence), redirect_stderr(stderr):
            result = fastapi_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )

        self.assertEqual(result, 1)
        metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "failed")
        self.assertTrue(metadata["needs_review"])
        self.assertIn("could not be opened", metadata["error"])

    def test_watermark_text_marks_review(self):
        env_path = self.write_env()
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        zip_bytes = self.build_zip_bytes({"demo/vlm-engine_auto/demo.md": "# Demo\n识别出了水印\n"})
        post_sequence = PostSequence([FakeResponse(headers={"content-type": "application/zip"}, content=zip_bytes)])
        stderr = io.StringIO()

        with patch("fastapi_parse.requests.post", post_sequence), redirect_stderr(stderr):
            result = fastapi_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )

        self.assertEqual(result, 1)
        metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["needs_review"])
        self.assertIn("possible watermark text detected in full.md", metadata["review_reasons"])

    def test_duplicate_base_filename_fails_before_request(self):
        env_path = self.write_env()
        first = self.write_file("a/demo.pdf")
        second = self.write_file("b/demo.pdf")
        stderr = io.StringIO()

        with patch("fastapi_parse.requests.post") as post, redirect_stderr(stderr):
            result = fastapi_parse.main(
                [
                    "--file",
                    str(first),
                    "--file",
                    str(second),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(self.root / "out"),
                ]
            )

        self.assertEqual(result, 2)
        post.assert_not_called()
        self.assertIn("duplicate original base filename demo", stderr.getvalue())

    def test_async_timeout_writes_batch_metadata(self):
        env_path = self.write_env()
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        post_sequence = PostSequence([FakeResponse(status_code=202, json_payload={"task_id": "task-1", "status": "pending"})])
        get_sequence = GetSequence([FakeResponse(json_payload={"task_id": "task-1", "status": "running"})])
        stderr = io.StringIO()

        with patch("fastapi_parse.requests.post", post_sequence), patch("fastapi_parse.requests.get", get_sequence), patch(
            "fastapi_parse.time.sleep", lambda _: None
        ):
            with redirect_stderr(stderr):
                result = fastapi_parse.main(
                    [
                        "--mode",
                        "async",
                        "--file",
                        str(input_file),
                        "--env-file",
                        str(env_path),
                        "--output-dir",
                        str(output_dir),
                        "--poll-interval",
                        "0.01",
                        "--max-wait",
                        "0.01",
                    ]
                )

        self.assertEqual(result, 1)
        self.assertIn("task did not finish", stderr.getvalue())
        metadata = json.loads((output_dir / "batch.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["needs_review"])
        self.assertEqual(metadata["task_id"], "task-1")


if __name__ == "__main__":
    unittest.main()
