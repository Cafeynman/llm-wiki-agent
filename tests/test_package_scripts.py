from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
if os.name == "nt":
    (ROOT / "tmp").mkdir(exist_ok=True)
    tempfile.tempdir = str(ROOT / "tmp")
USER_ADAPTER_CONTENT = "# User-owned adapter\n"
REQUIRED_GITIGNORE_LINES = (
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
    ".obsidian/",
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
MANAGED_DIRECTORIES = ("docs", "scenarios", "scripts", ".agents/skills")
ROOT_PACKAGE_FILES = {
    "AGENTS.md",
    "WIKI.md",
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "pyproject.toml",
    "uv.lock",
    ".gitattributes",
    ".env.example",
}


class PackageScriptTest(unittest.TestCase):
    def bash_executable(self) -> str | None:
        if os.name == "nt":
            return None
        if sys.platform == "darwin" and Path("/bin/bash").is_file():
            return "/bin/bash"
        return shutil.which("bash")

    def windows_git_bash_executable(self) -> str | None:
        if os.name != "nt":
            return None
        git_bash = (
            Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            / "Git/bin/bash.exe"
        )
        return str(git_bash) if git_bash.is_file() else None

    def bash_path(self, path: Path) -> str:
        resolved = path.resolve()
        if os.name != "nt":
            return str(resolved)
        drive = resolved.drive.rstrip(":").lower()
        suffix = resolved.as_posix().split(":", 1)[1]
        return f"/{drive}{suffix}"

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

    def make_fake_uv(
        self,
        temp: Path,
        *,
        fail_lock: bool = False,
        fail_sync: bool = False,
        remove_on_sync: Path | None = None,
    ) -> tuple[dict[str, str], Path]:
        fake_bin = temp / "bin"
        fake_bin.mkdir()
        call_log = temp / "uv-calls.txt"
        cmd_remove = (
            'if "%1"=="sync" if defined UV_REMOVE_ON_SYNC del /f /q "%UV_REMOVE_ON_SYNC%"\r\n'
            if remove_on_sync is not None
            else ""
        )
        cmd_lock_failure = 'if "%1"=="lock" exit /b 8\r\n' if fail_lock else ""
        cmd_sync_failure = 'if "%1"=="sync" exit /b 9\r\n' if fail_sync else ""
        (fake_bin / "uv.cmd").write_text(
            '@echo off\r\n>>"%UV_CALL_LOG%" echo %*\r\n'
            + cmd_remove
            + cmd_lock_failure
            + cmd_sync_failure
            + "exit /b 0\r\n",
            encoding="ascii",
        )
        fake_uv = fake_bin / "uv"
        bash_remove = (
            '[[ "$1" == "sync" && -n "${UV_REMOVE_ON_SYNC_BASH:-}" ]] && '
            'rm -f -- "$UV_REMOVE_ON_SYNC_BASH"\n'
            if remove_on_sync is not None
            else ""
        )
        bash_lock_failure = '[[ "$1" == "lock" ]] && exit 8\n' if fail_lock else ""
        bash_sync_failure = '[[ "$1" == "sync" ]] && exit 9\n' if fail_sync else ""
        fake_uv.write_text(
            '#!/usr/bin/env bash\nlog="${UV_CALL_LOG_BASH:-$UV_CALL_LOG}"\n'
            'printf "%s\\n" "$*" >> "$log"\n'
            + bash_remove
            + bash_lock_failure
            + bash_sync_failure
            + "exit 0\n",
            encoding="ascii",
        )
        fake_uv.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        env["UV_CALL_LOG"] = str(call_log)
        if remove_on_sync is not None:
            env["UV_REMOVE_ON_SYNC"] = str(remove_on_sync)
        if os.name == "nt":
            env["UV_CALL_LOG_BASH"] = self.bash_path(call_log)
            if remove_on_sync is not None:
                env["UV_REMOVE_ON_SYNC_BASH"] = self.bash_path(remove_on_sync)
        elif remove_on_sync is not None:
            env["UV_REMOVE_ON_SYNC_BASH"] = str(remove_on_sync)
        return env, call_log

    def script_command(
        self,
        shell_kind: str,
        script_name: str,
        parameter: str,
        target: Path,
        *,
        package_root: Path | None = None,
    ) -> list[str]:
        source_root = ROOT if package_root is None else package_root
        if shell_kind == "powershell":
            shell = shutil.which("pwsh") or shutil.which("powershell")
            if shell is None:
                self.skipTest("PowerShell is not available")
            return [
                shell,
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(source_root / "scripts" / script_name),
                parameter,
                str(target),
            ]

        shell = self.bash_executable()
        if shell is None:
            self.skipTest("Bash is not available")
        script_path = source_root / "scripts" / script_name
        if os.name == "nt":
            return [shell, self.bash_path(script_path), parameter, self.bash_path(target)]
        return [shell, str(script_path), parameter, str(target)]

    def make_package_copy(self, root: Path) -> Path:
        package = root / "package"
        package.mkdir()
        inventory_entries = {
            tuple(line.strip().split(maxsplit=1))
            for line in (ROOT / "scripts/package-files.txt").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        package_files = {
            relative for state, relative in inventory_entries if state == "active"
        }
        package_files.update(
            {
                "PROJECT.md",
                ".gitignore",
            }
        )
        for relative in sorted(package_files):
            source = ROOT / relative
            destination = package / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return package

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
        for line in REQUIRED_GITIGNORE_LINES:
            self.assertEqual(gitignore.splitlines().count(line), 1, line)
        self.assertTrue((target / "uv.lock").is_file())
        self.assertEqual(
            (target / "CLAUDE.md").read_text(encoding="utf-8"),
            USER_ADAPTER_CONTENT,
        )
        for relative_path in (
            ".agents/skills/wiki-maintenance-feedback/SKILL.md",
            ".agents/skills/wiki-maintenance-feedback/references/report-template.md",
            "scenarios/exam-study/skills/exam-study/SKILL.md",
            "scenarios/exam-study/skills/exam-study/references/workflow-contract.md",
            "scenarios/exam-study/skills/exam-study/scripts/audit_wrong_questions.py",
        ):
            self.assertEqual(
                (target / relative_path).read_bytes(),
                (ROOT / relative_path).read_bytes(),
                relative_path,
            )
        calls = call_log.read_text(encoding="utf-8").splitlines()
        self.assertTrue(calls)
        self.assertTrue(
            all(
                call.strip() in {
                    "lock --check --default-index https://pypi.org/simple",
                    "sync --locked --default-index https://pypi.org/simple",
                }
                for call in calls
            ),
            calls,
        )
        self.assertEqual(
            calls.count("lock --check --default-index https://pypi.org/simple"),
            calls.count("sync --locked --default-index https://pypi.org/simple"),
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
        shell = self.bash_executable()
        if shell is None:
            self.skipTest("Bash is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=with_sentinel)
            env, call_log = self.make_fake_uv(temp)
            command = self.script_command("bash", script_name, parameter, target)

            for _ in range(2):
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            self.assert_target(target, call_log, with_sentinel=with_sentinel)

    def seed_existing_runtime(self, target: Path) -> None:
        (target / "wiki").mkdir(parents=True, exist_ok=True)
        (target / "wiki/existing.md").write_text("# Existing\n", encoding="utf-8")

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
        for line in REQUIRED_GITIGNORE_LINES:
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
            ("existing_custom", True, False, False, True),
            ("existing_custom_no_final_newline", True, False, False, False),
            ("missing_with_runtime", False, True, True, True),
            ("missing_empty", False, False, True, True),
        )
        for name, custom_policy, existing_runtime, expected_private, final_newline in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                if custom_policy:
                    (target / ".gitignore").write_text(
                        "# custom policy\n/custom/" + ("\n" if final_newline else ""),
                        encoding="utf-8",
                    )
                if existing_runtime:
                    self.seed_existing_runtime(target)

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
        shell = self.bash_executable()
        if shell is None:
            self.skipTest("Bash is not available")

        cases = (
            ("existing_custom", True, False, False, True),
            ("existing_custom_no_final_newline", True, False, False, False),
            ("missing_with_runtime", False, True, True, True),
            ("missing_empty", False, False, True, True),
        )
        for name, custom_policy, existing_runtime, expected_private, final_newline in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                if custom_policy:
                    (target / ".gitignore").write_text(
                        "# custom policy\n/custom/" + ("\n" if final_newline else ""),
                        encoding="utf-8",
                    )
                if existing_runtime:
                    self.seed_existing_runtime(target)

                env, call_log = self.make_fake_uv(temp)
                command = self.script_command("bash", script_name, parameter, target)
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

    def test_bash_large_gitignore_remains_idempotent(self) -> None:
        if os.name == "nt":
            self.skipTest("Supported Bash upgrade coverage runs on Linux and macOS")
        shell = self.bash_executable()
        if shell is None:
            self.skipTest("Bash is not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = temp / "target"
            target.mkdir()
            (target / ".gitignore").write_bytes(
                b".env\r\n" + (b"# padding for pipe buffer coverage\r\n" * 20000)
            )
            env, _ = self.make_fake_uv(temp)
            command = self.script_command("bash", "upgrade.sh", "-TargetRoot", target)

            for _ in range(2):
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            lines = (target / ".gitignore").read_text(encoding="utf-8").splitlines()
            for line in REQUIRED_GITIGNORE_LINES:
                self.assertEqual(lines.count(line), 1, line)

    def test_inventory_is_the_single_1_0_ownership_contract(self) -> None:
        inventory = (ROOT / "scripts/package-files.txt").read_text(encoding="utf-8")
        records = {
            tuple(line.strip().split(maxsplit=1))
            for line in inventory.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertEqual(
            inventory.splitlines().count("# inventory-schema: 1"), 1
        )
        self.assertFalse((ROOT / "scripts/upgrade-manifest.txt").exists())
        self.assertNotIn(("active", "CLAUDE.md"), records)
        for pre_1_path in (
            "scripts/upgrade-manifest.txt",
            "docs/通用底座改进计划.md",
            ".agents/skills/source-extraction/scripts/record_chunk_exception.py",
            ".agents/skills/source-extraction/tests/test_record_chunk_exception.py",
        ):
            self.assertNotIn(("active", pre_1_path), records)
            self.assertNotIn(("remove", pre_1_path), records)

    def test_package_inventory_matches_tracked_managed_files(self) -> None:
        git = shutil.which("git")
        if git is None:
            self.skipTest("Git is not available")
        inventory_path = ROOT / "scripts/package-files.txt"
        inventory = {
            tuple(line.strip().split(maxsplit=1))
            for line in inventory_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        result = subprocess.run(
            [git, "-c", "core.quotepath=false", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        tracked = {
            relative
            for relative in result.stdout.splitlines()
            if (ROOT / relative).is_file()
            and (
                relative in ROOT_PACKAGE_FILES
                or any(
                    relative.startswith(f"{directory}/")
                    for directory in MANAGED_DIRECTORIES
                )
            )
        }
        self.assertTrue({kind for kind, _path in inventory} <= {"active", "remove"})
        active = {path for kind, path in inventory if kind == "active"}
        removed = {path for kind, path in inventory if kind == "remove"}
        self.assertEqual(active, tracked)
        self.assertTrue(removed.isdisjoint(tracked))

    def test_upgrade_ignores_untracked_files_inside_managed_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            source_only = package / "docs/untracked-upgrade-sentinel.txt"
            source_only.write_text("must not be copied\n", encoding="utf-8")
            target = self.make_target(temp, with_sentinel=False)
            run_root = temp / "run"
            run_root.mkdir()
            env, _ = self.make_fake_uv(run_root)
            result = subprocess.run(
                self.script_command(
                    "powershell",
                    "upgrade.ps1",
                    "-TargetRoot",
                    target,
                    package_root=package,
                ),
                cwd=package,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((target / "docs/untracked-upgrade-sentinel.txt").exists())

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

    def test_upgrade_scripts_do_not_use_repository_state_for_ownership(self) -> None:
        powershell = (ROOT / "scripts/upgrade.ps1").read_text(encoding="utf-8")
        bash = (ROOT / "scripts/upgrade.sh").read_text(encoding="utf-8")

        for stale_token in (
            "Get-GitBaseline",
            "Test-GitPathMatchesHead",
            "Get-Command git",
            "& git",
            "HEAD:",
            "uncommitted changes",
        ):
            self.assertNotIn(stale_token, powershell)
        for stale_token in (
            "git -C",
            "command -v git",
            "git_baseline",
            "tracked_path_matches_head",
            "has_tracked_wiki_runtime",
        ):
            self.assertNotIn(stale_token, bash)

    def test_upgrade_scripts_support_documented_shell_versions(self) -> None:
        powershell = (ROOT / "scripts/upgrade.ps1").read_text(encoding="utf-8")
        bash = (ROOT / "scripts/upgrade.sh").read_text(encoding="utf-8")

        self.assertNotIn("GetRelativePath", powershell)
        self.assertNotIn("Get-FileHash", powershell)
        self.assertIn("Get-RelativePathCompat", powershell)
        self.assertIn("ReadAllLines", powershell)
        self.assertIn("UTF8Encoding", powershell)
        for bash_four_only in ("declare -A", "local -n", ",,}", "${!"):
            self.assertNotIn(bash_four_only, bash)
        for non_portable_operand_separator in ("cp -f --", "mv -f --", "rm -f --"):
            self.assertNotIn(non_portable_operand_separator, bash)
        self.assertNotIn("upgrade-manifest", powershell + bash)
        self.assertIn("package-files.txt\" ]] && metadata_order=1", bash)
        self.assertNotIn("metadata_order=2", bash)

    def test_bash_rejects_windows_runtime_before_writes(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows drive-path guard")
        shell = self.windows_git_bash_executable()
        if shell is None:
            self.skipTest("Git Bash is not available")
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            result = subprocess.run(
                [
                    shell,
                    self.bash_path(ROOT / "scripts/upgrade.sh"),
                    "-TargetRoot",
                    str(target),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("supports macOS and Linux only", result.stdout + result.stderr)
            self.assertFalse(target.exists())

    def test_windows_powershell_51_reads_utf8_ownership_paths(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows PowerShell 5.1 coverage")
        shell = shutil.which("powershell")
        if shell is None:
            self.skipTest("Windows PowerShell is not available")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            relative = "docs/中文升级契约.md"
            source = package / relative
            source.write_text("第一版\n", encoding="utf-8")
            inventory = package / "scripts/package-files.txt"
            inventory.write_text(
                inventory.read_text(encoding="utf-8") + f"active {relative}\n",
                encoding="utf-8",
            )
            target = temp / "target"
            target.mkdir()
            env, _ = self.make_fake_uv(temp)
            command = [
                shell,
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(package / "scripts/upgrade.ps1"),
                "-TargetRoot",
                str(target),
            ]
            first = subprocess.run(
                command,
                cwd=package,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual((target / relative).read_text(encoding="utf-8"), "第一版\n")

            source.write_text("第二版\n", encoding="utf-8")
            second = subprocess.run(
                command,
                cwd=package,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual((target / relative).read_text(encoding="utf-8"), "第二版\n")
            self.assertIn(
                "# inventory-schema: 1",
                (target / "scripts/package-files.txt").read_text(encoding="utf-8"),
            )

    def test_powershell_replaces_an_owned_file_without_repository_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            env, call_log = self.make_fake_uv(temp)
            command = self.script_command("powershell", "upgrade.ps1", "-TargetRoot", target)
            first = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            (target / "WIKI.md").write_text("# Local edit inside package ownership\n", encoding="utf-8")
            call_log.unlink()
            second = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual((target / "WIKI.md").read_bytes(), (ROOT / "WIKI.md").read_bytes())
            self.assertTrue(call_log.exists())

    def test_powershell_rejects_invalid_utf8_old_metadata_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            scripts = target / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "package-files.txt").write_bytes(
                b"# inventory-schema: 1\nactive scripts/package-files.txt\n\xff\n"
            )
            before = self.snapshot_working_tree(target)
            env, call_log = self.make_fake_uv(temp)
            result = subprocess.run(
                self.script_command("powershell", "upgrade.ps1", "-TargetRoot", target),
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertFalse(call_log.exists())

    def test_usage_documents_describe_the_overwrite_guard(self) -> None:
        usage = (ROOT / "docs/usage.md").read_text(encoding="utf-8")
        usage_zh = (ROOT / "docs/usage.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("only package ownership source", usage)
        self.assertIn("target Git history is not consulted", usage)
        self.assertIn("blocks the upgrade before target writes", usage)
        self.assertIn("links or reparse points", usage)
        self.assertIn("declares `# inventory-schema: 1`", usage)
        self.assertIn("`active <path>` and `remove <path>`", usage)
        self.assertIn("Versions before 1.0 are not supported", usage)
        self.assertIn("retained until the path explicitly returns as `active`", usage)
        self.assertIn("new inventory is committed last", usage)
        self.assertIn("rejects Windows runtimes", usage)
        self.assertNotIn("tracked and clean", usage)
        self.assertIn("唯一包所有权来源", usage_zh)
        self.assertIn("不读取目标 Git 历史", usage_zh)
        self.assertIn("在写入目标前停止", usage_zh)
        self.assertIn("目录联接", usage_zh)
        self.assertIn("`# inventory-schema: 1`", usage_zh)
        self.assertIn("`active <path>` 与 `remove <path>`", usage_zh)
        self.assertIn("1.0 之前的版本不作为升级来源支持", usage_zh)
        self.assertIn("保留到该路径明确重新成为 `active`", usage_zh)
        self.assertIn("新 inventory 最后", usage_zh)
        self.assertIn("拒绝 Windows 运行时", usage_zh)
        self.assertNotIn("相对 `HEAD` 干净", usage_zh)

    def test_cross_platform_contract_workflow_is_lightweight(self) -> None:
        workflow = (ROOT / ".github/workflows/package-contract-tests.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("macos-latest", workflow)
        self.assertIn("windows-latest", workflow)
        self.assertIn("runner.os == 'Linux'", workflow)
        self.assertIn("runner.os == 'macOS'", workflow)
        self.assertIn("bash -n scripts/init.sh scripts/upgrade.sh", workflow)
        self.assertIn("/bin/bash -n scripts/init.sh scripts/upgrade.sh", workflow)
        self.assertIn("uv lock --check", workflow)
        self.assertIn("UV_DEFAULT_INDEX: https://pypi.org/simple", workflow)
        self.assertIn("uv run --no-project python -m unittest", workflow)
        self.assertNotIn("uv sync", workflow)


    def assert_ownership_guard(self, shell_kind: str) -> None:
        script_name = "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            target = self.make_target(temp, with_sentinel=True)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            command = self.script_command(
                shell_kind,
                script_name,
                "-TargetRoot",
                target,
                package_root=package,
            )
            setup = subprocess.run(
                command,
                cwd=package,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            project_content = "# Project\n\nkeep project choices\n"
            env_content = "PRIVATE_SETTING=preserve\n"
            runtime_content = "# User runtime change\n"
            (target / "PROJECT.md").write_text(project_content, encoding="utf-8")
            (target / ".env").write_text(env_content, encoding="utf-8")
            (target / "wiki/home.md").write_text(runtime_content, encoding="utf-8")
            (target / "WIKI.md").write_text("# target edit\n", encoding="utf-8")
            replace_root = temp / "replace"
            replace_root.mkdir()
            replace_env, _ = self.make_fake_uv(replace_root)
            replaced = subprocess.run(
                command,
                cwd=package,
                env=replace_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(replaced.returncode, 0, replaced.stdout + replaced.stderr)
            self.assertEqual(
                (target / "WIKI.md").read_bytes(),
                (package / "WIKI.md").read_bytes(),
            )
            self.assertEqual((target / "PROJECT.md").read_text(encoding="utf-8"), project_content)
            self.assertEqual((target / ".env").read_text(encoding="utf-8"), env_content)
            self.assertEqual((target / "wiki/home.md").read_text(encoding="utf-8"), runtime_content)

            relative = "docs/newly-owned.md"
            (package / relative).write_text("package content\n", encoding="utf-8")
            inventory = package / "scripts/package-files.txt"
            inventory.write_text(
                inventory.read_text(encoding="utf-8") + f"active {relative}\n",
                encoding="utf-8",
            )
            (target / relative).write_text("target content\n", encoding="utf-8")
            before = self.snapshot_working_tree(target)
            conflict_root = temp / "conflict"
            conflict_root.mkdir()
            conflict_env, conflict_log = self.make_fake_uv(conflict_root)
            conflict = subprocess.run(
                command,
                cwd=package,
                env=conflict_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(conflict.returncode, 0)
            self.assertIn(f"Conflict: {relative}", conflict.stdout + conflict.stderr)
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertFalse(conflict_log.exists())

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            command = self.script_command(
                shell_kind,
                script_name,
                "-TargetRoot",
                target,
                package_root=package,
            )
            setup = subprocess.run(
                command,
                cwd=package,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            relative = "target-only-retired-name.md"
            inventory = package / "scripts/package-files.txt"
            inventory.write_text(
                inventory.read_text(encoding="utf-8") + f"remove {relative}\n",
                encoding="utf-8",
            )
            target_path = target / relative
            target_path.write_text("target-owned content\n", encoding="utf-8")
            before = self.snapshot_working_tree(target)
            file_root = temp / "file-conflict"
            file_root.mkdir()
            file_env, file_log = self.make_fake_uv(file_root)
            file_conflict = subprocess.run(
                command,
                cwd=package,
                env=file_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(file_conflict.returncode, 0)
            self.assertIn(relative, file_conflict.stdout + file_conflict.stderr)
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertFalse(file_log.exists())

            target_path.unlink()
            target_path.mkdir()
            directory_root = temp / "directory-conflict"
            directory_root.mkdir()
            directory_env, directory_log = self.make_fake_uv(directory_root)
            directory_conflict = subprocess.run(
                command,
                cwd=package,
                env=directory_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(directory_conflict.returncode, 0)
            self.assertIn(relative, directory_conflict.stdout + directory_conflict.stderr)
            self.assertTrue(target_path.is_dir())
            self.assertFalse(directory_log.exists())

            target_path.rmdir()
            activation_root = temp / "activation"
            activation_root.mkdir()
            activation_env, _ = self.make_fake_uv(activation_root)
            activation = subprocess.run(
                command,
                cwd=package,
                env=activation_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(activation.returncode, 0, activation.stdout + activation.stderr)
            self.assertIn(
                f"remove {relative}",
                (target / "scripts/package-files.txt").read_text(encoding="utf-8"),
            )

            target_path.write_text("reappeared retired package file\n", encoding="utf-8")
            repeated = subprocess.run(
                command,
                cwd=package,
                env=activation_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
            self.assertFalse(target_path.exists())

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            command = self.script_command(
                shell_kind,
                script_name,
                "-TargetRoot",
                target,
                package_root=package,
            )
            setup = subprocess.run(
                command,
                cwd=package,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            relative = "docs/acknowledgements.md"
            inventory = package / "scripts/package-files.txt"
            inventory.write_text(
                inventory.read_text(encoding="utf-8").replace(
                    f"active {relative}\n", ""
                ),
                encoding="utf-8",
            )
            before = self.snapshot_working_tree(target)
            conflict_root = temp / "conflict"
            conflict_root.mkdir()
            conflict_env, conflict_log = self.make_fake_uv(conflict_root)
            conflict = subprocess.run(
                command,
                cwd=package,
                env=conflict_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(conflict.returncode, 0)
            self.assertIn(relative, conflict.stdout + conflict.stderr)
            self.assertIn("explicit remove", conflict.stdout + conflict.stderr)
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertFalse(conflict_log.exists())

    def assert_metadata_is_committed_last(self, shell_kind: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            target = self.make_target(temp, with_sentinel=False)
            script_name = "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh"
            command = self.script_command(
                shell_kind,
                script_name,
                "-TargetRoot",
                target,
                package_root=package,
            )

            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            setup = subprocess.run(
                command,
                cwd=package,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            target_inventory = target / "scripts/package-files.txt"
            old_inventory = target_inventory.read_bytes()
            (package / "WIKI.md").write_text("# next package contract\n", encoding="utf-8")
            package_inventory = package / "scripts/package-files.txt"
            package_inventory.write_text(
                package_inventory.read_text(encoding="utf-8")
                + "# next inventory generation\n",
                encoding="utf-8",
            )

            failure_root = temp / "failure"
            failure_root.mkdir()
            failure_env, _ = self.make_fake_uv(failure_root, fail_sync=True)
            failed = subprocess.run(
                command,
                cwd=package,
                env=failure_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(
                (target / "WIKI.md").read_text(encoding="utf-8"),
                "# next package contract\n",
            )
            self.assertEqual(target_inventory.read_bytes(), old_inventory)
            self.assertEqual(
                [path.name for path in target_inventory.parent.iterdir() if ".upgrade" in path.name],
                [],
            )

            rerun_root = temp / "rerun"
            rerun_root.mkdir()
            rerun_env, _ = self.make_fake_uv(rerun_root)
            rerun = subprocess.run(
                command,
                cwd=package,
                env=rerun_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
            self.assertEqual(target_inventory.read_bytes(), package_inventory.read_bytes())

    def assert_same_root_metadata_is_never_rewritten(self, shell_kind: str) -> None:
        if shell_kind == "bash" and os.name == "nt":
            self.skipTest("Supported Bash same-root coverage runs on Linux and macOS")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            inventory = package / "scripts/package-files.txt"
            inventory_before = inventory.read_bytes()
            env, call_log = self.make_fake_uv(temp)
            result = subprocess.run(
                self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    package,
                    package_root=package,
                ),
                cwd=package,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(inventory.read_bytes(), inventory_before)
            self.assertEqual(
                call_log.read_text(encoding="utf-8").splitlines(),
                [
                    "lock --check --default-index https://pypi.org/simple",
                    "sync --locked --default-index https://pypi.org/simple",
                ],
            )

    def assert_interrupted_initial_metadata_activation_is_conservative(
        self, shell_kind: str
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            relative = "docs/interrupted-first-adoption.md"
            (package / relative).write_text("package content\n", encoding="utf-8")
            inventory = package / "scripts/package-files.txt"
            inventory.write_text(
                inventory.read_text(encoding="utf-8") + f"active {relative}\n",
                encoding="utf-8",
            )
            target = self.make_target(temp, with_sentinel=False)
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
                package_root=package,
            )

            failure_root = temp / "failure"
            failure_root.mkdir()
            failure_env, _ = self.make_fake_uv(failure_root, fail_sync=True)
            interrupted = subprocess.run(
                command,
                cwd=package,
                env=failure_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertTrue((target / relative).is_file())
            self.assertFalse((target / "scripts/package-files.txt").exists())

            (target / relative).write_text("user edit after interruption\n", encoding="utf-8")
            rerun_root = temp / "rerun"
            rerun_root.mkdir()
            rerun_env, rerun_log = self.make_fake_uv(rerun_root)
            rerun = subprocess.run(
                command,
                cwd=package,
                env=rerun_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rerun.returncode, 0)
            self.assertIn(relative, rerun.stdout + rerun.stderr)
            self.assertIn("different content", rerun.stdout + rerun.stderr)
            self.assertEqual(
                (target / relative).read_text(encoding="utf-8"),
                "user edit after interruption\n",
            )
            self.assertFalse(rerun_log.exists())

    def assert_future_tombstone_is_applied_and_resumable(self, shell_kind: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            target = self.make_target(temp, with_sentinel=False)
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
                package_root=package,
            )
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            setup = subprocess.run(
                command,
                cwd=package,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            relative = "docs/acknowledgements.md"
            package_inventory = package / "scripts/package-files.txt"
            package_inventory.write_text(
                package_inventory.read_text(encoding="utf-8").replace(
                    f"active {relative}\n", f"remove {relative}\n"
                ),
                encoding="utf-8",
            )
            (package / relative).unlink()

            update_root = temp / "update"
            update_root.mkdir()
            update_env, _ = self.make_fake_uv(update_root)
            updated = subprocess.run(
                command,
                cwd=package,
                env=update_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(updated.returncode, 0, updated.stdout + updated.stderr)
            self.assertFalse((target / relative).exists())
            self.assertIn(
                f"remove {relative}",
                (target / "scripts/package-files.txt").read_text(encoding="utf-8"),
            )

            (target / relative).write_text("reappeared old package file\n", encoding="utf-8")
            resumed = subprocess.run(
                command,
                cwd=package,
                env=update_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
            self.assertFalse((target / relative).exists())

            package_inventory.write_text(
                package_inventory.read_text(encoding="utf-8").replace(
                    f"remove {relative}\n", ""
                ),
                encoding="utf-8",
            )
            before = self.snapshot_working_tree(target)
            dropped_root = temp / "dropped"
            dropped_root.mkdir()
            dropped_env, dropped_log = self.make_fake_uv(dropped_root)
            dropped = subprocess.run(
                command,
                cwd=package,
                env=dropped_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(dropped.returncode, 0)
            self.assertIn("old retired package path is absent", dropped.stdout + dropped.stderr)
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertFalse(dropped_log.exists())

    def assert_new_inventory_schema_guard(self, shell_kind: str) -> None:
        marker = "# inventory-schema: 1"
        cases = {
            "missing_schema": lambda text: text.replace(marker + "\n", ""),
            "duplicate_schema": lambda text: text + marker + "\n",
            "unsupported_schema": lambda text: text.replace(marker, "# inventory-schema: 2"),
            "invalid_line": lambda text: text + "file WIKI.md\n",
            "duplicate_path": lambda text: text + "active WIKI.md\n",
            "missing_source": lambda text: text + "active docs/missing-source.md\n",
            "remove_self": lambda text: text.replace(
                "active scripts/package-files.txt\n",
                "remove scripts/package-files.txt\n",
            ),
            "missing_self": lambda text: text.replace(
                "active scripts/package-files.txt\n", ""
            ),
        }
        for case, mutate in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                package = self.make_package_copy(temp)
                inventory = package / "scripts/package-files.txt"
                inventory.write_text(
                    mutate(inventory.read_text(encoding="utf-8")),
                    encoding="utf-8",
                )
                target = self.make_target(temp, with_sentinel=False)
                before = self.snapshot_working_tree(target)
                run_root = temp / "run"
                run_root.mkdir()
                env, call_log = self.make_fake_uv(run_root)
                result = subprocess.run(
                    self.script_command(
                        shell_kind,
                        "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                        "-TargetRoot",
                        target,
                        package_root=package,
                    ),
                    cwd=package,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0, case)
                self.assertEqual(self.snapshot_working_tree(target), before)
                self.assertFalse(call_log.exists())
    def assert_lock_failure_has_no_target_writes(self, shell_kind: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            before = self.snapshot_working_tree(target)
            env, call_log = self.make_fake_uv(temp, fail_lock=True)
            result = subprocess.run(
                self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    target,
                ),
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lock is stale", (result.stdout + result.stderr).lower())
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertEqual(
                call_log.read_text(encoding="utf-8").splitlines(),
                ["lock --check --default-index https://pypi.org/simple"],
            )

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

    def assert_source_link_preflight(self, shell_kind: str) -> None:
        if os.name == "nt":
            self.skipTest("POSIX source symlink coverage runs on Linux and macOS")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            package = self.make_package_copy(temp)
            external_docs = temp / "external-docs"
            (package / "docs").rename(external_docs)
            (package / "docs").symlink_to(external_docs, target_is_directory=True)
            target = temp / "target"
            target.mkdir()
            before = self.snapshot_working_tree(target)
            run_root = temp / "run"
            run_root.mkdir()
            env, call_log = self.make_fake_uv(run_root)
            result = subprocess.run(
                self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    target,
                    package_root=package,
                ),
                cwd=package,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("link", (result.stdout + result.stderr).lower())
            self.assertEqual(self.snapshot_working_tree(target), before)
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


    def test_powershell_package_ownership_guard(self) -> None:
        self.assert_ownership_guard("powershell")

    def test_bash_package_ownership_guard(self) -> None:
        self.assert_ownership_guard("bash")

    def test_powershell_ownership_metadata_is_committed_last(self) -> None:
        self.assert_metadata_is_committed_last("powershell")

    def test_bash_ownership_metadata_is_committed_last(self) -> None:
        self.assert_metadata_is_committed_last("bash")

    def test_powershell_same_root_metadata_is_never_rewritten(self) -> None:
        self.assert_same_root_metadata_is_never_rewritten("powershell")

    def test_bash_same_root_metadata_is_never_rewritten(self) -> None:
        self.assert_same_root_metadata_is_never_rewritten("bash")

    def test_powershell_interrupted_first_adoption_is_conservative(self) -> None:
        self.assert_interrupted_initial_metadata_activation_is_conservative(
            "powershell"
        )

    def test_bash_interrupted_first_adoption_is_conservative(self) -> None:
        self.assert_interrupted_initial_metadata_activation_is_conservative("bash")

    def test_powershell_future_tombstone_is_applied_and_resumable(self) -> None:
        self.assert_future_tombstone_is_applied_and_resumable("powershell")

    def test_bash_future_tombstone_is_applied_and_resumable(self) -> None:
        self.assert_future_tombstone_is_applied_and_resumable("bash")

    def test_powershell_new_inventory_schema_guard(self) -> None:
        self.assert_new_inventory_schema_guard("powershell")

    def test_bash_new_inventory_schema_guard(self) -> None:
        self.assert_new_inventory_schema_guard("bash")

    def test_powershell_target_structure_preflight(self) -> None:
        self.assert_structure_preflight("powershell")

    def test_bash_target_structure_preflight(self) -> None:
        self.assert_structure_preflight("bash")

    def test_powershell_rejects_linked_package_sources(self) -> None:
        self.assert_source_link_preflight("powershell")

    def test_bash_rejects_linked_package_sources(self) -> None:
        self.assert_source_link_preflight("bash")

    def test_powershell_missing_uv_has_no_target_writes(self) -> None:
        self.assert_missing_uv_has_no_target_writes("powershell")

    def test_bash_missing_uv_has_no_target_writes(self) -> None:
        self.assert_missing_uv_has_no_target_writes("bash")

    def test_powershell_lock_failure_has_no_target_writes(self) -> None:
        self.assert_lock_failure_has_no_target_writes("powershell")

    def test_bash_lock_failure_has_no_target_writes(self) -> None:
        self.assert_lock_failure_has_no_target_writes("bash")

if __name__ == "__main__":
    unittest.main()
