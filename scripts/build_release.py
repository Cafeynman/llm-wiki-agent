"""Build distribution archives from an immutable Git commit, using only stdlib."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile
import time
import tomllib
import zipfile

INVENTORY = "scripts/package-files.txt"
TEMPLATES = {"PROJECT.md", ".gitignore"}
PRIVATE_ROOTS = {
    ".git", ".env", ".venv", ".claude", ".claudian", ".codex", ".crush",
    ".obsidian", "tmp", "inbox", "raw", "intake", "reviews", "logs",
    "questions", "artifacts", "wiki", "__pycache__",
}


def git(root, *args):
    result = subprocess.run(["git", "--literal-pathspecs", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError(f"Git operation {args[0]} failed: {result.stderr.decode('utf-8', errors='replace').strip()}")
    return result.stdout


def inventory_paths(text):
    if text.splitlines().count("# inventory-schema: 1") != 1:
        raise ValueError(f"{INVENTORY}: expected exactly one schema-1 marker")
    active, seen = set(), set()
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or fields[0] not in {"active", "remove"}:
            raise ValueError(f"{INVENTORY}: invalid record {line!r}")
        kind, path = fields
        parts = PurePosixPath(path).parts
        if (not parts or path != '/'.join(parts) or '\\' in path or ':' in path
                or any(part in {'.', '..'} for part in parts) or path.startswith('/')):
            raise ValueError(f"{INVENTORY}: invalid path {path!r}")
        if path.casefold() in seen:
            raise ValueError(f"{INVENTORY}: duplicate path {path!r}")
        seen.add(path.casefold())
        if kind == "active":
            if parts[0].casefold() in PRIVATE_ROOTS or any(
                part.casefold() in {'.env', '__pycache__', '.git'} for part in parts
            ):
                raise ValueError(f"{INVENTORY}: private/runtime path {path!r}")
            active.add(path)
    if INVENTORY not in active:
        raise ValueError(f"{INVENTORY}: inventory must own itself")
    return active | TEMPLATES


def build(root, ref, output):
    commit = git(root, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").decode().strip()
    paths = inventory_paths(git(root, "show", f"{commit}:{INVENTORY}").decode('utf-8'))
    # Read raw Git blobs: archive/checkout filters may change line endings.
    entries = []
    for record in git(root, 'ls-tree', '-r', '-z', commit, '--', *sorted(paths)).split(b'\0'):
        if not record:
            continue
        header, path = record.split(b'\t', 1)
        mode, kind, oid = header.split()
        path = path.decode('utf-8')
        if path not in paths or kind != b'blob' or mode not in {b'100644', b'100755'}:
            raise ValueError(f'Unexpected or linked package file: {path}')
        entries.append((path, int(mode, 8) & 0o777, oid))
    if {path for path, _mode, _oid in entries} != paths:
        raise ValueError(f"Missing committed package files: {sorted(paths - {entry[0] for entry in entries})}")
    result = subprocess.run(['git', '-C', str(root), 'cat-file', '--batch'],
                            input=b''.join(oid + b'\n' for _path, _mode, oid in entries),
                            capture_output=True, check=True)
    stream, files = io.BytesIO(result.stdout), {}
    for path, mode, oid in entries:
        object_id, kind, size = stream.readline().split()
        if object_id != oid or kind != b'blob':
            raise ValueError(f'Git blob read failed for {path}')
        content = stream.read(int(size))
        if len(content) != int(size) or stream.read(1) != b'\n':
            raise ValueError(f'Incomplete Git blob for {path}')
        files[path] = (content, mode)
    version = tomllib.loads(files['pyproject.toml'][0].decode('utf-8'))['project']['version']
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?', version):
        raise ValueError(f"pyproject.toml: unsafe release version {version!r}")
    for path in ('scripts/init.sh', 'scripts/upgrade.sh'):
        if not files[path][1] & 0o111:
            raise ValueError(f"{path}: Git executable bit missing; fix before packaging")
    stamp = int(git(root, 'show', '-s', '--format=%ct', commit))
    prefix = f'llm-wiki-agent-{version}-{commit[:12]}'
    names = [prefix + suffix for suffix in ('.zip', '.tar.gz', '.json', '.sha256')]
    output = Path(output).resolve()
    if any((output / name).exists() for name in names):
        raise ValueError(f"Output already exists for {prefix} in {output}; choose another output directory")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.build-', dir=output) as temporary:
        stage = Path(temporary)
        with zipfile.ZipFile(stage / names[0], 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for path, (content, mode) in sorted(files.items()):
                info = zipfile.ZipInfo(f'{prefix}/{path}', time.gmtime(max(stamp, 315532800))[:6])
                info.create_system = 3
                info.external_attr = (0o100000 | mode) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content)
        with (stage / names[1]).open('wb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=stamp) as compressed:
                with tarfile.open(fileobj=compressed, mode='w') as archive:
                    for path, (content, mode) in sorted(files.items()):
                        info = tarfile.TarInfo(f'{prefix}/{path}')
                        info.size, info.mode, info.mtime = len(content), mode, stamp
                        archive.addfile(info, io.BytesIO(content))
        metadata = {'commit': commit, 'version': version, 'files': {
            path: {'sha256': hashlib.sha256(content).hexdigest(), 'mode': oct(mode)}
            for path, (content, mode) in sorted(files.items())
        }}
        (stage / names[2]).write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8', newline='\n')
        (stage / names[3]).write_text(''.join(
            f'{hashlib.sha256((stage / name).read_bytes()).hexdigest()}  {name}\n'
            for name in names[:3]
        ), encoding='utf-8', newline='\n')
        for name in names:
            (stage / name).rename(output / name)
    return [output / name for name in names]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD', help='Git commit, branch or tag (default: HEAD)')
    parser.add_argument('--output', type=Path, help='Output directory; omitted: prompt (blank uses current directory)')
    args = parser.parse_args()
    try:
        output = args.output
        if output is None:
            try:
                entered = input(f'Output directory (blank uses current directory {Path.cwd()}): ').strip()
            except EOFError:
                raise ValueError('No output directory input; pass --output PATH for non-interactive use') from None
            output = Path(entered) if entered else Path.cwd()
        for path in build(Path(__file__).resolve().parents[1], args.ref, output.expanduser()):
            print(path)
    except (ValueError, OSError, KeyError, UnicodeError, subprocess.CalledProcessError, tarfile.TarError) as error:
        parser.exit(1, f'Build failed: {error}\n')


if __name__ == '__main__':
    main()
