from __future__ import annotations

import hashlib
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
PRIVATE_RUNTIME_LINES = (
    "/inbox/*",
    "!/inbox/.gitkeep",
    "/raw/",
    "/intake/",
    "/reviews/",
    "/logs/",
    "/questions/",
    "/artifacts/",
    "/wiki/",
)
OTHER_RUNTIME_LINES = ("/intake/tmp/",)


class PackageScriptTest(unittest.TestCase):
    def snapshot_working_tree(self, target: Path) -> dict[str, tuple[str, str]]:
        snapshot: dict[str, tuple[str, str]] = {}
        for directory, dirnames, filenames in os.walk(target, followlinks=False):
            dirnames[:] = [name for name in dirnames if name != ".git"]
            base = Path(directory)
            for name in sorted(dirnames + filenames):
                path = base / name
                relative = path.relative_to(target).as_posix()
                if path.is_symlink():
                    snapshot[relative] = ("link", os.readlink(path))
                elif path.is_dir():
                    snapshot[relative] = ("directory", "")
                else:
                    snapshot[relative] = (
                        "file",
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                    )
        return snapshot

    def create_directory_link(self, link: Path, target: Path) -> None:
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.skipTest(f"Unable to create a Windows junction: {result.stderr}")
            return
        link.symlink_to(target, target_is_directory=True)

    def environment_without_uv(self) -> dict[str, str]:
        env = os.environ.copy()
        if os.name == "nt":
            system_root = Path(env.get("SystemRoot", r"C:\Windows"))
            env["PATH"] = os.pathsep.join(
                (str(system_root / "System32"), str(system_root))
            )
        else:
            env["PATH"] = "/usr/bin:/bin"
        return env

    def make_fake_uv(self, temp: Path) -> tuple[dict[str, str], Path]:
        fake_bin = temp / "bin"
        fake_bin.mkdir()
        call_log = temp / "uv-calls.txt"
        (fake_bin / "uv.cmd").write_text(
            '@echo off\r\n>>"%UV_CALL_LOG%" echo %*\r\nexit /b 0\r\n',
            encoding="ascii",
        )
        fake_uv = fake_bin / "uv"
        fake_uv.write_text(
            '#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$UV_CALL_LOG"\n',
            encoding="ascii",
        )
        fake_uv.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        env["UV_CALL_LOG"] = str(call_log)
        return env, call_log

    def script_command(
        self,
        shell_kind: str,
        script_name: str,
        parameter: str,
        target: Path,
    ) -> list[str]:
        if shell_kind == "powershell":
            shell = shutil.which("pwsh") or shutil.which("powershell")
            if shell is None:
                self.skipTest("PowerShell is not available")
            return [
                shell,
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(ROOT / "scripts" / script_name),
                parameter,
                str(target),
            ]

        if os.name == "nt":
            self.skipTest("Bash package integration runs on POSIX CI")
        shell = shutil.which("bash")
        if shell is None:
            self.skipTest("Bash is not available")
        return [shell, str(ROOT / "scripts" / script_name), parameter, str(target)]

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

    def seed_tracked_runtime(self, target: Path) -> None:
        git = shutil.which("git")
        if git is None:
            self.skipTest("Git is not available")

        (target / "wiki").mkdir(parents=True, exist_ok=True)
        (target / "wiki/existing.md").write_text("# Existing\n", encoding="utf-8")
        subprocess.run([git, "init", str(target)], check=True, capture_output=True)
        subprocess.run(
            [git, "-C", str(target), "add", "wiki/existing.md"],
            check=True,
            capture_output=True,
        )

    def assert_wiki_ignore_behavior(self, target: Path, *, expected_ignored: bool) -> None:
        git = shutil.which("git")
        if git is None:
            self.skipTest("Git is not available")

        if not (target / ".git").exists():
            subprocess.run([git, "init", str(target)], check=True, capture_output=True)
        (target / "wiki/new.md").write_text("# New\n", encoding="utf-8")
        result = subprocess.run(
            [git, "-C", str(target), "check-ignore", "wiki/new.md"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode == 0, expected_ignored, result.stdout)

    def assert_gitignore_case(
        self,
        target: Path,
        *,
        custom_policy: bool,
        expected_private: bool,
    ) -> None:
        lines = (target / ".gitignore").read_text(encoding="utf-8-sig").splitlines()
        for line in BASELINE_LINES:
            self.assertEqual(lines.count(line), 1, line)
        if custom_policy:
            self.assertIn("# custom policy", lines)
            self.assertIn("/custom/", lines)
        if expected_private:
            for line in PRIVATE_RUNTIME_LINES:
                self.assertIn(line, lines)
            for line in OTHER_RUNTIME_LINES:
                self.assertNotIn(line, lines)
        else:
            for line in PRIVATE_RUNTIME_LINES + OTHER_RUNTIME_LINES:
                self.assertNotIn(line, lines)
        self.assert_wiki_ignore_behavior(target, expected_ignored=expected_private)

    def run_powershell_gitignore_matrix(self, script_name: str, parameter: str) -> None:
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell is None:
            self.skipTest("PowerShell is not available")

        cases = (
            ("existing_custom", True, False, False),
            ("missing_tracked", False, True, False),
            ("missing_untracked", False, False, True),
        )
        for name, custom_policy, tracked_runtime, expected_private in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                if custom_policy:
                    (target / ".gitignore").write_text(
                        "# custom policy\n/custom/\n", encoding="utf-8"
                    )
                if tracked_runtime:
                    self.seed_tracked_runtime(target)

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
                self.assert_gitignore_case(
                    target,
                    custom_policy=custom_policy,
                    expected_private=expected_private,
                )

    def run_bash_gitignore_matrix(self, script_name: str, parameter: str) -> None:
        if os.name == "nt":
            self.skipTest("Bash package integration runs on POSIX CI")
        shell = shutil.which("bash")
        if shell is None:
            self.skipTest("Bash is not available")

        cases = (
            ("existing_custom", True, False, False),
            ("missing_tracked", False, True, False),
            ("missing_untracked", False, False, True),
        )
        for name, custom_policy, tracked_runtime, expected_private in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                if custom_policy:
                    (target / ".gitignore").write_text(
                        "# custom policy\n/custom/\n", encoding="utf-8"
                    )
                if tracked_runtime:
                    self.seed_tracked_runtime(target)

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
                self.assert_gitignore_case(
                    target,
                    custom_policy=custom_policy,
                    expected_private=expected_private,
                )

    def test_init_powershell_is_locked_and_preserves_gitignore_policy(self) -> None:
        self.run_powershell_script("init.ps1", "-VaultRoot", with_sentinel=False)

    def test_upgrade_powershell_preserves_target_only_skill(self) -> None:
        self.run_powershell_script("upgrade.ps1", "-TargetRoot", with_sentinel=True)

    def test_init_bash_is_locked_and_preserves_gitignore_policy(self) -> None:
        self.run_bash_script("init.sh", "-VaultRoot", with_sentinel=False)

    def test_upgrade_bash_preserves_target_only_skill(self) -> None:
        self.run_bash_script("upgrade.sh", "-TargetRoot", with_sentinel=True)

    def test_init_powershell_preserves_or_seeds_gitignore_policy(self) -> None:
        self.run_powershell_gitignore_matrix("init.ps1", "-VaultRoot")

    def test_upgrade_powershell_preserves_or_seeds_gitignore_policy(self) -> None:
        self.run_powershell_gitignore_matrix("upgrade.ps1", "-TargetRoot")

    def test_init_bash_preserves_or_seeds_gitignore_policy(self) -> None:
        self.run_bash_gitignore_matrix("init.sh", "-VaultRoot")

    def test_upgrade_bash_preserves_or_seeds_gitignore_policy(self) -> None:
        self.run_bash_gitignore_matrix("upgrade.sh", "-TargetRoot")

    def test_manifest_leaves_runtime_adapters_user_owned(self) -> None:
        manifest = (ROOT / "scripts/upgrade-manifest.txt").read_text(encoding="utf-8")
        self.assertNotIn("file CLAUDE.md", manifest.splitlines())

    def test_init_scripts_are_thin_upgrade_wrappers(self) -> None:
        powershell = (ROOT / "scripts/init.ps1").read_text(encoding="utf-8")
        bash = (ROOT / "scripts/init.sh").read_text(encoding="utf-8")
        self.assertIn("upgrade.ps1", powershell)
        self.assertIn("upgrade.sh", bash)
        self.assertLessEqual(len(powershell.splitlines()), 40)
        self.assertLessEqual(len(bash.splitlines()), 60)
        self.assertNotIn("astral.sh", powershell + bash)
        self.assertNotIn("Invoke-RestMethod", powershell)
        self.assertNotIn("curl", bash)

    def test_usage_documents_describe_the_overwrite_guard(self) -> None:
        usage = (ROOT / "docs/usage.md").read_text(encoding="utf-8")
        usage_zh = (ROOT / "docs/usage.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("tracked and clean", usage)
        self.assertIn("stops before target writes", usage)
        self.assertIn("links or reparse points", usage)
        self.assertNotIn("Listed files are overwritten", usage)
        self.assertIn("已跟踪且相对 `HEAD` 干净", usage_zh)
        self.assertIn("在写入目标前停止", usage_zh)
        self.assertIn("目录联接", usage_zh)
        self.assertNotIn("列出的文件会被覆盖", usage_zh)

    def test_cross_platform_contract_workflow_is_lightweight(self) -> None:
        workflow = (ROOT / ".github/workflows/package-contract-tests.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("bash -n scripts/init.sh scripts/upgrade.sh", workflow)
        self.assertIn("uv run --no-project python -m unittest", workflow)
        self.assertNotIn("uv sync", workflow)

    def assert_overwrite_guard(self, shell_kind: str) -> None:
        git = shutil.which("git")
        if git is None:
            self.skipTest("Git is not available")

        for script_name, parameter in (
            ("init.ps1" if shell_kind == "powershell" else "init.sh", "-VaultRoot"),
            ("upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh", "-TargetRoot"),
        ):
            with self.subTest(script=script_name, case="non_git_conflict"), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                local_wiki = b"# Local contract\n"
                (target / "WIKI.md").write_bytes(local_wiki)
                env, call_log = self.make_fake_uv(temp)
                result = subprocess.run(
                    self.script_command(shell_kind, script_name, parameter, target),
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((target / "WIKI.md").read_bytes(), local_wiki)
                self.assertFalse((target / "AGENTS.md").exists())
                self.assertFalse(call_log.exists())

            with self.subTest(script=script_name, case="clean_git_replace"), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                (target / "WIKI.md").write_text("# Previous package contract\n", encoding="utf-8")
                subprocess.run([git, "init", str(target)], check=True, capture_output=True)
                subprocess.run([git, "-C", str(target), "add", "WIKI.md"], check=True, capture_output=True)
                subprocess.run(
                    [
                        git,
                        "-C",
                        str(target),
                        "-c",
                        "user.name=Package Tests",
                        "-c",
                        "user.email=package-tests@example.invalid",
                        "commit",
                        "-m",
                        "baseline",
                    ],
                    check=True,
                    capture_output=True,
                )
                env, call_log = self.make_fake_uv(temp)
                subprocess.run(
                    self.script_command(shell_kind, script_name, parameter, target),
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    (target / "WIKI.md").read_bytes(),
                    (ROOT / "WIKI.md").read_bytes(),
                )
                self.assertTrue(call_log.exists())

            with self.subTest(script=script_name, case="runtime_only_dirty"), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                env, call_log = self.make_fake_uv(temp)
                command = self.script_command(shell_kind, script_name, parameter, target)
                subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run([git, "init", str(target)], check=True, capture_output=True)
                subprocess.run([git, "-C", str(target), "add", "-A"], check=True, capture_output=True)
                subprocess.run(
                    [git, "-C", str(target), "add", "-f", "wiki/home.md"],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    [
                        git,
                        "-C",
                        str(target),
                        "-c",
                        "user.name=Package Tests",
                        "-c",
                        "user.email=package-tests@example.invalid",
                        "commit",
                        "-m",
                        "baseline",
                    ],
                    check=True,
                    capture_output=True,
                )
                runtime_page = target / "wiki/home.md"
                runtime_page.write_text("# User runtime change\n", encoding="utf-8")
                call_log.write_text("", encoding="utf-8")
                subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(runtime_page.read_text(encoding="utf-8"), "# User runtime change\n")
                self.assertEqual(len(call_log.read_text(encoding="utf-8").splitlines()), 1)

            for conflict_case in (
                "tracked_modified",
                "staged_modified",
                "tracked_deleted",
                "same_name_untracked",
            ):
                with self.subTest(script=script_name, case=conflict_case), tempfile.TemporaryDirectory() as temp_dir:
                    temp = Path(temp_dir)
                    target = temp / "target"
                    target.mkdir()
                    subprocess.run([git, "init", str(target)], check=True, capture_output=True)

                    if conflict_case == "same_name_untracked":
                        (target / "baseline.txt").write_text("baseline\n", encoding="utf-8")
                        committed_path = "baseline.txt"
                    else:
                        (target / "WIKI.md").write_text(
                            "# Previous package contract\n", encoding="utf-8"
                        )
                        committed_path = "WIKI.md"
                    subprocess.run(
                        [git, "-C", str(target), "add", committed_path],
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        [
                            git,
                            "-C",
                            str(target),
                            "-c",
                            "user.name=Package Tests",
                            "-c",
                            "user.email=package-tests@example.invalid",
                            "commit",
                            "-m",
                            "baseline",
                        ],
                        check=True,
                        capture_output=True,
                    )

                    if conflict_case == "tracked_deleted":
                        (target / "WIKI.md").unlink()
                    else:
                        (target / "WIKI.md").write_text(
                            "# Local managed-file change\n", encoding="utf-8"
                        )
                    if conflict_case == "staged_modified":
                        subprocess.run(
                            [git, "-C", str(target), "add", "WIKI.md"],
                            check=True,
                            capture_output=True,
                        )

                    before = self.snapshot_working_tree(target)
                    env, call_log = self.make_fake_uv(temp)
                    result = subprocess.run(
                        self.script_command(shell_kind, script_name, parameter, target),
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Conflict: WIKI.md", result.stdout + result.stderr)
                    self.assertEqual(self.snapshot_working_tree(target), before)
                    self.assertFalse(call_log.exists())

    def assert_structure_preflight(self, shell_kind: str) -> None:
        for script_name, parameter in (
            ("init.ps1" if shell_kind == "powershell" else "init.sh", "-VaultRoot"),
            ("upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh", "-TargetRoot"),
        ):
            with self.subTest(script=script_name, case="runtime_type_collision"), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                (target / "logs").write_text("not a directory\n", encoding="utf-8")
                before = self.snapshot_working_tree(target)
                env, call_log = self.make_fake_uv(temp)
                result = subprocess.run(
                    self.script_command(shell_kind, script_name, parameter, target),
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("logs", result.stdout + result.stderr)
                self.assertEqual(self.snapshot_working_tree(target), before)
                self.assertFalse(call_log.exists())

            for target_exists in (True, False):
                case = "linked_ancestor_existing_target" if target_exists else "linked_ancestor_missing_target"
                with self.subTest(script=script_name, case=case), tempfile.TemporaryDirectory() as temp_dir:
                    temp = Path(temp_dir)
                    external = temp / "external"
                    external.mkdir()
                    sentinel = external / "sentinel.txt"
                    sentinel.write_text("outside\n", encoding="utf-8")
                    if target_exists:
                        (external / "target").mkdir()

                    linked_ancestor = temp / "linked-ancestor"
                    self.create_directory_link(linked_ancestor, external)
                    target = linked_ancestor / "target"
                    before = self.snapshot_working_tree(external)
                    env, call_log = self.make_fake_uv(temp)
                    result = subprocess.run(
                        self.script_command(shell_kind, script_name, parameter, target),
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("target root path", (result.stdout + result.stderr).lower())
                    self.assertEqual(self.snapshot_working_tree(external), before)
                    self.assertFalse(call_log.exists())

            with self.subTest(script=script_name, case="linked_managed_directory"), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                external = temp / "external"
                target.mkdir()
                external.mkdir()
                sentinel = external / "sentinel.txt"
                sentinel.write_text("outside\n", encoding="utf-8")
                self.create_directory_link(target / "docs", external)
                env, call_log = self.make_fake_uv(temp)
                result = subprocess.run(
                    self.script_command(shell_kind, script_name, parameter, target),
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("docs", result.stdout + result.stderr)
                self.assertEqual(sentinel.read_text(encoding="utf-8"), "outside\n")
                self.assertEqual(sorted(path.name for path in external.iterdir()), ["sentinel.txt"])
                self.assertFalse((target / "AGENTS.md").exists())
                self.assertFalse(call_log.exists())

            if os.name != "nt":
                with self.subTest(script=script_name, case="linked_gitignore"), tempfile.TemporaryDirectory() as temp_dir:
                    temp = Path(temp_dir)
                    target = temp / "target"
                    target.mkdir()
                    external_gitignore = temp / "external.gitignore"
                    external_gitignore.write_text("external-policy\n", encoding="utf-8")
                    (target / ".gitignore").symlink_to(external_gitignore)
                    env, call_log = self.make_fake_uv(temp)
                    result = subprocess.run(
                        self.script_command(shell_kind, script_name, parameter, target),
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(".gitignore", result.stdout + result.stderr)
                    self.assertEqual(
                        external_gitignore.read_text(encoding="utf-8"),
                        "external-policy\n",
                    )
                    self.assertFalse((target / "AGENTS.md").exists())
                    self.assertFalse(call_log.exists())

    def assert_missing_uv_has_no_target_writes(self, shell_kind: str) -> None:
        script_name = "init.ps1" if shell_kind == "powershell" else "init.sh"
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            target.mkdir()
            result = subprocess.run(
                self.script_command(shell_kind, script_name, "-VaultRoot", target),
                cwd=ROOT,
                env=self.environment_without_uv(),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("uv was not found", result.stdout + result.stderr)
            self.assertEqual(list(target.iterdir()), [])

    def test_powershell_minimal_overwrite_guard(self) -> None:
        self.assert_overwrite_guard("powershell")

    def test_bash_minimal_overwrite_guard(self) -> None:
        self.assert_overwrite_guard("bash")

    def test_powershell_target_structure_preflight(self) -> None:
        self.assert_structure_preflight("powershell")

    def test_bash_target_structure_preflight(self) -> None:
        self.assert_structure_preflight("bash")

    def test_powershell_missing_uv_has_no_target_writes(self) -> None:
        self.assert_missing_uv_has_no_target_writes("powershell")

    def test_bash_missing_uv_has_no_target_writes(self) -> None:
        self.assert_missing_uv_has_no_target_writes("bash")


if __name__ == "__main__":
    unittest.main()
