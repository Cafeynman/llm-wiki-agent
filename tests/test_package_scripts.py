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
RETIRED_PACKAGE_FILE = ".agents/skills/markitdown-skill/README.md"
MANAGED_DIRECTORIES = ("docs", "scenarios", "scripts", ".agents/skills")


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
        manifest_lines = (ROOT / "scripts/upgrade-manifest.txt").read_text(
            encoding="utf-8"
        ).splitlines()
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
        for line in manifest_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            kind, relative = stripped.split(maxsplit=1)
            if kind == "file":
                package_files.add(relative)
        package_files.update(
            {
                "PROJECT.md",
                ".gitignore",
                "scripts/upgrade-manifest.txt",
                "scripts/package-files.txt",
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

    def convert_target_metadata_to_legacy(self, target: Path) -> None:
        manifest = target / "scripts/upgrade-manifest.txt"
        manifest_lines = manifest.read_text(encoding="utf-8").splitlines()
        manifest.write_text(
            "\n".join(line for line in manifest_lines if line != "inventory all")
            + "\n",
            encoding="utf-8",
        )
        non_directory_paths = {
            relative
            for kind, relative in (
                line.split(maxsplit=1)
                for line in manifest_lines
                if line and not line.startswith("#") and line != "inventory all"
            )
            if kind in {"file", "remove"}
        }
        inventory = target / "scripts/package-files.txt"
        typed_inventory = [
            line.split(maxsplit=1)
            for line in inventory.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        ]
        inventory.write_text(
            "# Legacy directory-only ownership inventory.\n"
            + "\n".join(
                relative
                for state, relative in typed_inventory
                if state == "active" and relative not in non_directory_paths
            )
            + "\n",
            encoding="utf-8",
        )

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

    def assert_owned_retired_package_file_cleanup(self, shell_kind: str) -> None:
        for state in ("owned_file", "owned_missing", "owned_directory"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = self.make_target(temp, with_sentinel=True)
                env, call_log = self.make_fake_uv(temp)
                command = self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    target,
                )
                first = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

                retired = target / RETIRED_PACKAGE_FILE
                target_only = target / ".agents/skills/self-improving-agent/user-owned.txt"
                retired.parent.mkdir(parents=True, exist_ok=True)
                if state == "owned_directory":
                    retired.mkdir()
                elif state == "owned_file":
                    retired.write_text("old package documentation\n", encoding="utf-8")

                old_manifest = target / "scripts/upgrade-manifest.txt"
                old_manifest.write_text(
                    "\n".join(
                        line
                        for line in old_manifest.read_text(encoding="utf-8").splitlines()
                        if line != f"remove {RETIRED_PACKAGE_FILE}"
                    )
                    + "\n",
                    encoding="utf-8",
                )
                old_inventory = target / "scripts/package-files.txt"
                old_inventory.write_text(
                    old_inventory.read_text(encoding="utf-8").replace(
                        f"remove {RETIRED_PACKAGE_FILE}\n",
                        f"active {RETIRED_PACKAGE_FILE}\n",
                    ),
                    encoding="utf-8",
                )

                before = self.snapshot_working_tree(target)
                call_log.unlink()
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )

                if state == "owned_directory":
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f"Conflict: {RETIRED_PACKAGE_FILE}", result.stdout + result.stderr)
                    self.assertIn("directory", result.stdout + result.stderr)
                    self.assertEqual(self.snapshot_working_tree(target), before)
                    self.assertFalse(call_log.exists())
                else:
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertFalse(retired.exists())
                    self.assertEqual(target_only.read_text(encoding="utf-8"), "keep me\n")
                    self.assertTrue(call_log.exists())
                    after = self.snapshot_working_tree(target)
                    second = subprocess.run(
                        command,
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
                    self.assertEqual(self.snapshot_working_tree(target), after)

    def assert_continued_tombstone_cleanup(self, shell_kind: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            env, call_log = self.make_fake_uv(temp)
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
            )
            first = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            retired = target / RETIRED_PACKAGE_FILE
            retired.parent.mkdir(parents=True, exist_ok=True)
            retired.write_text("unexpected retired package file\n", encoding="utf-8")
            call_log.unlink()
            second = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertFalse(retired.exists())
            self.assertTrue(call_log.exists())

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

    def test_manifest_leaves_runtime_adapters_user_owned(self) -> None:
        manifest = (ROOT / "scripts/upgrade-manifest.txt").read_text(encoding="utf-8")
        inventory = (ROOT / "scripts/package-files.txt").read_text(encoding="utf-8")
        self.assertEqual(manifest.splitlines().count("inventory all"), 1)
        self.assertEqual(
            inventory.splitlines().count("# inventory-format: complete"), 1
        )
        self.assertNotIn("file CLAUDE.md", manifest.splitlines())
        self.assertIn(f"remove {RETIRED_PACKAGE_FILE}", manifest.splitlines())

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
            [git, "-c", "core.quotepath=false", "ls-files", *MANAGED_DIRECTORIES],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        tracked = set(result.stdout.splitlines())
        manifest_entries = [
            line.strip().split(maxsplit=1)
            for line in (ROOT / "scripts/upgrade-manifest.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        tracked.update(relative for kind, relative in manifest_entries if kind == "file")
        retired = {relative for kind, relative in manifest_entries if kind == "remove"}
        expected_inventory = {("active", relative) for relative in tracked}
        expected_inventory.update(("remove", relative) for relative in retired)
        self.assertEqual(inventory, expected_inventory)

    def test_upgrade_ignores_untracked_files_inside_managed_directories(self) -> None:
        source_only = ROOT / "docs/untracked-upgrade-sentinel.txt"
        self.assertFalse(source_only.exists())
        source_only.write_text("must not be copied\n", encoding="utf-8")
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = self.make_target(temp, with_sentinel=False)
                env, _ = self.make_fake_uv(temp)
                result = subprocess.run(
                    self.script_command("powershell", "upgrade.ps1", "-TargetRoot", target),
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse((target / "docs/untracked-upgrade-sentinel.txt").exists())
        finally:
            source_only.unlink(missing_ok=True)

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
        self.assertIn("manifest.txt\" ]] && metadata_order=1", bash)
        self.assertIn("package-files.txt\" ]] && metadata_order=2", bash)

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

            self.convert_target_metadata_to_legacy(target)
            source.write_text("第三版\n", encoding="utf-8")
            third = subprocess.run(
                command,
                cwd=package,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(third.returncode, 0, third.stdout + third.stderr)
            self.assertEqual((target / relative).read_text(encoding="utf-8"), "第三版\n")
            self.assertIn(
                "# inventory-format: complete",
                (target / "scripts/package-files.txt").read_text(encoding="utf-8"),
            )

            (target / "scripts/upgrade-manifest.txt").unlink()
            source.write_text("第四版\n", encoding="utf-8")
            fourth = subprocess.run(
                command,
                cwd=package,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(fourth.returncode, 0, fourth.stdout + fourth.stderr)
            self.assertEqual((target / relative).read_text(encoding="utf-8"), "第四版\n")

    def test_windows_powershell_51_resumes_initial_inventory_checkpoint(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows PowerShell 5.1 coverage")
        shell = shutil.which("powershell")
        if shell is None:
            self.skipTest("Windows PowerShell is not available")

        for missing_metadata in ("manifest", "inventory"):
            with self.subTest(missing_metadata=missing_metadata), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                package = self.make_package_copy(temp)
                relative = "docs/首次检查点恢复.md"
                (package / relative).write_text("包内容\n", encoding="utf-8")
                manifest = package / "scripts/upgrade-manifest.txt"
                inventory = package / "scripts/package-files.txt"
                inventory.write_text(
                    inventory.read_text(encoding="utf-8")
                    + f"active {relative}\n",
                    encoding="utf-8",
                )
                manifest_bytes = manifest.read_bytes()
                inventory_bytes = inventory.read_bytes()
                removed_source = (
                    manifest if missing_metadata == "manifest" else inventory
                )
                target = self.make_target(temp, with_sentinel=False)
                failure_root = temp / "failure"
                failure_root.mkdir()
                failure_env, _ = self.make_fake_uv(
                    failure_root, remove_on_sync=removed_source
                )
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
                interrupted = subprocess.run(
                    command,
                    cwd=package,
                    env=failure_env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(interrupted.returncode, 0)
                checkpoint = (target / "scripts/package-files.txt").read_text(
                    encoding="utf-8"
                )
                self.assertEqual(
                    [
                        line
                        for line in checkpoint.splitlines()
                        if line and not line.startswith("#")
                    ],
                    ["active scripts/package-files.txt"],
                )

                manifest.write_bytes(manifest_bytes)
                inventory.write_bytes(inventory_bytes)
                rerun_root = temp / "rerun"
                rerun_root.mkdir()
                rerun_env, call_log = self.make_fake_uv(rerun_root)
                rerun = subprocess.run(
                    command,
                    cwd=package,
                    env=rerun_env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
                self.assertTrue(call_log.exists())
                self.assertEqual(
                    (target / relative).read_text(encoding="utf-8"), "包内容\n"
                )
                self.assertEqual(
                    (target / "scripts/upgrade-manifest.txt").read_bytes(),
                    manifest_bytes,
                )
                self.assertEqual(
                    (target / "scripts/package-files.txt").read_bytes(),
                    inventory_bytes,
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

    def test_powershell_retires_a_path_owned_by_the_old_inventory(self) -> None:
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

            retired = target / RETIRED_PACKAGE_FILE
            retired.parent.mkdir(parents=True, exist_ok=True)
            retired.write_text("old package documentation\n", encoding="utf-8")
            old_manifest = target / "scripts/upgrade-manifest.txt"
            old_manifest.write_text(
                "\n".join(
                    line
                    for line in old_manifest.read_text(encoding="utf-8").splitlines()
                    if line != f"remove {RETIRED_PACKAGE_FILE}"
                )
                + "\n",
                encoding="utf-8",
            )
            old_inventory = target / "scripts/package-files.txt"
            old_inventory.write_text(
                old_inventory.read_text(encoding="utf-8").replace(
                    f"remove {RETIRED_PACKAGE_FILE}\n",
                    f"active {RETIRED_PACKAGE_FILE}\n",
                ),
                encoding="utf-8",
            )
            call_log.unlink()
            second = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertFalse(retired.exists())

    def test_powershell_rejects_partial_old_ownership_metadata_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            (target / "scripts").mkdir(parents=True)
            (target / "scripts/upgrade-manifest.txt").write_text(
                "file WIKI.md\n",
                encoding="utf-8",
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
            self.assertIn("ownership metadata", (result.stdout + result.stderr).lower())
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertFalse(call_log.exists())

    def test_powershell_rejects_invalid_utf8_old_metadata_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            scripts = target / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "upgrade-manifest.txt").write_bytes(b"file WIKI.md\n")
            (scripts / "package-files.txt").write_bytes(b"WIKI.md\n\xff\n")
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
        self.assertIn("old `scripts/upgrade-manifest.txt`", usage)
        self.assertIn("target Git history is not consulted", usage)
        self.assertIn("blocks the upgrade before target writes", usage)
        self.assertIn("links or reparse points", usage)
        self.assertIn("declares `inventory all`", usage)
        self.assertIn("declares `# inventory-format: complete`", usage)
        self.assertIn("`active <path>` and `remove <path>`", usage)
        self.assertIn("legacy inventory is first replaced atomically", usage)
        self.assertIn("rejects Windows runtimes", usage)
        self.assertNotIn("tracked and clean", usage)
        self.assertIn("旧 `scripts/upgrade-manifest.txt`", usage_zh)
        self.assertIn("不读取目标 Git 历史", usage_zh)
        self.assertIn("在写入目标前停止", usage_zh)
        self.assertIn("目录联接", usage_zh)
        self.assertIn("声明 `inventory all`", usage_zh)
        self.assertIn("声明 `# inventory-format: complete`", usage_zh)
        self.assertIn("`active <path>` 与 `remove <path>`", usage_zh)
        self.assertIn("先把旧 inventory 原子替换", usage_zh)
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
        for script_name, parameter in (
            ("init.ps1" if shell_kind == "powershell" else "init.sh", "-VaultRoot"),
            ("upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh", "-TargetRoot"),
        ):
            with self.subTest(script=script_name, case="legacy_conflict"), tempfile.TemporaryDirectory() as temp_dir:
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

            with self.subTest(script=script_name, case="legacy_identical_adoption"), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = temp / "target"
                target.mkdir()
                (target / "WIKI.md").write_bytes((ROOT / "WIKI.md").read_bytes())
                env, call_log = self.make_fake_uv(temp)
                result = subprocess.run(
                    self.script_command(shell_kind, script_name, parameter, target),
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(
                    (target / "WIKI.md").read_bytes(),
                    (ROOT / "WIKI.md").read_bytes(),
                )
                self.assertTrue((target / "scripts/upgrade-manifest.txt").is_file())
                self.assertTrue(call_log.exists())

            with self.subTest(script=script_name, case="owned_reconciliation"), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = self.make_target(temp, with_sentinel=True)
                env, call_log = self.make_fake_uv(temp)
                command = self.script_command(shell_kind, script_name, parameter, target)
                first = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

                (target / "WIKI.md").write_text("# Previous package contract\n", encoding="utf-8")
                (target / "AGENTS.md").unlink()
                (target / "PROJECT.md").write_text("# Project\n\nkeep project choices\n", encoding="utf-8")
                (target / ".env").write_text("PRIVATE_SETTING=preserve\n", encoding="utf-8")
                runtime_page = target / "wiki/home.md"
                runtime_page.write_text("# User runtime change\n", encoding="utf-8")
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
                self.assertEqual((target / "AGENTS.md").read_bytes(), (ROOT / "AGENTS.md").read_bytes())
                self.assertEqual((target / "PROJECT.md").read_text(encoding="utf-8"), "# Project\n\nkeep project choices\n")
                self.assertEqual((target / ".env").read_text(encoding="utf-8"), "PRIVATE_SETTING=preserve\n")
                self.assertEqual(runtime_page.read_text(encoding="utf-8"), "# User runtime change\n")
                self.assertEqual(
                    (target / ".agents/skills/self-improving-agent/user-owned.txt").read_text(encoding="utf-8"),
                    "keep me\n",
                )
                self.assertEqual(len(call_log.read_text(encoding="utf-8").splitlines()), 2)
                after = self.snapshot_working_tree(target)
                third = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(third.returncode, 0, third.stdout + third.stderr)
                self.assertEqual(self.snapshot_working_tree(target), after)

            for conflict_case in (
                "new_claim",
                "missing_retirement",
                "partial_metadata",
                "unmarked_inventory_only",
                "malformed_metadata",
                "duplicate_metadata",
                "legacy_tombstone",
            ):
                with self.subTest(script=script_name, case=conflict_case), tempfile.TemporaryDirectory() as temp_dir:
                    temp = Path(temp_dir)
                    target = temp / "target"
                    target.mkdir()

                    if conflict_case in ("new_claim", "missing_retirement"):
                        setup_root = temp / "setup"
                        setup_root.mkdir()
                        setup_target = self.make_target(setup_root, with_sentinel=False)
                        setup_env, _ = self.make_fake_uv(setup_root)
                        setup_command = self.script_command(shell_kind, script_name, parameter, setup_target)
                        setup = subprocess.run(
                            setup_command,
                            cwd=ROOT,
                            env=setup_env,
                            capture_output=True,
                            text=True,
                        )
                        self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
                        target = setup_target
                        old_manifest = target / "scripts/upgrade-manifest.txt"
                        if conflict_case == "new_claim":
                            old_manifest.write_text(
                                "\n".join(
                                    line
                                    for line in old_manifest.read_text(encoding="utf-8").splitlines()
                                    if line != "file WIKI.md"
                                )
                                + "\n",
                                encoding="utf-8",
                            )
                            old_inventory = target / "scripts/package-files.txt"
                            old_inventory.write_text(
                                "\n".join(
                                    line
                                    for line in old_inventory.read_text(
                                        encoding="utf-8"
                                    ).splitlines()
                                    if line != "active WIKI.md"
                                )
                                + "\n",
                                encoding="utf-8",
                            )
                            (target / "WIKI.md").write_text("# Target-owned contract\n", encoding="utf-8")
                        else:
                            old_manifest.write_text(
                                old_manifest.read_text(encoding="utf-8") + "file legacy-owned.md\n",
                                encoding="utf-8",
                            )
                            old_inventory = target / "scripts/package-files.txt"
                            old_inventory.write_text(
                                old_inventory.read_text(encoding="utf-8")
                                + "active legacy-owned.md\n",
                                encoding="utf-8",
                            )
                            (target / "legacy-owned.md").write_text("old package file\n", encoding="utf-8")
                    elif conflict_case == "partial_metadata":
                        (target / "scripts").mkdir()
                        (target / "scripts/upgrade-manifest.txt").write_text("file WIKI.md\n", encoding="utf-8")
                    elif conflict_case == "unmarked_inventory_only":
                        (target / "scripts").mkdir()
                        (target / "scripts/package-files.txt").write_text(
                            "WIKI.md\n", encoding="utf-8"
                        )
                    elif conflict_case == "malformed_metadata":
                        (target / "scripts").mkdir()
                        (target / "scripts/upgrade-manifest.txt").write_text("dir scripts\n", encoding="utf-8")
                        (target / "scripts/package-files.txt").write_text("../escape.md\n", encoding="utf-8")
                    elif conflict_case == "duplicate_metadata":
                        (target / "scripts").mkdir()
                        (target / "scripts/upgrade-manifest.txt").write_text(
                            "dir docs\n",
                            encoding="utf-8",
                        )
                        (target / "scripts/package-files.txt").write_text(
                            "docs/example.md\nDOCS/EXAMPLE.md\n",
                            encoding="utf-8",
                        )
                    else:
                        retired = target / RETIRED_PACKAGE_FILE
                        retired.parent.mkdir(parents=True)
                        retired.write_text("target-owned legacy file\n", encoding="utf-8")

                    before = self.snapshot_working_tree(target)
                    run_root = temp / "run"
                    run_root.mkdir()
                    env, call_log = self.make_fake_uv(run_root)
                    result = subprocess.run(
                        self.script_command(shell_kind, script_name, parameter, target),
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    output = result.stdout + result.stderr
                    expected = {
                        "new_claim": "Conflict: WIKI.md",
                        "missing_retirement": "legacy-owned.md",
                        "partial_metadata": "ownership metadata",
                        "unmarked_inventory_only": "standalone inventory",
                        "malformed_metadata": "invalid package path",
                        "duplicate_metadata": "duplicate package path",
                        "legacy_tombstone": RETIRED_PACKAGE_FILE,
                    }[conflict_case]
                    self.assertIn(expected, output)
                    self.assertEqual(self.snapshot_working_tree(target), before)
                    self.assertFalse(call_log.exists())

    def assert_metadata_is_committed_last(self, shell_kind: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
            )
            setup = subprocess.run(
                command,
                cwd=ROOT,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            old_manifest = target / "scripts/upgrade-manifest.txt"
            old_manifest.write_text(
                "# prior ownership metadata\n" + old_manifest.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            old_inventory = target / "scripts/package-files.txt"
            old_inventory.write_text(
                "# prior ownership inventory\n"
                + old_inventory.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            prior_metadata = {
                "manifest": old_manifest.read_bytes(),
                "inventory": old_inventory.read_bytes(),
            }
            (target / "WIKI.md").write_text("# Previous package contract\n", encoding="utf-8")
            failure_root = temp / "failure"
            failure_root.mkdir()
            failure_env, _ = self.make_fake_uv(failure_root, fail_sync=True)
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=failure_env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(old_manifest.read_bytes(), prior_metadata["manifest"])
            self.assertEqual(old_inventory.read_bytes(), prior_metadata["inventory"])

    def assert_same_root_metadata_is_never_rewritten(self, shell_kind: str) -> None:
        if shell_kind == "bash" and os.name == "nt":
            self.skipTest("Supported Bash same-root coverage runs on Linux and macOS")

        script_name = "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh"
        for metadata_mode in ("complete", "legacy", "missing"):
            with self.subTest(metadata_mode=metadata_mode), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                package = self.make_package_copy(temp)
                manifest = package / "scripts/upgrade-manifest.txt"
                inventory = package / "scripts/package-files.txt"
                if metadata_mode == "legacy":
                    self.convert_target_metadata_to_legacy(package)
                elif metadata_mode == "missing":
                    manifest.unlink()
                    inventory.unlink()

                before = self.snapshot_working_tree(package)
                metadata_before = {
                    "manifest": manifest.read_bytes() if manifest.exists() else None,
                    "inventory": inventory.read_bytes() if inventory.exists() else None,
                }
                run_root = temp / "run"
                run_root.mkdir()
                env, call_log = self.make_fake_uv(run_root)
                result = subprocess.run(
                    self.script_command(
                        shell_kind,
                        script_name,
                        "-TargetRoot",
                        package,
                        package_root=package,
                    ),
                    cwd=package,
                    env=env,
                    capture_output=True,
                    text=True,
                )

                if metadata_mode == "complete":
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(
                        call_log.read_text(encoding="utf-8").splitlines(),
                        [
                            "lock --check --default-index https://pypi.org/simple",
                            "sync --locked --default-index https://pypi.org/simple",
                        ],
                    )
                    self.assertTrue((package / "wiki/home.md").is_file())
                    self.assertEqual(manifest.read_bytes(), metadata_before["manifest"])
                    self.assertEqual(inventory.read_bytes(), metadata_before["inventory"])
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.snapshot_working_tree(package), before)
                    self.assertFalse(call_log.exists())

    def assert_interrupted_metadata_activation_is_conservative(
        self, shell_kind: str
    ) -> None:
        temp_parent = ROOT / "tmp" if shell_kind == "bash" and os.name == "nt" else None
        if temp_parent is not None:
            temp_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_parent) as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            setup_command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
            )
            setup = subprocess.run(
                setup_command,
                cwd=ROOT,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            package = self.make_package_copy(temp)
            new_relative = "docs/interrupted-owned.md"
            new_source = package / new_relative
            new_source.write_text("new package content\n", encoding="utf-8")
            package_manifest = package / "scripts/upgrade-manifest.txt"
            package_manifest.write_text(
                "# interrupted metadata generation\n"
                + package_manifest.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            package_inventory = package / "scripts/package-files.txt"
            package_inventory.write_text(
                package_inventory.read_text(encoding="utf-8")
                + f"active {new_relative}\n",
                encoding="utf-8",
            )
            inventory_bytes = package_inventory.read_bytes()
            old_inventory_bytes = (target / "scripts/package-files.txt").read_bytes()

            failure_root = temp / "failure"
            failure_root.mkdir()
            failure_env, _ = self.make_fake_uv(
                failure_root,
                remove_on_sync=package_inventory,
            )
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
                package_root=package,
            )
            interrupted = subprocess.run(
                command,
                cwd=package,
                env=failure_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertTrue((target / new_relative).is_file())
            self.assertIn(
                "interrupted metadata generation",
                (target / "scripts/upgrade-manifest.txt").read_text(encoding="utf-8"),
                interrupted.stdout + interrupted.stderr,
            )
            self.assertEqual(
                (target / "scripts/package-files.txt").read_bytes(),
                old_inventory_bytes,
            )

            package_inventory.write_bytes(inventory_bytes)
            (target / new_relative).write_text(
                "user edit after interrupted upgrade\n",
                encoding="utf-8",
            )
            rerun_root = temp / "rerun"
            rerun_root.mkdir()
            rerun_env, call_log = self.make_fake_uv(rerun_root)
            rerun = subprocess.run(
                command,
                cwd=package,
                env=rerun_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rerun.returncode, 0)
            self.assertIn(new_relative, rerun.stdout + rerun.stderr)
            self.assertIn("different content", rerun.stdout + rerun.stderr)
            self.assertEqual(
                (target / new_relative).read_text(encoding="utf-8"),
                "user edit after interrupted upgrade\n",
            )
            self.assertFalse(call_log.exists())
            self.assertEqual(
                [path.name for path in (target / "scripts").iterdir() if ".upgrade" in path.name],
                [],
            )

    def assert_interrupted_legacy_metadata_activation_is_conservative(
        self, shell_kind: str
    ) -> None:
        for missing_metadata in ("manifest", "inventory"):
            with self.subTest(missing_metadata=missing_metadata), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = self.make_target(temp, with_sentinel=False)
                setup_root = temp / "setup"
                setup_root.mkdir()
                setup_env, _ = self.make_fake_uv(setup_root)
                setup_command = self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    target,
                )
                setup = subprocess.run(
                    setup_command,
                    cwd=ROOT,
                    env=setup_env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
                self.convert_target_metadata_to_legacy(target)
                legacy_manifest_lines = [
                    line
                    for line in (
                        target / "scripts/upgrade-manifest.txt"
                    ).read_text(encoding="utf-8").splitlines()
                    if line and not line.startswith("#")
                ]
                expected_checkpoint_records = {
                    f"active {line}"
                    for line in (
                        target / "scripts/package-files.txt"
                    ).read_text(encoding="utf-8").splitlines()
                    if line and not line.startswith("#")
                }
                for line in legacy_manifest_lines:
                    kind, relative = line.split(maxsplit=1)
                    if kind == "file":
                        expected_checkpoint_records.add(f"active {relative}")
                    elif kind == "remove":
                        expected_checkpoint_records.add(f"remove {relative}")

                package = self.make_package_copy(temp)
                new_relative = "docs/legacy-transition-owned.md"
                (package / new_relative).write_text(
                    "new package content\n", encoding="utf-8"
                )
                package_manifest = package / "scripts/upgrade-manifest.txt"
                package_manifest.write_text(
                    "# legacy transition generation\n"
                    + package_manifest.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                package_inventory = package / "scripts/package-files.txt"
                package_inventory.write_text(
                    package_inventory.read_text(encoding="utf-8")
                    + f"active {new_relative}\n",
                    encoding="utf-8",
                )
                manifest_bytes = package_manifest.read_bytes()
                inventory_bytes = package_inventory.read_bytes()
                removed_source = (
                    package_manifest
                    if missing_metadata == "manifest"
                    else package_inventory
                )

                failure_root = temp / "failure"
                failure_root.mkdir()
                failure_env, _ = self.make_fake_uv(
                    failure_root,
                    remove_on_sync=removed_source,
                )
                command = self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    target,
                    package_root=package,
                )
                interrupted = subprocess.run(
                    command,
                    cwd=package,
                    env=failure_env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(interrupted.returncode, 0)
                self.assertTrue((target / new_relative).is_file())
                target_inventory = (target / "scripts/package-files.txt").read_text(
                    encoding="utf-8"
                )
                self.assertIn("# inventory-format: complete", target_inventory)
                self.assertNotIn(new_relative, target_inventory)
                self.assertEqual(
                    {
                        line
                        for line in target_inventory.splitlines()
                        if line and not line.startswith("#")
                    },
                    expected_checkpoint_records,
                )
                target_manifest = (target / "scripts/upgrade-manifest.txt").read_text(
                    encoding="utf-8"
                )
                if missing_metadata == "manifest":
                    self.assertNotIn("inventory all", target_manifest)
                else:
                    self.assertIn("legacy transition generation", target_manifest)

                package_manifest.write_bytes(manifest_bytes)
                package_inventory.write_bytes(inventory_bytes)
                edited_target = temp / "edited-target"
                shutil.copytree(target, edited_target)

                clean_root = temp / "clean-rerun"
                clean_root.mkdir()
                clean_env, clean_call_log = self.make_fake_uv(clean_root)
                clean_rerun = subprocess.run(
                    command,
                    cwd=package,
                    env=clean_env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    clean_rerun.returncode,
                    0,
                    clean_rerun.stdout + clean_rerun.stderr,
                )
                self.assertTrue(clean_call_log.exists())
                self.assertEqual(
                    (target / new_relative).read_text(encoding="utf-8"),
                    "new package content\n",
                )
                self.assertEqual(
                    (target / "scripts/upgrade-manifest.txt").read_bytes(),
                    manifest_bytes,
                )
                self.assertEqual(
                    (target / "scripts/package-files.txt").read_bytes(),
                    inventory_bytes,
                )

                (edited_target / new_relative).write_text(
                    "user edit after interrupted legacy transition\n",
                    encoding="utf-8",
                )
                rerun_root = temp / "rerun"
                rerun_root.mkdir()
                rerun_env, call_log = self.make_fake_uv(rerun_root)
                edited_command = self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    edited_target,
                    package_root=package,
                )
                rerun = subprocess.run(
                    edited_command,
                    cwd=package,
                    env=rerun_env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(rerun.returncode, 0)
                rerun_output = rerun.stdout + rerun.stderr
                self.assertIn(new_relative, rerun_output)
                self.assertIn("different content", rerun_output)
                self.assertNotIn(
                    "scripts/package-files.txt: new package-owned path", rerun_output
                )
                self.assertEqual(
                    (edited_target / new_relative).read_text(encoding="utf-8"),
                    "user edit after interrupted legacy transition\n",
                )
                self.assertFalse(call_log.exists())

    def assert_interrupted_initial_metadata_activation_is_conservative(
        self, shell_kind: str
    ) -> None:
        for missing_metadata in ("manifest", "inventory"):
            with self.subTest(missing_metadata=missing_metadata), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                target = self.make_target(temp, with_sentinel=False)
                package = self.make_package_copy(temp)
                new_relative = "docs/initial-transition-owned.md"
                (package / new_relative).write_text(
                    "new package content\n", encoding="utf-8"
                )
                package_manifest = package / "scripts/upgrade-manifest.txt"
                package_manifest.write_text(
                    "# initial transition generation\n"
                    + package_manifest.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                package_inventory = package / "scripts/package-files.txt"
                package_inventory.write_text(
                    package_inventory.read_text(encoding="utf-8")
                    + f"active {new_relative}\n",
                    encoding="utf-8",
                )
                manifest_bytes = package_manifest.read_bytes()
                inventory_bytes = package_inventory.read_bytes()
                removed_source = (
                    package_manifest
                    if missing_metadata == "manifest"
                    else package_inventory
                )

                failure_root = temp / "failure"
                failure_root.mkdir()
                failure_env, _ = self.make_fake_uv(
                    failure_root,
                    remove_on_sync=removed_source,
                )
                command = self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    target,
                    package_root=package,
                )
                interrupted = subprocess.run(
                    command,
                    cwd=package,
                    env=failure_env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(interrupted.returncode, 0)
                self.assertTrue((target / new_relative).is_file())
                target_inventory = (target / "scripts/package-files.txt").read_text(
                    encoding="utf-8"
                )
                self.assertIn("# inventory-format: complete", target_inventory)
                self.assertEqual(
                    [
                        line
                        for line in target_inventory.splitlines()
                        if line and not line.startswith("#")
                    ],
                    ["active scripts/package-files.txt"],
                )
                if missing_metadata == "manifest":
                    self.assertFalse(
                        (target / "scripts/upgrade-manifest.txt").exists()
                    )
                else:
                    self.assertIn(
                        "initial transition generation",
                        (target / "scripts/upgrade-manifest.txt").read_text(
                            encoding="utf-8"
                        ),
                    )

                package_manifest.write_bytes(manifest_bytes)
                package_inventory.write_bytes(inventory_bytes)
                edited_target = temp / "edited-target"
                shutil.copytree(target, edited_target)

                clean_root = temp / "clean-rerun"
                clean_root.mkdir()
                clean_env, clean_call_log = self.make_fake_uv(clean_root)
                clean_rerun = subprocess.run(
                    command,
                    cwd=package,
                    env=clean_env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    clean_rerun.returncode,
                    0,
                    clean_rerun.stdout + clean_rerun.stderr,
                )
                self.assertTrue(clean_call_log.exists())
                self.assertEqual(
                    (target / new_relative).read_text(encoding="utf-8"),
                    "new package content\n",
                )
                self.assertEqual(
                    (target / "scripts/upgrade-manifest.txt").read_bytes(),
                    manifest_bytes,
                )
                self.assertEqual(
                    (target / "scripts/package-files.txt").read_bytes(),
                    inventory_bytes,
                )

                (edited_target / new_relative).write_text(
                    "user edit after interrupted initial activation\n",
                    encoding="utf-8",
                )
                rerun_root = temp / "rerun"
                rerun_root.mkdir()
                rerun_env, call_log = self.make_fake_uv(rerun_root)
                edited_command = self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    edited_target,
                    package_root=package,
                )
                rerun = subprocess.run(
                    edited_command,
                    cwd=package,
                    env=rerun_env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(rerun.returncode, 0)
                rerun_output = rerun.stdout + rerun.stderr
                self.assertIn(new_relative, rerun_output)
                self.assertIn("different content", rerun_output)
                self.assertNotIn(
                    "scripts/package-files.txt: new package-owned path", rerun_output
                )
                self.assertEqual(
                    (edited_target / new_relative).read_text(encoding="utf-8"),
                    "user edit after interrupted initial activation\n",
                )
                self.assertFalse(call_log.exists())

    def assert_interrupted_direct_file_activation_is_conservative(
        self, shell_kind: str
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            setup_command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
            )
            setup = subprocess.run(
                setup_command,
                cwd=ROOT,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            package_root = temp / "direct-file-package"
            package_root.mkdir()
            package = self.make_package_copy(package_root)
            new_relative = "NEW-PACKAGE-ENTRY.md"
            (package / new_relative).write_text("new package content\n", encoding="utf-8")
            package_manifest = package / "scripts/upgrade-manifest.txt"
            package_manifest.write_text(
                package_manifest.read_text(encoding="utf-8")
                + f"file {new_relative}\n",
                encoding="utf-8",
            )
            package_inventory = package / "scripts/package-files.txt"
            package_inventory.write_text(
                package_inventory.read_text(encoding="utf-8")
                + f"active {new_relative}\n",
                encoding="utf-8",
            )
            inventory_bytes = package_inventory.read_bytes()
            old_inventory_bytes = (target / "scripts/package-files.txt").read_bytes()

            failure_root = temp / "direct-file-failure"
            failure_root.mkdir()
            failure_env, _ = self.make_fake_uv(
                failure_root,
                remove_on_sync=package_inventory,
            )
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
                package_root=package,
            )
            interrupted = subprocess.run(
                command,
                cwd=package,
                env=failure_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertEqual(
                (target / "scripts/package-files.txt").read_bytes(),
                old_inventory_bytes,
            )
            self.assertTrue((target / new_relative).is_file())

            package_inventory.write_bytes(inventory_bytes)
            (target / new_relative).write_text(
                "user edit after interrupted upgrade\n",
                encoding="utf-8",
            )
            rerun_root = temp / "direct-file-rerun"
            rerun_root.mkdir()
            rerun_env, call_log = self.make_fake_uv(rerun_root)
            rerun = subprocess.run(
                command,
                cwd=package,
                env=rerun_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rerun.returncode, 0)
            self.assertIn(new_relative, rerun.stdout + rerun.stderr)
            self.assertEqual(
                (target / new_relative).read_text(encoding="utf-8"),
                "user edit after interrupted upgrade\n",
            )
            self.assertFalse(call_log.exists())

    def assert_interrupted_retired_to_active_transition_is_conservative(
        self, shell_kind: str
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            setup_command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
            )
            setup = subprocess.run(
                setup_command,
                cwd=ROOT,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            package_root = temp / "reactivation-package"
            package_root.mkdir()
            package = self.make_package_copy(package_root)
            source = package / RETIRED_PACKAGE_FILE
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("reactivated package content\n", encoding="utf-8")
            manifest = package / "scripts/upgrade-manifest.txt"
            manifest.write_text(
                "\n".join(
                    line
                    for line in manifest.read_text(encoding="utf-8").splitlines()
                    if line != f"remove {RETIRED_PACKAGE_FILE}"
                )
                + "\n",
                encoding="utf-8",
            )
            inventory = package / "scripts/package-files.txt"
            inventory.write_text(
                inventory.read_text(encoding="utf-8").replace(
                    f"remove {RETIRED_PACKAGE_FILE}\n",
                    f"active {RETIRED_PACKAGE_FILE}\n",
                ),
                encoding="utf-8",
            )
            inventory_bytes = inventory.read_bytes()
            old_inventory_bytes = (target / "scripts/package-files.txt").read_bytes()

            failure_root = temp / "reactivation-failure"
            failure_root.mkdir()
            failure_env, _ = self.make_fake_uv(
                failure_root,
                remove_on_sync=inventory,
            )
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
                package_root=package,
            )
            interrupted = subprocess.run(
                command,
                cwd=package,
                env=failure_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertTrue((target / RETIRED_PACKAGE_FILE).is_file())
            self.assertEqual(
                (target / "scripts/package-files.txt").read_bytes(),
                old_inventory_bytes,
            )

            inventory.write_bytes(inventory_bytes)
            (target / RETIRED_PACKAGE_FILE).write_text(
                "user edit after interrupted reactivation\n",
                encoding="utf-8",
            )
            rerun_root = temp / "reactivation-rerun"
            rerun_root.mkdir()
            rerun_env, call_log = self.make_fake_uv(rerun_root)
            rerun = subprocess.run(
                command,
                cwd=package,
                env=rerun_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rerun.returncode, 0)
            self.assertIn(RETIRED_PACKAGE_FILE, rerun.stdout + rerun.stderr)
            self.assertEqual(
                (target / RETIRED_PACKAGE_FILE).read_text(encoding="utf-8"),
                "user edit after interrupted reactivation\n",
            )
            self.assertFalse(call_log.exists())

    def assert_interrupted_tombstone_drop_is_resumable(self, shell_kind: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            setup = subprocess.run(
                self.script_command(
                    shell_kind,
                    "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                    "-TargetRoot",
                    target,
                ),
                cwd=ROOT,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            package_root = temp / "dropped-tombstone-package"
            package_root.mkdir()
            package = self.make_package_copy(package_root)
            manifest = package / "scripts/upgrade-manifest.txt"
            manifest.write_text(
                "\n".join(
                    line
                    for line in manifest.read_text(encoding="utf-8").splitlines()
                    if line != f"remove {RETIRED_PACKAGE_FILE}"
                )
                + "\n",
                encoding="utf-8",
            )
            inventory = package / "scripts/package-files.txt"
            inventory.write_text(
                "\n".join(
                    line
                    for line in inventory.read_text(encoding="utf-8").splitlines()
                    if line != f"remove {RETIRED_PACKAGE_FILE}"
                )
                + "\n",
                encoding="utf-8",
            )
            inventory_bytes = inventory.read_bytes()

            failure_root = temp / "dropped-tombstone-failure"
            failure_root.mkdir()
            failure_env, _ = self.make_fake_uv(
                failure_root,
                remove_on_sync=inventory,
            )
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
                package_root=package,
            )
            interrupted = subprocess.run(
                command,
                cwd=package,
                env=failure_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertNotIn(
                f"remove {RETIRED_PACKAGE_FILE}",
                (target / "scripts/upgrade-manifest.txt").read_text(encoding="utf-8"),
            )
            self.assertIn(
                f"remove {RETIRED_PACKAGE_FILE}",
                (target / "scripts/package-files.txt").read_text(encoding="utf-8"),
            )

            inventory.write_bytes(inventory_bytes)
            released_path = target / RETIRED_PACKAGE_FILE
            released_path.parent.mkdir(parents=True, exist_ok=True)
            released_path.write_text("target-owned after tombstone release\n", encoding="utf-8")
            rerun_root = temp / "dropped-tombstone-rerun"
            rerun_root.mkdir()
            rerun_env, call_log = self.make_fake_uv(rerun_root)
            rerun = subprocess.run(
                command,
                cwd=package,
                env=rerun_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
            self.assertEqual(
                released_path.read_text(encoding="utf-8"),
                "target-owned after tombstone release\n",
            )
            self.assertTrue(call_log.exists())

    def add_fresh_tombstone(self, package: Path, relative: str) -> tuple[Path, bytes]:
        manifest = package / "scripts/upgrade-manifest.txt"
        manifest.write_text(
            manifest.read_text(encoding="utf-8") + f"remove {relative}\n",
            encoding="utf-8",
        )
        inventory = package / "scripts/package-files.txt"
        inventory.write_text(
            inventory.read_text(encoding="utf-8") + f"remove {relative}\n",
            encoding="utf-8",
        )
        return inventory, inventory.read_bytes()

    def assert_fresh_tombstone_activation_is_conservative(self, shell_kind: str) -> None:
        script_name = "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            setup = subprocess.run(
                self.script_command(shell_kind, script_name, "-TargetRoot", target),
                cwd=ROOT,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            package_root = temp / "tombstone-package"
            package_root.mkdir()
            package = self.make_package_copy(package_root)
            relative = "target-only-retired-name.md"
            self.add_fresh_tombstone(package, relative)
            command = self.script_command(
                shell_kind,
                script_name,
                "-TargetRoot",
                target,
                package_root=package,
            )

            target_file = target / relative
            target_file.write_text("target-owned content\n", encoding="utf-8")
            before = self.snapshot_working_tree(target)
            conflict_root = temp / "tombstone-conflict"
            conflict_root.mkdir()
            conflict_env, call_log = self.make_fake_uv(conflict_root)
            conflict = subprocess.run(
                command,
                cwd=package,
                env=conflict_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(conflict.returncode, 0)
            self.assertIn(relative, conflict.stdout + conflict.stderr)
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertFalse(call_log.exists())

            target_file.unlink()
            target_file.mkdir()
            directory_before = self.snapshot_working_tree(target)
            directory_conflict_root = temp / "tombstone-directory-conflict"
            directory_conflict_root.mkdir()
            directory_conflict_env, directory_call_log = self.make_fake_uv(
                directory_conflict_root
            )
            directory_conflict = subprocess.run(
                command,
                cwd=package,
                env=directory_conflict_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(directory_conflict.returncode, 0)
            self.assertIn(
                relative, directory_conflict.stdout + directory_conflict.stderr
            )
            self.assertEqual(self.snapshot_working_tree(target), directory_before)
            self.assertFalse(directory_call_log.exists())

            target_file.rmdir()
            activation_root = temp / "tombstone-activation"
            activation_root.mkdir()
            activation_env, activation_log = self.make_fake_uv(activation_root)
            activation = subprocess.run(
                command,
                cwd=package,
                env=activation_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(activation.returncode, 0, activation.stdout + activation.stderr)
            target_file.write_text("reappeared retired package file\n", encoding="utf-8")
            repeated = subprocess.run(
                command,
                cwd=package,
                env=activation_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(repeated.returncode, 0, repeated.stdout + repeated.stderr)
            self.assertFalse(target_file.exists())
            self.assertTrue(activation_log.exists())

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            setup_root = temp / "setup"
            setup_root.mkdir()
            setup_env, _ = self.make_fake_uv(setup_root)
            setup = subprocess.run(
                self.script_command(shell_kind, script_name, "-TargetRoot", target),
                cwd=ROOT,
                env=setup_env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)

            package_root = temp / "interrupted-tombstone-package"
            package_root.mkdir()
            package = self.make_package_copy(package_root)
            relative = "interrupted-retired-name.md"
            inventory, inventory_bytes = self.add_fresh_tombstone(package, relative)
            failure_root = temp / "interrupted-tombstone-failure"
            failure_root.mkdir()
            failure_env, _ = self.make_fake_uv(
                failure_root,
                remove_on_sync=inventory,
            )
            command = self.script_command(
                shell_kind,
                script_name,
                "-TargetRoot",
                target,
                package_root=package,
            )
            interrupted = subprocess.run(
                command,
                cwd=package,
                env=failure_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(interrupted.returncode, 0)
            inventory.write_bytes(inventory_bytes)
            target_file = target / relative
            target_file.write_text("created after interruption\n", encoding="utf-8")
            before = self.snapshot_working_tree(target)
            rerun_root = temp / "interrupted-tombstone-rerun"
            rerun_root.mkdir()
            rerun_env, call_log = self.make_fake_uv(rerun_root)
            rerun = subprocess.run(
                command,
                cwd=package,
                env=rerun_env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rerun.returncode, 0)
            self.assertIn(relative, rerun.stdout + rerun.stderr)
            self.assertEqual(self.snapshot_working_tree(target), before)
            self.assertFalse(call_log.exists())

    def assert_new_inventory_schema_guard(self, shell_kind: str) -> None:
        script_name = "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh"
        cases = {
            "missing_header": "must declare 'inventory all'",
            "missing_inventory_marker": "inventory must declare '# inventory-format: complete'",
            "missing_manifest_path": "inventory is missing active manifest path: WIKI.md",
            "orphan_inventory": "inventory path is not classified by the manifest",
            "duplicate_header": "exactly once",
            "duplicate_inventory": "duplicate package path",
            "classification_mismatch": "classification does not match the manifest",
            "untyped_inventory": "Invalid New package complete inventory line",
            "missing_retired_path": "inventory is missing retired manifest path",
        }
        for case, expected in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp_dir:
                temp = Path(temp_dir)
                package = self.make_package_copy(temp)
                manifest = package / "scripts/upgrade-manifest.txt"
                inventory = package / "scripts/package-files.txt"
                if case == "missing_header":
                    manifest.write_text(
                        "\n".join(
                            line
                            for line in manifest.read_text(encoding="utf-8").splitlines()
                            if line != "inventory all"
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                elif case == "missing_inventory_marker":
                    inventory.write_text(
                        "\n".join(
                            line
                            for line in inventory.read_text(encoding="utf-8").splitlines()
                            if line != "# inventory-format: complete"
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                elif case == "missing_manifest_path":
                    inventory.write_text(
                        "\n".join(
                            line
                            for line in inventory.read_text(encoding="utf-8").splitlines()
                            if line != "active WIKI.md"
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                elif case == "orphan_inventory":
                    inventory.write_text(
                        inventory.read_text(encoding="utf-8")
                        + "active orphan-not-owned.md\n",
                        encoding="utf-8",
                    )
                elif case == "duplicate_header":
                    manifest.write_text(
                        manifest.read_text(encoding="utf-8").replace(
                            "inventory all\n", "inventory all\ninventory all\n", 1
                        ),
                        encoding="utf-8",
                    )
                elif case == "duplicate_inventory":
                    inventory.write_text(
                        inventory.read_text(encoding="utf-8") + "active wiki.md\n",
                        encoding="utf-8",
                    )
                elif case == "classification_mismatch":
                    inventory.write_text(
                        inventory.read_text(encoding="utf-8").replace(
                            "active WIKI.md\n", "remove WIKI.md\n"
                        ),
                        encoding="utf-8",
                    )
                elif case == "untyped_inventory":
                    inventory.write_text(
                        inventory.read_text(encoding="utf-8").replace(
                            "active WIKI.md\n", "WIKI.md\n"
                        ),
                        encoding="utf-8",
                    )
                else:
                    inventory.write_text(
                        "\n".join(
                            line
                            for line in inventory.read_text(encoding="utf-8").splitlines()
                            if line != f"remove {RETIRED_PACKAGE_FILE}"
                        )
                        + "\n",
                        encoding="utf-8",
                    )

                target = temp / "target"
                target.mkdir()
                before = self.snapshot_working_tree(target)
                run_root = temp / "run"
                run_root.mkdir()
                env, call_log = self.make_fake_uv(run_root)
                result = subprocess.run(
                    self.script_command(
                        shell_kind,
                        script_name,
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
                self.assertIn(expected, result.stdout + result.stderr)
                self.assertEqual(self.snapshot_working_tree(target), before)
                self.assertFalse(call_log.exists())

    def assert_legacy_inventory_metadata_is_supported(self, shell_kind: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            target = self.make_target(temp, with_sentinel=False)
            env, call_log = self.make_fake_uv(temp)
            command = self.script_command(
                shell_kind,
                "upgrade.ps1" if shell_kind == "powershell" else "upgrade.sh",
                "-TargetRoot",
                target,
            )
            first = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            self.convert_target_metadata_to_legacy(target)
            (target / "WIKI.md").write_text("# Legacy-owned local copy\n", encoding="utf-8")
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
            if shell_kind == "bash" and os.name != "nt":
                for relative in (
                    "scripts/upgrade-manifest.txt",
                    "scripts/package-files.txt",
                ):
                    self.assertEqual(
                        stat.S_IMODE((target / relative).stat().st_mode),
                        0o644,
                    )

            target_manifest = target / "scripts/upgrade-manifest.txt"
            target_manifest.write_text(
                "\n".join(
                    line
                    for line in target_manifest.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if line != "inventory all"
                )
                + "\n",
                encoding="utf-8",
            )
            (target / "WIKI.md").write_text(
                "# Legacy manifest with marked inventory\n", encoding="utf-8"
            )
            call_log.unlink()
            third = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(third.returncode, 0, third.stdout + third.stderr)
            self.assertEqual(
                (target / "WIKI.md").read_bytes(), (ROOT / "WIKI.md").read_bytes()
            )
            self.assertEqual(
                (target / "scripts/upgrade-manifest.txt").read_bytes(),
                (ROOT / "scripts/upgrade-manifest.txt").read_bytes(),
            )
            self.assertEqual(
                (target / "scripts/package-files.txt").read_bytes(),
                (ROOT / "scripts/package-files.txt").read_bytes(),
            )
            self.assertTrue(call_log.exists())

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

    def test_powershell_interrupted_metadata_activation_is_conservative(self) -> None:
        self.assert_interrupted_metadata_activation_is_conservative("powershell")

    def test_bash_interrupted_metadata_activation_is_conservative(self) -> None:
        self.assert_interrupted_metadata_activation_is_conservative("bash")

    def test_powershell_interrupted_legacy_metadata_activation_is_conservative(
        self,
    ) -> None:
        self.assert_interrupted_legacy_metadata_activation_is_conservative(
            "powershell"
        )

    def test_bash_interrupted_legacy_metadata_activation_is_conservative(self) -> None:
        self.assert_interrupted_legacy_metadata_activation_is_conservative("bash")

    def test_powershell_interrupted_initial_metadata_activation_is_conservative(
        self,
    ) -> None:
        self.assert_interrupted_initial_metadata_activation_is_conservative(
            "powershell"
        )

    def test_bash_interrupted_initial_metadata_activation_is_conservative(self) -> None:
        self.assert_interrupted_initial_metadata_activation_is_conservative("bash")

    def test_powershell_interrupted_direct_file_activation_is_conservative(self) -> None:
        self.assert_interrupted_direct_file_activation_is_conservative("powershell")

    def test_bash_interrupted_direct_file_activation_is_conservative(self) -> None:
        self.assert_interrupted_direct_file_activation_is_conservative("bash")

    def test_powershell_interrupted_retired_to_active_transition_is_conservative(
        self,
    ) -> None:
        self.assert_interrupted_retired_to_active_transition_is_conservative(
            "powershell"
        )

    def test_bash_interrupted_retired_to_active_transition_is_conservative(
        self,
    ) -> None:
        self.assert_interrupted_retired_to_active_transition_is_conservative("bash")

    def test_powershell_interrupted_tombstone_drop_is_resumable(self) -> None:
        self.assert_interrupted_tombstone_drop_is_resumable("powershell")

    def test_bash_interrupted_tombstone_drop_is_resumable(self) -> None:
        self.assert_interrupted_tombstone_drop_is_resumable("bash")

    def test_powershell_fresh_tombstone_activation_is_conservative(self) -> None:
        self.assert_fresh_tombstone_activation_is_conservative("powershell")

    def test_bash_fresh_tombstone_activation_is_conservative(self) -> None:
        self.assert_fresh_tombstone_activation_is_conservative("bash")

    def test_powershell_new_inventory_schema_guard(self) -> None:
        self.assert_new_inventory_schema_guard("powershell")

    def test_bash_new_inventory_schema_guard(self) -> None:
        self.assert_new_inventory_schema_guard("bash")

    def test_powershell_legacy_inventory_metadata_is_supported(self) -> None:
        self.assert_legacy_inventory_metadata_is_supported("powershell")

    def test_bash_legacy_inventory_metadata_is_supported(self) -> None:
        self.assert_legacy_inventory_metadata_is_supported("bash")

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

    def test_powershell_removes_owned_retired_package_files(self) -> None:
        self.assert_owned_retired_package_file_cleanup("powershell")

    def test_bash_removes_owned_retired_package_files(self) -> None:
        self.assert_owned_retired_package_file_cleanup("bash")

    def test_powershell_continues_a_tombstone_cleanup(self) -> None:
        self.assert_continued_tombstone_cleanup("powershell")

    def test_bash_continues_a_tombstone_cleanup(self) -> None:
        self.assert_continued_tombstone_cleanup("bash")


if __name__ == "__main__":
    unittest.main()
