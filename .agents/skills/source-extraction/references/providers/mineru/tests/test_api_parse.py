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

import api_parse


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            return self._body
        return self._body[:size]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class UrlopenSequence:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout=0):
        self.requests.append((request, timeout))
        if not self.responses:
            raise AssertionError("No more fake responses configured")
        return self.responses.pop(0)


class RequestsSequence:
    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.calls = []

    def __call__(self, url, data=None, timeout=0, headers=None):
        self.calls.append((url, timeout, headers or {}))
        if hasattr(data, "read"):
            data.read()
        if not self.statuses:
            raise AssertionError("No more fake upload responses configured")
        status = self.statuses.pop(0)
        return type("Resp", (), {"status_code": status})()


class TestApiParse(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_env(self, text: str) -> Path:
        path = self.root / ".env"
        if "MINERU_BASE_URL" not in text:
            text = text.rstrip("\n") + "\nMINERU_BASE_URL=https://mineru.test\n"
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

    def test_missing_token_is_allowed_by_script(self):
        env_path = self.write_env("")
        input_file = self.write_file("demo.pdf")
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "demo.pdf",
                                        "state": "done",
                                        "data_id": "demo",
                                        "full_zip_url": "https://cdn/result.zip",
                                        "err_msg": "",
                                    }
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(self.build_zip_bytes({"full.md": "# ok\n"})),
            ]
        )
        upload_sequence = RequestsSequence([200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            result = api_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(self.root / "out"),
                    "--poll-interval",
                    "0",
                ]
            )

        self.assertEqual(result, 0)
        request, _timeout = sequence.requests[0]
        self.assertNotIn("Authorization", request.headers)

    def test_missing_base_url_returns_error(self):
        env_path = self.root / ".env"
        env_path.write_text("", encoding="utf-8")
        input_file = self.write_file("demo.pdf")
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            result = api_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(self.root / "out"),
                ]
            )

        self.assertEqual(result, 2)
        self.assertIn("missing MinerU base URL", stderr.getvalue())

    def test_create_upload_batch_uses_expected_request_shape(self):
        input_file = self.write_file("demo.pdf")
        file_specs = api_parse.build_file_specs(
            api_parse.parse_args(
                [
                    "--file",
                    str(input_file),
                    "--output-dir",
                    str(self.root / "out"),
                    "--model-version",
                    "vlm",
                    "--enable-table",
                    "--extra-format",
                    "docx",
                ]
            ),
            [input_file],
        )
        payload = api_parse.build_request_payload(
            api_parse.parse_args(
                [
                    "--file",
                    str(input_file),
                    "--output-dir",
                    str(self.root / "out"),
                    "--model-version",
                    "vlm",
                    "--enable-table",
                    "--extra-format",
                    "docx",
                ]
            ),
            file_specs,
        )
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                )
            ]
        )
        upload_sequence = RequestsSequence([])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence):
            batch_id, upload_urls = api_parse.create_upload_batch(
                base_url="https://mineru.net",
                token="secret-token",
                payload=payload,
                timeout=30.0,
            )

        self.assertEqual(batch_id, "batch-123")
        self.assertEqual(upload_urls, ["https://upload/1"])
        request, timeout = sequence.requests[0]
        self.assertEqual(timeout, 30.0)
        self.assertEqual(request.full_url, "https://mineru.net/api/v4/file-urls/batch")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.headers["Authorization"], "Bearer secret-token")
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["files"][0]["name"], "demo.pdf")
        self.assertEqual(body["model_version"], "vlm")
        self.assertEqual(body["extra_formats"], ["docx"])
        self.assertTrue(body["enable_table"])

    def test_request_payload_maps_common_options(self):
        input_file = self.write_file("demo.pdf")
        args = api_parse.parse_args(
            [
                "--file",
                str(input_file),
                "--output-dir",
                str(self.root / "out"),
                "--model-version",
                "pipeline",
                "--language",
                "en",
                "--no-enable-formula",
                "--no-enable-table",
                "--is-ocr",
                "--page-ranges",
                "1-3",
                "--data-id",
                "custom-data",
                "--extra-format",
                "docx",
                "--extra-format",
                "html",
                "--callback",
                "https://example.test/callback",
                "--seed",
                "seed-123",
                "--no-cache",
                "--cache-tolerance",
                "30",
            ]
        )
        file_specs = api_parse.build_file_specs(args, [input_file])
        payload = api_parse.build_request_payload(args, file_specs)

        self.assertEqual(payload["model_version"], "pipeline")
        self.assertEqual(payload["language"], "en")
        self.assertFalse(payload["enable_formula"])
        self.assertFalse(payload["enable_table"])
        self.assertEqual(payload["extra_formats"], ["docx", "html"])
        self.assertEqual(payload["callback"], "https://example.test/callback")
        self.assertEqual(payload["seed"], "seed-123")
        self.assertTrue(payload["no_cache"])
        self.assertEqual(payload["cache_tolerance"], 30)
        self.assertEqual(payload["files"][0]["data_id"], "custom-data")
        self.assertTrue(payload["files"][0]["is_ocr"])
        self.assertEqual(payload["files"][0]["page_ranges"], "1-3")

    def test_callback_requires_seed_before_provider_calls(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        input_file = self.write_file("demo.pdf")
        stderr = io.StringIO()

        with patch("api_parse.create_upload_batch") as create_upload_batch, redirect_stderr(stderr):
            result = api_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(self.root / "out"),
                    "--callback",
                    "https://example.test/callback",
                ]
            )

        self.assertEqual(result, 2)
        create_upload_batch.assert_not_called()
        self.assertIn("--seed is required when --callback is set", stderr.getvalue())

    def test_upload_sends_no_explicit_headers(self):
        input_file = self.write_file("demo.pdf", b"12345")
        upload_sequence = RequestsSequence([200])

        with patch("api_common.requests.put", upload_sequence):
            status = api_parse.upload_file("https://upload/1", input_file, timeout=30.0)

        self.assertEqual(status, 200)
        _url, _timeout, headers = upload_sequence.calls[0]
        self.assertEqual(headers, {})

    def test_main_single_file_uploads_polls_and_extracts_full_md(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        input_file = self.write_file("resnet.pdf")
        output_dir = self.root / "out"
        (output_dir / "extracted").mkdir(parents=True)
        (output_dir / "extracted" / "origin.pdf").write_bytes(b"stale")
        (output_dir / "result.zip").write_bytes(b"stale")
        zip_bytes = self.build_zip_bytes(
            {
                "result/full.md": "# ResNet\n\nResidual learning.\n",
                "result/images/fig.png": b"image-bytes",
                "result/layout.json": "{\"ok\": true}",
                "result/origin.pdf": b"original-pdf",
            }
        )
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {"file_name": "resnet.pdf", "state": "running", "data_id": "resnet"}
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "resnet.pdf",
                                        "state": "done",
                                        "data_id": "resnet",
                                        "full_zip_url": "https://cdn/result.zip",
                                        "err_msg": "",
                                    }
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(zip_bytes),
            ]
        )
        upload_sequence = RequestsSequence([200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            result = api_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--poll-interval",
                    "0",
                ]
            )

        self.assertEqual(result, 0)
        self.assertEqual((output_dir / "source.md").read_text(encoding="utf-8"), "# ResNet\n\nResidual learning.\n")
        self.assertEqual((output_dir / "full.md").read_text(encoding="utf-8"), "# ResNet\n\nResidual learning.\n")
        self.assertEqual((output_dir / "images" / "fig.png").read_bytes(), b"image-bytes")
        self.assertFalse((output_dir / "result.zip").exists())
        self.assertFalse((output_dir / "extracted").exists())
        self.assertFalse((output_dir / "layout.json").exists())
        self.assertFalse((output_dir / "origin.pdf").exists())
        batch_metadata = json.loads((output_dir / "batch.json").read_text(encoding="utf-8"))
        self.assertEqual(batch_metadata["batch_id"], "batch-123")
        item_metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(item_metadata["model_version"], "vlm")
        self.assertEqual(item_metadata["state"], "done")
        self.assertFalse(item_metadata["needs_review"])
        self.assertEqual(item_metadata["preserved_outputs"], ["source.md", "full.md", "images/"])

    def test_keep_flags_preserve_zip_and_full_extraction(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        zip_bytes = self.build_zip_bytes(
            {
                "result/full.md": "# Demo\n",
                "result/layout.json": "{\"ok\": true}",
                "result/origin.pdf": b"original-pdf",
            }
        )
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "demo.pdf",
                                        "state": "done",
                                        "data_id": "demo",
                                        "full_zip_url": "https://cdn/result.zip",
                                        "err_msg": "",
                                    }
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(zip_bytes),
            ]
        )
        upload_sequence = RequestsSequence([200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            result = api_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--keep-result-zip",
                    "--keep-all-extracted",
                    "--poll-interval",
                    "0",
                ]
            )

        self.assertEqual(result, 0)
        self.assertTrue((output_dir / "result.zip").exists())
        self.assertTrue((output_dir / "extracted" / "result" / "layout.json").exists())
        self.assertTrue((output_dir / "extracted" / "result" / "origin.pdf").exists())
        item_metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(
            item_metadata["preserved_outputs"],
            ["source.md", "full.md", "extracted/", "result.zip"],
        )

    def test_watermark_text_marks_review(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        zip_bytes = self.build_zip_bytes({"result/full.md": "# Demo\n\n识别到水印内容\n"})
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "demo.pdf",
                                        "state": "done",
                                        "data_id": "demo",
                                        "full_zip_url": "https://cdn/result.zip",
                                        "err_msg": "",
                                    }
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(zip_bytes),
            ]
        )
        upload_sequence = RequestsSequence([200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            result = api_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--poll-interval",
                    "0",
                ]
            )

        self.assertEqual(result, 0)
        item_metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        self.assertTrue(item_metadata["needs_review"])
        self.assertEqual(item_metadata["review_reasons"], ["possible watermark text detected in full.md"])
        batch_metadata = json.loads((output_dir / "batch.json").read_text(encoding="utf-8"))
        self.assertTrue(batch_metadata["results"][0]["needs_review"])

    def test_main_batch_writes_per_file_directories(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        file_a = self.write_file("a.pdf")
        file_b = self.write_file("b.pdf")
        output_dir = self.root / "out"
        zip_a = self.build_zip_bytes({"result/full.md": "# A\n"})
        zip_b = self.build_zip_bytes({"result/full.md": "# B\n"})
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "file_urls": ["https://upload/1", "https://upload/2"],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "api-renamed-a.pdf",
                                        "state": "done",
                                        "data_id": "a",
                                        "full_zip_url": "https://cdn/a.zip",
                                        "err_msg": "",
                                    },
                                    {
                                        "file_name": "b.pdf",
                                        "state": "done",
                                        "data_id": "b",
                                        "full_zip_url": "https://cdn/b.zip",
                                        "err_msg": "",
                                    },
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(zip_a),
                FakeResponse(zip_b),
            ]
        )
        upload_sequence = RequestsSequence([200, 200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            result = api_parse.main(
                [
                    "--file",
                    str(file_a),
                    "--file",
                    str(file_b),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--poll-interval",
                    "0",
                ]
            )

        self.assertEqual(result, 0)
        self.assertEqual((output_dir / "a" / "source.md").read_text(encoding="utf-8"), "# A\n")
        self.assertEqual((output_dir / "b" / "source.md").read_text(encoding="utf-8"), "# B\n")
        item_metadata = json.loads((output_dir / "a" / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(item_metadata["file_name"], "api-renamed-a.pdf")
        batch_metadata = json.loads((output_dir / "batch.json").read_text(encoding="utf-8"))
        self.assertEqual(len(batch_metadata["results"]), 2)

    def test_main_handles_out_of_order_batch_results(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        file_a = self.write_file("a.pdf")
        file_b = self.write_file("b.pdf")
        output_dir = self.root / "out"
        zip_a = self.build_zip_bytes({"result/full.md": "# A\n"})
        zip_b = self.build_zip_bytes({"result/full.md": "# B\n"})
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "file_urls": ["https://upload/1", "https://upload/2"],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "b.pdf",
                                        "state": "done",
                                        "data_id": "b",
                                        "full_zip_url": "https://cdn/b.zip",
                                        "err_msg": "",
                                    },
                                    {
                                        "file_name": "a.pdf",
                                        "state": "done",
                                        "data_id": "a",
                                        "full_zip_url": "https://cdn/a.zip",
                                        "err_msg": "",
                                    },
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(zip_a),
                FakeResponse(zip_b),
            ]
        )
        upload_sequence = RequestsSequence([200, 200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            result = api_parse.main(
                [
                    "--file",
                    str(file_a),
                    "--file",
                    str(file_b),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--poll-interval",
                    "0",
                ]
            )

        self.assertEqual(result, 0)
        self.assertEqual((output_dir / "a" / "source.md").read_text(encoding="utf-8"), "# A\n")
        self.assertEqual((output_dir / "b" / "source.md").read_text(encoding="utf-8"), "# B\n")

    def test_batch_rejects_duplicate_original_base_names(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        file_a = self.write_file("dir-a/demo.pdf")
        file_b = self.write_file("dir-b/demo.pdf")
        output_dir = self.root / "out"
        stderr = io.StringIO()

        with patch("api_parse.create_upload_batch") as create_upload_batch:
            with redirect_stderr(stderr):
                result = api_parse.main(
                    [
                        "--file",
                        str(file_a),
                        "--file",
                        str(file_b),
                        "--env-file",
                        str(env_path),
                        "--output-dir",
                        str(output_dir),
                        "--poll-interval",
                        "0",
                    ]
                )

        self.assertEqual(result, 2)
        create_upload_batch.assert_not_called()
        self.assertIn("duplicate original base filename demo", stderr.getvalue())
        self.assertFalse((output_dir / "demo" / "source.md").exists())

    def test_rejects_more_than_50_files(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        files: list[str] = []
        for index in range(51):
            files.extend(["--file", str(self.write_file(f"{index}.pdf"))])
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            result = api_parse.main(
                files
                + [
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(self.root / "out"),
                    "--max-files-per-batch",
                    "50",
                ]
            )

        self.assertEqual(result, 2)
        self.assertIn("up to 50 files", stderr.getvalue())

    def test_file_limit_prechecks_are_disabled_by_default_and_configurable(self):
        input_file = self.write_file("demo.pdf", b"1234567890")
        default_args = api_parse.parse_args(
            [
                "--file",
                str(input_file),
                "--output-dir",
                str(self.root / "out"),
            ]
        )
        self.assertEqual(api_parse.build_file_specs(default_args, [input_file])[0]["path"], input_file)

        strict_args = api_parse.parse_args(
            [
                "--file",
                str(input_file),
                "--output-dir",
                str(self.root / "out"),
                "--max-file-mb",
                "0.000001",
            ]
        )
        with self.assertRaisesRegex(RuntimeError, "configured 1e-06 MB file-size limit"):
            api_parse.build_file_specs(strict_args, [input_file])

    def test_default_run_cleans_stale_generated_outputs(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        (output_dir / "images").mkdir(parents=True)
        (output_dir / "images" / "old.png").write_bytes(b"old")
        (output_dir / "extracted").mkdir(parents=True)
        (output_dir / "extracted" / "origin.pdf").write_bytes(b"old")
        (output_dir / "result.zip").write_bytes(b"old")
        (output_dir / "origin.pdf").write_bytes(b"old")
        (output_dir / "layout.json").write_text("{}", encoding="utf-8")
        (output_dir / "content_list.json").write_text("[]", encoding="utf-8")
        zip_bytes = self.build_zip_bytes({"result/full.md": "# Fresh\n"})
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "demo.pdf",
                                        "state": "done",
                                        "data_id": "demo",
                                        "full_zip_url": "https://cdn/result.zip",
                                        "err_msg": "",
                                    }
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(zip_bytes),
            ]
        )
        upload_sequence = RequestsSequence([200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            result = api_parse.main(
                [
                    "--file",
                    str(input_file),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--poll-interval",
                    "0",
                ]
            )

        self.assertEqual(result, 0)
        self.assertEqual((output_dir / "source.md").read_text(encoding="utf-8"), "# Fresh\n")
        self.assertFalse((output_dir / "images").exists())
        self.assertFalse((output_dir / "extracted").exists())
        self.assertFalse((output_dir / "result.zip").exists())
        self.assertFalse((output_dir / "origin.pdf").exists())
        self.assertFalse((output_dir / "layout.json").exists())
        self.assertFalse((output_dir / "content_list.json").exists())

    def test_batch_run_cleans_stale_generated_subdirectories(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        file_a = self.write_file("a.pdf")
        file_b = self.write_file("b.pdf")
        output_dir = self.root / "out"
        (output_dir / "001-old").mkdir(parents=True)
        (output_dir / "001-old" / "source.md").write_text("# old\n", encoding="utf-8")
        (output_dir / "unrelated").mkdir(parents=True)
        (output_dir / "unrelated" / "note.txt").write_text("keep", encoding="utf-8")
        zip_a = self.build_zip_bytes({"result/full.md": "# A\n"})
        zip_b = self.build_zip_bytes({"result/full.md": "# B\n"})
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "file_urls": ["https://upload/1", "https://upload/2"],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "a.pdf",
                                        "state": "done",
                                        "data_id": "a",
                                        "full_zip_url": "https://cdn/a.zip",
                                        "err_msg": "",
                                    },
                                    {
                                        "file_name": "b.pdf",
                                        "state": "done",
                                        "data_id": "b",
                                        "full_zip_url": "https://cdn/b.zip",
                                        "err_msg": "",
                                    },
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(zip_a),
                FakeResponse(zip_b),
            ]
        )
        upload_sequence = RequestsSequence([200, 200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            result = api_parse.main(
                [
                    "--file",
                    str(file_a),
                    "--file",
                    str(file_b),
                    "--env-file",
                    str(env_path),
                    "--output-dir",
                    str(output_dir),
                    "--poll-interval",
                    "0",
                ]
            )

        self.assertEqual(result, 0)
        self.assertFalse((output_dir / "001-old").exists())
        self.assertTrue((output_dir / "unrelated" / "note.txt").exists())

    def test_missing_full_zip_url_writes_review_metadata(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        stderr = io.StringIO()
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "demo.pdf",
                                        "state": "done",
                                        "data_id": "demo",
                                        "err_msg": "",
                                    }
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
            ]
        )
        upload_sequence = RequestsSequence([200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            with redirect_stderr(stderr):
                result = api_parse.main(
                    [
                        "--file",
                        str(input_file),
                        "--env-file",
                        str(env_path),
                        "--output-dir",
                        str(output_dir),
                        "--poll-interval",
                        "0",
                    ]
                )

        self.assertEqual(result, 1)
        self.assertIn("missing full_zip_url", stderr.getvalue())
        item_metadata = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
        batch_metadata = json.loads((output_dir / "batch.json").read_text(encoding="utf-8"))
        self.assertTrue(item_metadata["needs_review"])
        self.assertEqual(item_metadata["extraction_error"], "missing full_zip_url")
        self.assertTrue(batch_metadata["needs_review"])

    def test_timeout_writes_batch_review_metadata(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        input_file = self.write_file("demo.pdf")
        output_dir = self.root / "out"
        stderr = io.StringIO()
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "demo.pdf",
                                        "state": "running",
                                        "data_id": "demo",
                                        "err_msg": "",
                                    }
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
            ]
        )
        upload_sequence = RequestsSequence([200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            with redirect_stderr(stderr):
                result = api_parse.main(
                    [
                        "--file",
                        str(input_file),
                        "--env-file",
                        str(env_path),
                        "--output-dir",
                        str(output_dir),
                        "--poll-interval",
                        "0",
                        "--max-polls",
                        "1",
                    ]
                )

        self.assertEqual(result, 1)
        self.assertIn("batch did not finish after 1 polls", stderr.getvalue())
        batch_metadata = json.loads((output_dir / "batch.json").read_text(encoding="utf-8"))
        self.assertEqual(batch_metadata["batch_id"], "batch-123")
        self.assertTrue(batch_metadata["needs_review"])
        self.assertEqual(batch_metadata["results"][0]["state"], "running")
        self.assertTrue(batch_metadata["results"][0]["needs_review"])

    def test_failed_item_returns_error(self):
        env_path = self.write_env("MINERU_TOKEN=test-token\n")
        input_file = self.write_file("demo.pdf")
        stderr = io.StringIO()
        sequence = UrlopenSequence(
            [
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                        }
                    ).encode("utf-8")
                ),
                FakeResponse(
                    json.dumps(
                        {
                            "code": 0,
                            "msg": "ok",
                            "data": {
                                "batch_id": "batch-123",
                                "extract_result": [
                                    {
                                        "file_name": "demo.pdf",
                                        "state": "failed",
                                        "data_id": "demo",
                                        "err_msg": "unsupported file",
                                    }
                                ],
                            },
                        }
                    ).encode("utf-8")
                ),
            ]
        )
        upload_sequence = RequestsSequence([200])

        with patch("api_common.urlopen", sequence), patch("api_common.requests.put", upload_sequence), patch(
            "api_parse.time.sleep", lambda _: None
        ):
            with redirect_stderr(stderr):
                result = api_parse.main(
                    [
                        "--file",
                        str(input_file),
                        "--env-file",
                        str(env_path),
                        "--output-dir",
                        str(self.root / "out"),
                        "--poll-interval",
                        "0",
                    ]
                )

        self.assertEqual(result, 1)
        self.assertIn("unsupported file", stderr.getvalue())
        item_metadata = json.loads((self.root / "out" / "result.json").read_text(encoding="utf-8"))
        batch_metadata = json.loads((self.root / "out" / "batch.json").read_text(encoding="utf-8"))
        self.assertEqual(item_metadata["state"], "failed")
        self.assertEqual(item_metadata["err_msg"], "unsupported file")
        self.assertEqual(item_metadata["extraction_error"], "unsupported file")
        self.assertTrue(item_metadata["needs_review"])
        self.assertTrue(batch_metadata["needs_review"])


if __name__ == "__main__":
    unittest.main()
