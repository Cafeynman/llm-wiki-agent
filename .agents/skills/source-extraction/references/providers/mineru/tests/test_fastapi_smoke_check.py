import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import fastapi_smoke_check


class TestFastApiSmokeCheck(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_env(self, text: str) -> Path:
        path = self.root / ".env"
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing_base_url_fails_before_route_check(self):
        env_path = self.write_env("")
        stdout = io.StringIO()

        with patch("fastapi_smoke_check.request_json") as request_json, redirect_stdout(stdout):
            result = fastapi_smoke_check.main(["--env-file", str(env_path)])

        self.assertEqual(result, 2)
        request_json.assert_not_called()
        self.assertIn("missing MinerU FastAPI base URL", stdout.getvalue())

    def test_token_required_profile_requires_token_before_route_check(self):
        env_path = self.write_env("MINERU_FASTAPI_BASE_URL=https://mineru.local\n")
        stdout = io.StringIO()

        with patch("fastapi_smoke_check.request_json") as request_json, redirect_stdout(stdout):
            result = fastapi_smoke_check.main(["--env-file", str(env_path), "--requires-token"])

        self.assertEqual(result, 2)
        request_json.assert_not_called()
        self.assertIn("required token is missing", stdout.getvalue())

    def test_health_route_reports_supported_fields(self):
        env_path = self.write_env("MINERU_FASTAPI_BASE_URL=https://mineru.local\nMINERU_FASTAPI_TOKEN=secret\n")
        calls = []

        def fake_request_json(url, *, method, headers, payload=None, timeout=0):
            calls.append((url, method, headers, payload, timeout))
            return 200, {
                "protocol_version": "1",
                "processing_window_size": 1,
                "max_concurrent_requests": 1,
            }

        stdout = io.StringIO()
        with patch("fastapi_smoke_check.request_json", fake_request_json), redirect_stdout(stdout):
            result = fastapi_smoke_check.main(["--env-file", str(env_path), "--user-agent", "curl/8.0"])

        self.assertEqual(result, 0)
        self.assertEqual(calls[0][1], "GET")
        self.assertEqual(calls[0][2]["Authorization"], "Bearer secret")
        self.assertEqual(calls[0][2]["User-Agent"], "curl/8.0")
        self.assertIn("health_route_valid=ok", stdout.getvalue())
        self.assertIn("protocol_version_present=true", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
