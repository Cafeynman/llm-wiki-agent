"""Build reviewed source ranges without guessing boundaries or image meaning."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from urllib.parse import unquote, quote

from audit_chunks import inspect_chunks, size_kind
from audit_intake_file import content_units, extract_headings, DEFAULT_LARGE_SOURCE_THRESHOLD
from chunk_contract import INDEX_COLUMNS, parse_index_text, valid_chunk_component, DEFAULT_SMALL_CHUNK_THRESHOLD

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'obsidian-wiki-lint' / 'scripts'))
from markdown_code import mask_markdown_code
from obsidian_links import WIKILINK_RE, parse_wikilink_inner
from lint_wiki import build_lookup, resolve_target, resolve_markdown_target

INLINE_LINK = re.compile(r'!?\[([^\]\n]*)\]\((<[^>\n]+>|[^\s()]+)\)')


def linked_boundary(path):
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def reference_paths(vault, documents):
    """Resolve actual references using the shared vault resolver; ambiguity stays conservative."""
    paths = [path for path, _ in documents]
    attachments = [p for p in vault.rglob('*') if p.is_file() and p.suffix.lower() != '.md' and not any(part.startswith('.') for part in p.relative_to(vault).parts)]
    existing = [p for p in vault.rglob('*.md') if not any(part.startswith('.') for part in p.relative_to(vault).parts)]
    all_files, by_stem = build_lookup(list(dict.fromkeys(paths + existing + attachments)), vault)
    references, unsupported = {}, []
    for path, text in documents:
        masked = mask_markdown_code(text)
        rel = path.relative_to(vault).as_posix()
        spans = []
        for match in WIKILINK_RE.finditer(masked):
            value = parse_wikilink_inner(match.group(1)).target
            if Path(value).suffix and not value.endswith('.md'):
                for asset in attachments:
                    if asset.name == Path(value).name:
                        references.setdefault(asset.resolve(), []).append(path)
            resolution = resolve_target(vault, value, all_files, by_stem)
            if resolution:
                references.setdefault((vault/resolution[0]).resolve(), []).append(path)
            # Ambiguous basename links cannot prove a target is unused.
            if '/' not in value and len(by_stem.get(Path(value).stem, [])) > 1:
                for candidate in by_stem[Path(value).stem]:
                    references.setdefault((vault/candidate).resolve(), []).append(path)
            spans.append(match.span())
        for match in INLINE_LINK.finditer(masked):
            value = unquote(match.group(2).strip('<>')).split('#', 1)[0]
            if value and not re.match(r'^[a-zA-Z][\w+.-]*:', value):
                resolution = resolve_markdown_target(vault, rel, value, all_files)
                if resolution:
                    references.setdefault((vault/resolution[0]).resolve(), []).append(path)
            spans.append(match.span())
        remainder = list(masked)
        for start, end in spans:
            remainder[start:end] = ' ' * (end-start)
        if re.search(r'!?\[[^\n\]]+\]\s*(?:\[[^\n]*\]|:)|\]\s*\(|!\[|<(?:img|a|picture)\b', ''.join(remainder), re.I):
            unsupported.append(path)
    return references, unsupported


def vault_documents(vault, root, stage):
    documents = []
    for path in vault.rglob('*.md'):
        rel = path.relative_to(vault)
        if any(part in {'.git', '.venv'} or part.startswith('.'+root.name+'-build-') for part in rel.parts) or path.is_relative_to(stage):
            continue
        if any(linked_boundary(candidate) for candidate in [path, *path.parents] if candidate.is_relative_to(vault)):
            fail(f'{path}: linked paths prevent complete reference scanning')
        actual = stage/path.relative_to(root) if path.is_relative_to(root) else path
        if actual.is_file():
            documents.append((path, actual.read_bytes().decode('utf-8-sig')))
    # New chunks and renamed supporting Markdown do not yet exist at final paths.
    known = {path for path, _ in documents}
    for path in stage.rglob('*.md'):
        final = root/path.relative_to(stage)
        if final not in known:
            documents.append((final, path.read_bytes().decode('utf-8-sig')))
    return documents

IMAGE = re.compile(r'!\[([^\]\n]*)\]\((<[^>\n]+>|[^\s()]+)\)')


def fail(message):
    raise ValueError(message)


def safe_relative(value):
    if not isinstance(value, str) or '\\' in value or ':' in value:
        fail(f'invalid relative path: {value!r}')
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(p in {'.', '..'} for p in path.parts):
        fail(f'invalid relative path: {value!r}')
    return path


def images(text, name):
    masked = mask_markdown_code(text)
    matches = list(IMAGE.finditer(masked))
    rest = list(masked)
    for match in matches:
        rest[match.start():match.end()] = ' ' * (match.end()-match.start())
    if re.search(r'!\[|<img\b|<picture\b', ''.join(rest), re.I):
        fail(f'{name}: unsupported image syntax; use simple inline Markdown images before building')
    return matches


def target(match):
    return unquote(match.group(2).strip('<>'))


def rewrite_images(text, name, changes, root, location, record):
    edits = []
    for occurrence, match in enumerate(images(text, name), 1):
        old = target(match)
        if not re.match(r'^[a-zA-Z][\w+.-]*:', old) and not old.startswith('#'):
            resolved = (location / old).resolve()
            if not resolved.is_relative_to(root) or not resolved.is_file():
                fail(f'{name}: image {occurrence} missing or outside source folder: {old}')
        change = changes.get((name, occurrence))
        if change:
            if change.get('expected') != old:
                fail(f'{name}: image {occurrence} expected target mismatch: {old}')
            action = change.get('action')
            if action == 'delete':
                if change.get('authorized') is not True or not change.get('reason', '').strip():
                    fail(f'{name}: image {occurrence} deletion requires authorized=true and reason')
                replacement = ''
            elif action == 'rename':
                new = str(safe_relative(change['to']))
                if Path(new).suffix.lower() not in {'.png','.jpg','.jpeg','.gif','.svg','.webp','.bmp','.tif','.tiff','.avif','.ico'}:
                    fail(f'{name}: renamed attachment must have an image suffix: {new}')
                old_path = (location / old).resolve()
                new_path = (root / new).resolve()
                if not old_path.is_relative_to(root) or not old_path.is_file():
                    fail(f'{name}: image {occurrence} missing or outside attachment: {old}')
                if new_path.exists() and new_path.read_bytes() != old_path.read_bytes():
                    fail(f'{name}: rename target conflict: {new}')
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(old_path, new_path) if old_path != new_path else None
                replacement = '![' + match.group(1) + '](<' + os.path.relpath(new_path, location).replace('\\', '/') + '>)'
            else:
                fail(f'{name}: image {occurrence} invalid action: {action}')
            edits.append((match.start(), match.end(), replacement))
            record.append({'file': name, 'occurrence': occurrence, **change, 'original_asset': os.path.relpath((location/old).resolve(), root).replace('\\', '/') if not re.match(r'^[a-zA-Z][\w+.-]*:', old) else None})
    for start, end, replacement in reversed(edits):
        text = text[:start] + replacement + text[end:]
    return text


def chunk_body(text, start, end, title, depth):
    body = ''.join(text.splitlines(keepends=True)[start-1:end])
    # Copy-only path rebasing. Source-local images were already checked.
    for match in reversed(images(body, f'lines {start}-{end}')):
        value = target(match)
        if re.match(r'^[a-zA-Z][\w+.-]*:', value) or value.startswith('#'):
            continue
        replacement = '![' + match.group(1) + '](<' + '../' * depth + value + '>)'
        body = body[:match.start()] + replacement + body[match.end():]
    # Reject unparsed inline forms (e.g. optional titles) before moving text.
    masked = mask_markdown_code(body)
    remainder = list(masked)
    for match in INLINE_LINK.finditer(masked):
        remainder[match.start():match.end()] = ' ' * (match.end()-match.start())
    if re.search(r'\]\s*\(', ''.join(remainder)):
        fail(f'lines {start}-{end}: unsupported inline link syntax; normalize before building')
    # Ordinary local inline links move with the text as well.
    links = list(re.finditer(r'(?<!!)\[([^\]\n]+)\]\((<[^>\n]+>|[^\s()]+)\)', masked))
    for match in reversed(links):
        value = unquote(match.group(2).strip('<>'))
        if re.match(r'^[a-zA-Z][\w+.-]*:', value) or value.startswith(('#', '/')):
            continue
        replacement = '[' + match.group(1) + '](<' + '../' * depth + value + '>)'
        body = body[:match.start()] + replacement + body[match.end():]
    if re.search(r'(?m)^\s*\[[^]\n]+\]:', masked):
        fail(f'lines {start}-{end}: reference-style links require explicit normalization before chunking')
    return f'# {title}\n\n<!-- source-lines: {start}-{end} -->\n\n' + body


def source_boundary(root, vault):
    root, vault = root.absolute(), vault.absolute()
    if not root.is_relative_to(vault) or root == vault:
        fail('intake folder must be inside --vault')
    current = root
    while current != vault:
        if linked_boundary(current):
            fail(f'{current}: symlink/junction source paths are unsupported')
        current = current.parent
    # The explicit vault is trusted; system ancestors may legitimately be linked.
    root, vault = root.resolve(), vault.resolve()
    if not root.is_relative_to(vault):
        fail('resolved source folder must remain inside --vault')
    return root, vault


def index_label(name):
    return name.replace('[', '&#91;').replace(']', '&#93;')


def build(root, plan, vault):
    # One ephemeral lock, removed on all ordinary exits; a crash leaves an actionable lock.
    root, vault = source_boundary(root, vault)
    lock = root.parent / ('.'+root.name+'-build.lock')
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        fail(f'{lock}: another build or interrupted writer owns this source; inspect before removing the lock')
    try:
        os.close(descriptor)
        return _build(root, plan, vault)
    finally:
        if root.exists():
            lock.unlink()  # Missing destination means recovery is outstanding; keep ownership evidence.


def source_snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def _build(root, plan, vault):
    root, vault = source_boundary(root, vault)
    if not isinstance(plan, dict) or not isinstance(plan.get('chunks'), list) or not isinstance(plan.get('images', []), list):
        fail('plan must contain a chunks array and optional images array')
    root, vault = root.resolve(), vault.resolve()
    if not root.is_relative_to(vault) or root == vault:
        fail('intake folder must be inside --vault')
    if any(linked_boundary(p) for p in [root, *root.rglob('*')]):
        fail(f'{root}: symlinks are not supported during replacement')
    relative_root = root.relative_to(vault)
    if len(relative_root.parts) < 3 or relative_root.parts[:2] not in {('intake', 'tmp'), ('intake', 'processed')}:
        fail('replacement is limited to one source under intake/tmp or intake/processed')
    initial_snapshot = source_snapshot(root)
    original = (root/'source.md').read_bytes()
    if hashlib.sha256(original).hexdigest() != plan.get('source_sha256'):
        fail('source.md changed: regenerate the range plan from current bytes')
    text = original.decode('utf-8')
    lines = text.splitlines(keepends=True)
    chunks = plan.get('chunks', [])
    cursor, names = 1, set()
    for item in chunks:
        if not isinstance(item, dict):
            fail('each chunks entry must be an object')
        start, end = item.get('start'), item.get('end')
        if type(start) is not int or type(end) is not int or start != cursor or end < start or end > len(lines):
            fail(f'chunk {item.get("path")}: expected next range starting at {cursor}; omission, overlap or order error')
        cursor = end+1
        path = safe_relative(item['path'])
        if path.suffix != '.md' or not all(valid_chunk_component(p, semantic=True) for p in [*path.parts[:-1], path.stem]):
            fail(f'{path}: new chunks require numeric-semantic names')
        if str(path).casefold() in names:
            fail(f'duplicate chunk path: {path}')
        names.add(str(path).casefold())
        description = item.get('description', '')
        if not isinstance(description, str) or any(c in description for c in '\r\n|'):
            fail(f'{path}: description must be a single table-safe line')
        if not isinstance(item.get('title'), str) or not item['title'].strip() or any(c in item['title'] for c in '\r\n|'):
            fail(f'{path}: title must be a single nonempty table-safe line')
    if not chunks or cursor != len(lines)+1:
        fail(f'source.md: uncovered lines from {cursor}')
    changes = {}
    for change in plan.get('images', []):
        if not isinstance(change, dict):
            fail('each images entry must be an object')
        name = str(safe_relative(change['file']))
        key = (name, change.get('occurrence'))
        if key in changes or type(key[1]) is not int or key[1] < 1:
            fail(f'duplicate/invalid image occurrence: {key}')
        if name.startswith('chunks/'):
            fail('image decisions target canonical source/supporting Markdown, not generated chunks')
        changes[key] = change
    stage = Path(tempfile.mkdtemp(prefix=f'.{root.name}-build-', dir=root.parent))
    backup = root.parent / (stage.name + '-previous')
    try:
        shutil.copytree(root, stage, dirs_exist_ok=True)
        records = []
        for md in stage.rglob('*.md'):
            if md.is_relative_to(stage/'chunks'):
                continue
            name = md.relative_to(stage).as_posix()
            body = md.read_bytes().decode('utf-8')
            changed = rewrite_images(body, name, changes, stage, md.parent, records)
            if changed != body:
                md.write_text(changed, encoding='utf-8', newline='')
        if len(records) != len(changes):
            fail('image plan contains a missing file or occurrence')
        current = (stage/'source.md').read_bytes().decode('utf-8')
        if len(current.splitlines(keepends=True)) != len(lines):
            fail('image edits changed source line count')
        old_chunks = root/'chunks'
        if (stage/'chunks').exists():
            for old_file in (stage/'chunks').rglob('*.md'):
                if old_file.name != 'index.md' and not valid_chunk_component(old_file.stem):
                    fail(f'{old_file.relative_to(stage)}: unowned Markdown in chunk tree; preserve and resolve before rebuilding')
                old_file.unlink()  # Replace generated Markdown only; preserve every attachment.
        (stage/'chunks').mkdir(exist_ok=True)
        rows = {}
        changed_old = set()
        for item in chunks:
            relative = Path(item['path'])
            output = stage/'chunks'/relative
            output.parent.mkdir(parents=True, exist_ok=True)
            body = chunk_body(current, item['start'], item['end'], item['title'], len(relative.parts))
            output.write_text(body, encoding='utf-8', newline='')
            units = content_units(body)
            kind = size_kind(units, DEFAULT_SMALL_CHUNK_THRESHOLD, DEFAULT_LARGE_SOURCE_THRESHOLD)
            status = {'under':'undersized', 'over':'oversized'}.get(kind, kind)
            # Audit's size kinds are canonical. Explicit new decisions need reviewed=true.
            reason = item.get('size_reason', '')
            reviewed = item.get('reviewed') is True
            old = old_chunks/relative
            if not reason and old.is_file() and old.read_bytes().decode('utf-8') == body:
                prior, _ = parse_index_text((old.parent/'index.md').read_text(encoding='utf-8'))
                for row in prior:
                    if unquote(row.target) == relative.name and row.size_status.startswith('accepted-'):
                        reason, reviewed = row.reason, row.review_status == 'reviewed'
            if reason:
                if not reviewed or kind == 'normal' or '\n' in reason or '|' in reason:
                    fail(f'{relative}: invalid reviewed size reason')
                status = 'accepted-under' if kind == 'under' else 'accepted-over'
            if old.is_file() and old.read_bytes().decode('utf-8') != body:
                changed_old.add(old)
            decision = f'{units} · {status}' + (f' — {reason}' if reason else '')
            description = item.get('description') or f'Complete source lines {item["start"]}-{item["end"]}'
            rows.setdefault(relative.parent, []).append(f'| [{index_label(relative.stem)}]({quote(relative.name)}) | {item["title"]} · source lines {item["start"]}-{item["end"]} | {description} | {decision} | {"reviewed" if reviewed else "pending"} |')
        if old_chunks.exists():
            for old in old_chunks.rglob('*.md'):
                if old.name != 'index.md' and not (stage/'chunks'/old.relative_to(old_chunks)).exists():
                    changed_old.add(old)
        for folder in list(rows):
            parent = folder
            while parent != Path('.'):
                rows.setdefault(parent.parent, [])
                parent = parent.parent
        for folder in sorted(rows, key=lambda p: len(p.parts), reverse=True):
            groups = []
            for child in rows:
                if child != folder and child.parent == folder:
                    groups.append(f'| [{index_label(child.name)}]({quote(child.name)}/index.md) | {child.name} | — | — · group | pending |')
            table = '| ' + ' | '.join(INDEX_COLUMNS) + ' |\n| ' + ' | '.join(['---']*5) + ' |\n'
            (stage/'chunks'/folder/'index.md').write_text('# Source chunks\n\n' + table + '\n'.join(rows[folder]+groups)+'\n', encoding='utf-8')
        # Derive sibling order from the reviewed range order, including interleaved leaves/groups.
        for folder in rows:
            index_path = stage/'chunks'/folder/'index.md'
            parsed, problems = parse_index_text(index_path.read_text(encoding='utf-8'))
            by_target = {unquote(row.target): line for row, line in zip(parsed, index_path.read_text(encoding='utf-8').splitlines()[4:])}
            ordered, previous, closed = [], None, set()
            for item in chunks:
                path = Path(item['path'])
                if folder != Path('.') and not path.is_relative_to(folder):
                    continue
                child = path.relative_to(folder).parts[0]
                entry = child if len(path.relative_to(folder).parts) == 1 else child+'/index.md'
                if entry != previous:
                    if entry in closed:
                        fail(f'{folder}: ranges revisit group {entry}; keep groups contiguous')
                    closed.add(entry)
                    ordered.append(by_target[entry])
                    previous = entry
            prefix = index_path.read_text(encoding='utf-8').splitlines()[:4]
            index_path.write_text('\n'.join(prefix+ordered)+'\n', encoding='utf-8')
        source_title = next(iter(extract_headings(text)), root.name)
        root_index = stage/'chunks'/'index.md'
        heading = f'# {source_title}\n\nSource: [source.md](../source.md) · `{root.relative_to(vault).as_posix()}/source.md`\n\nRule: inclusive source-line ranges, each line once in source order; index rows define reading order.'
        root_index.write_text(root_index.read_text(encoding='utf-8').replace('# Source chunks', heading, 1), encoding='utf-8')
        result = inspect_chunks(stage, DEFAULT_SMALL_CHUNK_THRESHOLD, DEFAULT_LARGE_SOURCE_THRESHOLD)
        failures = result['errors'] + [warning for warning in result['warnings'] if warning['code'] == 'unresolved_local_image']
        if failures:
            fail('chunk validation failed: ' + json.dumps(failures, ensure_ascii=False))
        # Physical deletion is opt-in and only follows a complete reference check.
        if old_chunks.exists():
            for old_index in old_chunks.rglob('index.md'):
                if not (stage/'chunks'/old_index.relative_to(old_chunks)).exists():
                    changed_old.add(old_index)
        documents = vault_documents(vault, root, stage)
        references, unsupported = reference_paths(vault, documents)
        for old in changed_old:
            incoming = [path for path in references.get(old.resolve(), []) if not path.is_relative_to(old_chunks)]
            if incoming:
                fail(f'{incoming[0]}: reference to changed chunk {old}; resolve its source range before replacement')
        if changed_old and unsupported:
            fail(f'{unsupported[0]}: unsupported reference syntax prevents safe changed-chunk replacement')
        asset_results = []
        for record in records:
            if record.get('delete_file') is not True:
                continue
            asset = record.get('original_asset')
            if not asset or record.get('authorized') is not True:
                fail(f'{record["file"]}: physical deletion needs a local asset and authorized=true')
            if Path(asset).suffix.lower() not in {'.png','.jpg','.jpeg','.gif','.svg','.webp','.bmp','.tif','.tiff','.avif','.ico'}:
                fail(f'physical deletion restricted to image attachments: {asset}')
            original_asset = (root/asset).resolve()
            staged_asset = (stage/asset).resolve()
            if not staged_asset.is_relative_to(stage):
                fail(f'physical deletion outside source folder: {asset}')
            incoming = references.get(original_asset, [])
            reason = ('retained reference: ' + str(incoming[0])) if incoming else ('unsupported reference syntax: ' + str(unsupported[0])) if unsupported else ''
            if not reason:
                asset_name = Path(asset).name
                forms = [asset_name.casefold(), quote(asset_name).casefold(), json.dumps(asset_name, ensure_ascii=True)[1:-1].casefold()]
                for non_markdown in vault.rglob('*'):
                    if non_markdown.suffix.lower() not in {'.canvas', '.base'} or not non_markdown.is_file():
                        continue
                    if any(part in {'.git', '.venv'} or part.startswith('.'+root.name+'-build-') for part in non_markdown.relative_to(vault).parts):
                        continue
                    actual = stage/non_markdown.relative_to(root) if non_markdown.is_relative_to(root) else non_markdown
                    try:
                        contents = actual.read_text(encoding='utf-8-sig').casefold()
                    except (OSError, UnicodeError):
                        reason = f'unsupported unreadable reference surface: {non_markdown}'
                        break
                    if any(form in contents for form in forms):
                        reason = f'unsupported non-Markdown reference: {non_markdown}'
                        break
            if not reason and staged_asset.is_file():
                staged_asset.unlink()
            asset_results.append({'path': asset, 'deleted': not bool(reason), 'reason': reason})
        report = {'images': records, 'attachment_actions': asset_results, 'retained_original_attachments': not asset_results or any(not row['deleted'] for row in asset_results), 'audit': result['status']}
        if records:
            with (stage/'manifest.md').open('a', encoding='utf-8') as handle:
                handle.write('\n## Image transformations\n\n```json\n'+json.dumps(records, ensure_ascii=False, indent=2)+'\n```\n')
        if source_snapshot(root) != initial_snapshot:
            fail('source folder changed during build; previous results retained')
        print(f'Publishing {root}; recovery copy: {backup}', file=sys.stderr, flush=True)
        root.rename(backup)
        try:
            stage.rename(root)
        except BaseException:
            backup.rename(root)
            raise
        try:
            shutil.rmtree(backup)  # Exact prior directory owned by this completed transaction.
            report['recovery_copy'] = None
        except OSError as error:
            report['recovery_copy'] = str(backup)
            report['cleanup_warning'] = str(error)
        return report
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('intake', type=Path)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--vault', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.intake, json.loads(args.plan.read_text(encoding='utf-8')), args.vault), ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'build_chunks: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
