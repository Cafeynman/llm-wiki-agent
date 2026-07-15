from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
USER_ADAPTER_CONTENT = "# User-owned adapter\n"
BASELINE_LINES = (
    ".env",
    "**/.env",
    ".venv/",
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "tmp/",
    ".claude/",
    ".claudian/",
    ".codex/",
)
VERSIONED_POLICY = "\n".join(
    (
        "# user-owned rules",
        "/custom/",
        "/inbox/*",
        "!/inbox/.gitkeep",
        "/intake/tmp/",
        "",
    )
)


class PackageScriptTest(unittest.TestCase):
    def make_target(self, root: Path, *, with_sentinel: bool) -> Path:
        target = root / "target"
        target.mkdir()
        (target / ".gitignore").write_text(VERSIONED_POLICY, encoding="utf-8")
        (target / "CLAUDE.md").write_text(USER_ADAPTER_CONTENT, encoding="utf-8")
        if with_sentinel:
            sentinel = target / ".agents/skills/self-improving-agent/user-owned.txt"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("keep me\n", encoding="utf-8")
        return target

    def assert_target(self, target: Path, call_log: Path, *, with_sentinel: bool) -> None:
        gitignore = (target / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("# user-owned rules", gitignore)
        self.assertIn("/custom/", gitignore)
        self.assertNotIn("/raw/", gitignore)
        for line in BASELINE_LINES:
            self.assertEqual(gitignore.splitlines().count(line), 1, line)
        self.assertTrue((target / "uv.lock").is_file())
        self.assertEqual(
            (target / "CLAUDE.md").read_text(encoding="utf-8"),
            USER_ADAPTER_CONTENT,
        )
        calls = call_log.read_text(encoding="utf-8").splitlines()
        self.assertTrue(calls)
        self.assertTrue(
            all(
                call.strip()
                == "sync --locked --default-index https://pypi.org/simple"
                for call in calls
            ),
            calls,
        )
        if with_sentinel:
            self.assertEqual(
                (target / ".agents/skills/self-improving-agent/user-owned.txt").read_text(
                    encoding="utf-8"
                ),
                "keep me\n",
            )

    def run_powershell_script(self, script_name: str, parameter: str, *, with_sentinel: bool) -> None:
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell is None:
            self.skipTest("PowerShell is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=with_sentinel)
            fake_bin = temp / "bin"
            fake_bin.mkdir()
            call_log = temp / "uv-calls.txt"
            (fake_bin / "uv.cmd").write_text(
                '@echo off\r\n>>"%UV_CALL_LOG%" echo %*\r\nexit /b 0\r\n',
                encoding="ascii",
            )
            env = os.environ.copy()
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            env["UV_CALL_LOG"] = str(call_log)
            command = [
                shell,
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(ROOT / "scripts" / script_name),
                parameter,
                str(target),
            ]

            for _ in range(2):
                subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            self.assert_target(target, call_log, with_sentinel=with_sentinel)

    def run_bash_script(self, script_name: str, parameter: str, *, with_sentinel: bool) -> None:
        if os.name == "nt":
            self.skipTest("Bash package integration runs on POSIX CI")
        shell = shutil.which("bash")
        if shell is None:
            self.skipTest("Bash is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=with_sentinel)
            fake_bin = temp / "bin"
            fake_bin.mkdir()
            call_log = temp / "uv-calls.txt"
            fake_uv = fake_bin / "uv"
            fake_uv.write_text(
                '#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$UV_CALL_LOG"\n',
                encoding="ascii",
            )
            fake_uv.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            env["UV_CALL_LOG"] = str(call_log)
            command = [shell, str(ROOT / "scripts" / script_name), parameter, str(target)]

            for _ in range(2):
                subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            self.assert_target(target, call_log, with_sentinel=with_sentinel)

    def test_init_powershell_is_locked_and_preserves_gitignore_policy(self) -> None:
        self.run_powershell_script("init.ps1", "-VaultRoot", with_sentinel=False)

    def test_upgrade_powershell_preserves_target_only_skill(self) -> None:
        self.run_powershell_script("upgrade.ps1", "-TargetRoot", with_sentinel=True)

    def test_init_bash_is_locked_and_preserves_gitignore_policy(self) -> None:
        self.run_bash_script("init.sh", "-VaultRoot", with_sentinel=False)

    def test_upgrade_bash_preserves_target_only_skill(self) -> None:
        self.run_bash_script("upgrade.sh", "-TargetRoot", with_sentinel=True)

    def test_manifest_leaves_runtime_adapters_user_owned(self) -> None:
        manifest = (ROOT / "scripts/upgrade-manifest.txt").read_text(encoding="utf-8")
        self.assertNotIn("file CLAUDE.md", manifest.splitlines())


if __name__ == "__main__":
    unittest.main()
