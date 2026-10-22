import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_release', ROOT / 'scripts/build_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseBuildTest(unittest.TestCase):
    def setUp(self):
        (ROOT / 'tmp').mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / 'tmp')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'repo'
        self.root.mkdir()
        self.output = Path(self.temporary.name) / 'output'
        self.run_git('init', '-q')
        self.run_git('config', 'user.name', 'Test Fixture')
        self.run_git('config', 'user.email', 'fixture@example.invalid')
        files = {
            'pyproject.toml': '[project]\nversion = "1.0.0"\n',
            'PROJECT.md': 'Blank project template\n',
            '.gitignore': '.env\n',
            'scripts/init.sh': '#!/bin/sh\n',
            'scripts/upgrade.sh': '#!/bin/sh\n',
        }
        for path, content in files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
        self.inventory = '# inventory-schema: 1\n' + ''.join(
            f'active {path}\n' for path in ('scripts/package-files.txt', 'pyproject.toml', 'scripts/init.sh', 'scripts/upgrade.sh')
        )
        (self.root / release.INVENTORY).write_text(self.inventory, encoding='utf-8')
        self.run_git('add', '.')
        self.run_git('update-index', '--chmod=+x', 'scripts/init.sh', 'scripts/upgrade.sh')
        self.run_git('commit', '-qm', 'fixture')

    def run_git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def test_committed_templates_archive_parity_and_reproducibility(self):
        (self.root / 'PROJECT.md').write_text('Local personalized project', encoding='utf-8')
        (self.root / '.env').write_text('fixture private data', encoding='utf-8')
        paths = release.build(self.root, 'HEAD', self.output)
        second = release.build(self.root, 'HEAD', self.output / 'second')
        self.assertEqual([path.read_bytes() for path in paths], [path.read_bytes() for path in second])
        with zipfile.ZipFile(paths[0]) as archive:
            zipped = {name.split('/', 1)[1]: archive.read(name) for name in archive.namelist()}
        with tarfile.open(paths[1]) as archive:
            packed = {member.name.split('/', 1)[1]: archive.extractfile(member).read() for member in archive}
            self.assertTrue(all(member.mode & 0o111 for member in archive.getmembers() if member.name.endswith('.sh')))
        self.assertEqual(zipped, packed)
        self.assertEqual(zipped['PROJECT.md'], release.git(self.root, 'show', 'HEAD:PROJECT.md'))
        self.assertNotIn('.env', zipped)
        self.assertEqual(set(zipped), set(json.loads(paths[2].read_text())['files']))
        with self.assertRaisesRegex(ValueError, 'already exists'):
            release.build(self.root, 'HEAD', self.output)

    def test_invalid_inventory_paths_and_private_content(self):
        for path in ('../outside', '/absolute', 'docs/../outside', '.env', 'raw/file', 'docs/.env', 'scripts\\file'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                release.inventory_paths(self.inventory + f'active {path}\n')

    def test_missing_file_and_executable_mode_fail_before_outputs(self):
        (self.root / release.INVENTORY).write_text(self.inventory + 'active missing.md\n', encoding='utf-8')
        self.run_git('add', '.')
        self.run_git('commit', '-qm', 'missing fixture')
        with self.assertRaises(ValueError):
            release.build(self.root, 'HEAD', self.output)
        self.assertFalse(self.output.exists())
        (self.root / release.INVENTORY).write_text(self.inventory, encoding='utf-8')
        self.run_git('add', '.')
        self.run_git('update-index', '--chmod=-x', 'scripts/upgrade.sh')
        self.run_git('commit', '-qm', 'mode fixture')
        with self.assertRaisesRegex(ValueError, 'executable bit'):
            release.build(self.root, 'HEAD', self.output)

    def test_committed_symlink_is_rejected(self):
        oid = subprocess.run(['git', '-C', str(self.root), 'hash-object', '-w', '--stdin'],
                             input=b'PROJECT.md', capture_output=True, check=True).stdout.decode().strip()
        self.run_git('update-index', '--add', '--cacheinfo', f'120000,{oid},linked.md')
        (self.root / release.INVENTORY).write_text(self.inventory + 'active linked.md\n', encoding='utf-8')
        self.run_git('add', release.INVENTORY)
        self.run_git('commit', '-qm', 'linked fixture')
        with self.assertRaisesRegex(ValueError, 'linked package file'):
            release.build(self.root, 'HEAD', self.output)
        self.assertFalse(self.output.exists())

    def test_cli_output_prompt_and_explicit_directory(self):
        script = self.root / 'scripts/build_release.py'
        script.write_bytes((ROOT / 'scripts/build_release.py').read_bytes())
        for case, args, entered, directory in (
            ('blank', [], '\n', '.'),
            ('entered', [], 'chosen directory\n', 'chosen directory'),
            ('explicit', ['--output', 'chosen directory'], '', 'chosen directory'),
        ):
            with self.subTest(case=case):
                caller = Path(self.temporary.name) / case
                caller.mkdir()
                result = subprocess.run([sys.executable, str(script), *args], cwd=caller,
                                        input=entered, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(list((caller / directory).glob('llm-wiki-agent-*'))), 4)
        result = subprocess.run([sys.executable, str(script)], cwd=self.root,
                                input='', capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('pass --output PATH', result.stderr)


if __name__ == '__main__':
    (ROOT / 'tmp').mkdir(exist_ok=True)
    unittest.main()
