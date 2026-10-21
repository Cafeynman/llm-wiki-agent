from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/skills/source-extraction/scripts'))
import audit_source_closeout as audit


class CloseoutTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.vault = Path(self.temporary.name)
        self.source = 'raw/digested/资料/报告.pdf'
        self.write(self.source, b'%PDF fixture')
        self.accepted = 'intake/processed/资料/报告/'
        self.write(self.accepted + 'source.md', '# 正文\n这是保留完整上下文的来源正文。' * 8)
        self.write(self.accepted + 'summary.md', '# 摘要\n内容摘要。')
        self.write(self.accepted + 'manifest.md', '[[raw/digested/资料/报告.pdf]]\n[[reviews/source-review/record]]')
        self.write('reviews/source-review/record.md', '# 审核\n审核依据。')
        self.write('wiki/sources/资料/报告.md', '---\nsources:\n  - "[[intake/processed/资料/报告/source]]"\n---\n# 来源\n来源说明。')

    def write(self, name, text):
        path = self.vault / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text if isinstance(text, bytes) else text.encode('utf-8'))
        return path

    def inspect(self):
        return audit.inspect_closeout(self.vault, self.source)

    def codes(self):
        return {issue['code'] for issue in self.inspect()['errors']}

    def test_pre_ingest_and_closeout_share_preserved_text_boundary(self):
        original = '# Source\nOriginal example raw/digested/example.pdf and footnote[^missing].\n'
        self.write(self.accepted + 'source.md', original * 8)
        self.write(self.accepted + 'provider/part.md', original)
        with patch('builtins.print'):
            self.assertEqual(audit.lint.lint(self.vault, self.accepted.rstrip('/')), 0)
        self.assertEqual(self.inspect()['status'], 'pass')
        self.write(self.accepted + 'manifest.md', original)
        with patch('builtins.print'):
            self.assertEqual(audit.lint.lint(self.vault, self.accepted.rstrip('/')), 1)
        self.assertIn('markdown_contract', self.codes())

    def test_complete_source_passes_without_mutation(self):
        before = {p.relative_to(self.vault): p.read_bytes() for p in self.vault.rglob('*') if p.is_file()}
        result = self.inspect()
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['scope'], 'structural-only')
        self.assertIn('review and log completeness', result['not_checked'])
        self.assertEqual(before, {p.relative_to(self.vault): p.read_bytes() for p in self.vault.rglob('*') if p.is_file()})

    def test_empty_alt_image_missing_is_reported(self):
        self.write(self.accepted + 'summary.md', '![](images/missing.png)')
        self.assertIn('broken_result_link', self.codes())

    def test_titled_markdown_link_resolves(self):
        for target in ('source.md "source title"', "source.md 'source title'", '<source.md> "source # title"', 'source.md#heading "title"', 'source.md (title)'):
            with self.subTest(target=target):
                self.write(self.accepted + 'summary.md', f'[Source]({target})')
                self.assertEqual(self.inspect()['status'], 'pass')

    def test_sibling_directory_is_not_source_collision(self):
        (self.vault / 'raw/digested/资料/报告').mkdir()
        self.assertEqual(self.inspect()['status'], 'pass')
    def test_missing_source_card(self):
        (self.vault / 'wiki/sources/资料/报告.md').unlink()
        self.assertIn('missing_required_file', self.codes())

    def test_multiple_raw_states(self):
        self.write('raw/ignored/资料/报告.pdf', b'other')
        self.assertIn('multiple_raw_states', self.codes())

    def test_inbox_and_tmp_residue(self):
        self.write('inbox/资料/报告.pdf', b'other')
        self.write('intake/tmp/资料/报告/source.md', '临时')
        self.assertTrue({'inbox_residue', 'temporary_residue'} <= self.codes())

    def test_pending_output_is_optional_and_terminal_states_reject_residue(self):
        for state in ('needs-review', 'ignored', 'unsupported'):
            source = f'raw/{state}/pending.pdf'
            self.write(source, b'original')
            self.assertEqual(audit.inspect_closeout(self.vault, source)['status'], 'pass')
            temporary = self.write('intake/tmp/pending/source.md', 'Retained review evidence')
            result = audit.inspect_closeout(self.vault, source)
            self.assertEqual('temporary_residue' in {row['code'] for row in result['errors']}, state != 'needs-review')
            self.assertEqual(temporary.read_text(), 'Retained review evidence')
            temporary.unlink(); temporary.parent.rmdir()
            (self.vault/source).unlink()

    def test_terminal_source_does_not_claim_pending_sibling_temporary_output(self):
        for state in ('digested', 'ignored', 'unsupported'):
            with self.subTest(state=state):
                name = '资料/报告' if state == 'digested' else f'{state}-report'
                source = f'raw/{state}/{name}.pdf'
                self.write(source, b'original')
                self.write(f'raw/needs-review/{name}.docx', b'pending original')
                self.write(f'intake/tmp/{name}/source.md', 'Pending review evidence')
                before = {p.relative_to(self.vault): p.read_bytes() for p in self.vault.rglob('*') if p.is_file()}
                result = audit.inspect_closeout(self.vault, source)
                self.assertEqual(result['errors'], [], result)
                self.assertIn('temporary_output_ownership_uncertain', {row['code'] for row in result['warnings']})
                self.assertEqual(before, {p.relative_to(self.vault): p.read_bytes() for p in self.vault.rglob('*') if p.is_file()})

    def test_broken_result_link(self):
        self.write(self.accepted + 'manifest.md', '[[wiki/claims/missing]]')
        self.assertIn('broken_result_link', self.codes())

    def test_frontmatter_intake_links_are_checked(self):
        self.write('wiki/sources/资料/报告.md', '---\nsources:\n  - "[[intake/processed/资料/报告/missing]]"\n---\n说明')
        self.assertIn('broken_result_link', self.codes())

    def test_markdown_relative_links(self):
        self.write(self.accepted + 'summary.md', '[正文](source.md)\n[不存在](missing.md)')
        errors = self.inspect()['errors']
        self.assertEqual(len(errors), 1, errors)
        self.assertIn('missing.md', errors[0]['message'])

    def test_other_source_in_progress_is_not_audited(self):
        self.write('inbox/other.pdf', b'draft')
        self.write('intake/tmp/other/source.md', b'\xff')
        self.write('intake/processed/another/manifest.md', '[[broken]]')
        self.assertEqual(self.inspect()['status'], 'pass')

    def test_same_stem_inbox_only_warns(self):
        self.write('inbox/资料/报告.docx', b'collision')
        result = self.inspect()
        self.assertEqual(result['status'], 'warn', result)
        self.assertIn('source_identity_collision', {issue['code'] for issue in result['warnings']})

    def test_two_digested_originals_conflict(self):
        self.write('raw/digested/资料/报告.docx', b'collision')
        self.assertIn('source_identity_collision', self.codes())

    def test_needs_review_with_digested_sibling_does_not_claim_output(self):
        self.source = 'raw/needs-review/资料/报告.docx'
        self.write(self.source, b'collision')
        result = self.inspect()
        self.assertEqual(result['status'], 'warn', result)
        self.assertIn('accepted_output_ownership_uncertain', {issue['code'] for issue in result['warnings']})

    def test_linked_ancestor_outside_vault_is_not_rejected(self):
        # Mock the platform topology; this is not a macOS execution test.
        original = Path.is_symlink
        with patch.object(Path, 'is_symlink', lambda path: path == self.vault.parent or original(path)):
            self.assertEqual(self.inspect()['status'], 'pass')

    def test_root_alias_is_resolved_before_audit(self):
        alias = self.vault.parent / (self.vault.name + '-alias')
        original = Path.resolve
        with patch.object(Path, 'resolve', lambda path, *a, **kw: self.vault if path == alias else original(path, *a, **kw)):
            self.assertEqual(audit.inspect_closeout(alias, self.source)['status'], 'pass')

    def test_internal_link_remains_rejected_without_symlink_privilege(self):
        original = Path.is_symlink
        linked = self.vault / 'intake/processed'
        with patch.object(Path, 'is_symlink', lambda path: path == linked or original(path)):
            self.assertEqual(self.inspect()['status'], 'input-error')

    def test_non_digested_requires_no_intake_or_card(self):
        self.source = 'raw/ignored/other.pdf'
        self.write(self.source, b'ignored')
        self.assertEqual(self.inspect()['status'], 'pass')
        self.write('intake/processed/other/source.md', '旧状态')
        self.assertIn('accepted_state_conflict', self.codes())

    def test_bad_utf8(self):
        self.write(self.accepted + 'summary.md', b'\xff')
        self.assertEqual(self.inspect()['status'], 'input-error')

    def test_unreadable_required_file(self):
        original = Path.read_text
        def unreadable(path, *args, **kwargs):
            if path.name == 'summary.md':
                raise PermissionError(f'permission denied: {path}')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', unreadable):
            self.assertEqual(self.inspect()['status'], 'input-error')

    def test_missing_and_traversal_input(self):
        for source in ('raw/digested/missing.pdf', '../outside.pdf', 'raw/digested/../../outside.pdf', str(self.vault / self.source)):
            with self.subTest(source=source):
                self.assertEqual(audit.inspect_closeout(self.vault, source)['status'], 'input-error')

    def test_link_escape(self):
        self.write(self.accepted + 'manifest.md', '[outside](../../../../../outside.md)\n[[wiki/missing]]')
        result = self.inspect()
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(len(result['errors']), 2)
        self.assertTrue(all(issue['path'] == self.accepted + 'manifest.md' for issue in result['errors']))
        self.assertTrue(all(issue['code'] == 'broken_result_link' for issue in result['errors']))
        self.assertTrue(any('../../../../../outside.md' in issue['message'] for issue in result['errors']))

    def test_preserved_source_text_does_not_receive_authored_page_rules(self):
        prose = '# Original\nThe document mentions wiki/sources/example.md as a path.\nFootnote across blocks[^original].'
        self.write(self.accepted + 'source.md', prose)
        self.write(self.accepted + 'provider-output.md', prose)
        self.assertEqual(self.inspect()['status'], 'pass')
        self.write(self.accepted + 'manifest.md', prose)
        self.assertIn('markdown_contract', self.codes())

    def test_preserved_source_links_are_still_checked(self):
        self.write(self.accepted + 'source.md', '# Original\nSee [missing attachment](missing.png) for context.')
        self.assertIn('broken_result_link', self.codes())

    def test_symlinked_intake_rejected(self):
        path = self.vault / self.accepted / 'linked.md'
        try:
            path.symlink_to(self.vault / self.accepted / 'source.md')
        except OSError as error:
            self.skipTest(f'symlink privilege unavailable: {error}')
        self.assertEqual(self.inspect()['status'], 'input-error')

    def test_placeholder_reuses_intake_audit(self):
        self.write(self.accepted + 'source.md', 'TODO: extract source')
        self.assertIn('placeholder_source', self.codes())

    def test_chunks_reuse_chunk_audit(self):
        self.write(self.accepted + 'chunks/unlisted.md', '# 章节\n正文。')
        self.assertIn('missing_chunks_index', self.codes())

    def test_json_and_exit_contract(self):
        cases = [(self.source, 0), ('raw/digested/missing.pdf', 2)]
        for source, expected in cases:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = audit.main([source, '--vault', str(self.vault), '--json'])
            self.assertEqual(code, expected)
            self.assertEqual(json.loads(output.getvalue())['schema'], 1)
        (self.vault / 'wiki/sources/资料/报告.md').unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audit.main([self.source, '--vault', str(self.vault)]), 1)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(audit.main(['--json']), 2)
        self.assertEqual(json.loads(output.getvalue())['status'], 'input-error')


if __name__ == '__main__':
    unittest.main()
