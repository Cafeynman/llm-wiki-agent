import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import smoke_check


class TestSmokeCheck(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_env(self, text: str) -> Path:
        path = self.root / ".env"
        path.write_text(text, encoding="utf-8")
        return path

    def test_token_required_profile_requires_token_before_route_check(self):
        env_path = self.write_env("")
        stdout = io.StringIO()

        with patch("smoke_check.request_json") as request_json, redirect_stdout(stdout):
            result = smoke_check.main(
                [
                    "--env-file",
                    str(env_path),
                    "--base-url",
                    "https://mineru.net",
                    "--requires-token",
                    "--docs-url",
                    "https://mineru.net/apiManage/docs",
                ]
            )

        self.assertEqual(result, 1)
        request_json.assert_not_called()
        self.assertIn("required token is missing for the selected profile", stdout.getvalue())
        self.assertIn("docs_url_configured=true", stdout.getvalue())

    def test_missing_base_url_fails_before_route_check(self):
        env_path = self.write_env("")
        stdout = io.StringIO()

        with patch("smoke_check.request_json") as request_json, redirect_stdout(stdout):
            result = smoke_check.main(["--env-file", str(env_path)])

        self.assertEqual(result, 2)
        request_json.assert_not_called()
        self.assertIn("missing MinerU base URL for the selected profile", stdout.getvalue())

    def test_custom_host_can_be_checked_without_token(self):
        env_path = self.write_env("")
        calls = []

        def fake_request_json(url, *, method, headers, payload=None, timeout=0):
            calls.append((url, method, headers, payload))
            if method == "POST":
                return 200, {
                    "code": 0,
                    "msg": "ok",
                    "data": {"batch_id": "batch-123", "file_urls": ["https://upload/1"]},
                }
            return 200, {"code": 0, "msg": "ok", "data": {"extract_result": []}}

        stdout = io.StringIO()
        with patch("smoke_check.request_json", fake_request_json), redirect_stdout(stdout):
            result = smoke_check.main(
                [
                    "--env-file",
                    str(env_path),
                    "--base-url",
                    "https://mineru.internal",
                ]
            )

        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 2)
        self.assertNotIn("Authorization", calls[0][2])
        self.assertIn("API accepted unauthenticated access", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
