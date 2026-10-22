import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.agents/skills/source-extraction/scripts'))
from build_chunks import build
from chunk_contract import valid_chunk_component


class BuildChunksTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.vault = Path(self.temp.name)
        self.root = self.vault/'intake'/'tmp'/'example'
        self.root.mkdir(parents=True)
        self.source('First paragraph with meaningful content.\nSecond paragraph with meaningful content.\n')

    def source(self, text):
        (self.root/'source.md').write_text(text, encoding='utf-8')

    def plan(self):
        return {'source_sha256': hashlib.sha256((self.root/'source.md').read_bytes()).hexdigest(), 'chunks': [{'path':'01-主题.md','title':'主题','start':1,'end':2}]}

    def test_first_build_and_unchanged_rebuild_ignore_unrelated_invalid_utf8(self):
        (self.vault/'unrelated.md').write_bytes(b'\xff')
        build(self.root, self.plan(), self.vault)
        before = (self.root/'chunks/01-主题.md').read_bytes()
        build(self.root, self.plan(), self.vault)
        self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())

    def test_first_build_ignores_unrelated_linked_document(self):
        import build_chunks
        note = self.vault/'unrelated.md'
        note.write_text('Unrelated text', encoding='utf-8')
        with patch.object(build_chunks, 'linked_boundary', side_effect=lambda p: p == note):
            build(self.root, self.plan(), self.vault)
        self.assertTrue((self.root/'chunks/01-主题.md').is_file())

    def test_changed_chunk_still_requires_readable_vault(self):
        build(self.root, self.plan(), self.vault)
        before = (self.root/'chunks/01-主题.md').read_bytes()
        (self.vault/'unrelated.md').write_bytes(b'\xff')
        self.source('Changed evidence with meaningful content.\nSecond paragraph with meaningful content.\n')
        plan = self.plan()
        with self.assertRaises(UnicodeError):
            build(self.root, plan, self.vault)
        self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())

    def test_physical_delete_retains_asset_when_scan_incomplete(self):
        self.source('Paragraph ![icon](a.png)\nOther prose.\n')
        (self.root/'a.png').write_bytes(b'image')
        (self.vault/'unrelated.md').write_bytes(b'\xff')
        plan = self.plan()
        plan['images'] = [{'file':'source.md', 'occurrence':1, 'expected':'a.png', 'action':'delete',
                           'authorized':True, 'reason':'decoration', 'delete_file':True}]
        result = build(self.root, plan, self.vault)
        self.assertTrue((self.root/'a.png').is_file())
        self.assertNotIn('![icon]', (self.root/'source.md').read_text())
        self.assertFalse(result['attachment_actions'][0]['deleted'])
        self.assertIn('incomplete reference scan', result['attachment_actions'][0]['reason'])

    def test_unrelated_footnote_allows_rebuild_but_its_inbound_link_protects(self):
        build(self.root, self.plan(), self.vault)
        note = self.vault/'note.md'
        note.write_text('A fact[^1].\n\n[^1]: Supporting explanation.\n', encoding='utf-8')
        plan = self.plan(); plan['chunks'][0]['title'] = 'Changed title'
        build(self.root, plan, self.vault)
        before = (self.root/'chunks/01-主题.md').read_bytes()
        note.write_text('A fact[^1].\n\n[^1]: [Evidence](<intake/tmp/example/chunks/01-主题.md> "Evidence")\n', encoding='utf-8')
        self.source('Changed evidence.\nSecond meaningful paragraph.\n')
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, 'reference to changed chunk'):
            build(self.root, plan, self.vault)
        self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())
        for reference in ('[ref]: https://example.test', '[Evidence][ref]'):
            note.write_text(reference, encoding='utf-8')
            with self.subTest(reference=reference), self.assertRaisesRegex(ValueError, 'unsupported reference syntax'):
                build(self.root, plan, self.vault)
            self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())

    def test_unrelated_titled_external_link_allows_changed_chunk(self):
        build(self.root, self.plan(), self.vault)
        (self.vault/'note.md').write_text('[Help](<https://example.test/help> "Help title")', encoding='utf-8')
        plan = self.plan(); plan['chunks'][0]['title'] = 'Changed title'
        build(self.root, plan, self.vault)
        self.assertIn('Changed title', (self.root/'chunks/01-主题.md').read_text(encoding='utf-8'))

    def test_titled_inbound_link_still_protects_changed_chunk(self):
        build(self.root, self.plan(), self.vault)
        (self.vault/'note.md').write_text('[Evidence](<intake/tmp/example/chunks/01-主题.md> "Evidence")', encoding='utf-8')
        self.source('Changed evidence.\nSecond meaningful paragraph.\n')
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, 'reference to changed chunk'):
            build(self.root, plan, self.vault)
        self.assertNotIn('Changed title', (self.root/'chunks/01-主题.md').read_text(encoding='utf-8'))

    def test_title_change_with_incoming_heading_anchor_preserves_old_chunk(self):
        build(self.root, self.plan(), self.vault)
        before = (self.root/'chunks/01-主题.md').read_bytes()
        (self.vault/'reference.md').write_text('[[intake/tmp/example/chunks/01-主题#主题]]', encoding='utf-8')
        plan = self.plan(); plan['chunks'][0]['title'] = 'Updated heading'
        with self.assertRaisesRegex(ValueError, 'reference to changed chunk'):
            build(self.root, plan, self.vault)
        self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())

    def test_removed_chunk_with_unknown_reference_stays_protected(self):
        build(self.root, self.plan(), self.vault)
        (self.vault/'note.md').write_text('<a href="intake/tmp/example/chunks/01-主题.md">source</a>', encoding='utf-8')
        plan = self.plan(); plan['chunks'][0]['path'] = '02-new.md'
        with self.assertRaisesRegex(ValueError, 'unsupported reference syntax'):
            build(self.root, plan, self.vault)
        self.assertTrue((self.root/'chunks/01-主题.md').exists())

    def test_remote_markup_preserved_and_local_link_rebased(self):
        text = ('Prose [site](https://example.com "Site title") ![remote](https://example.com/a.png "Title")\n'
                '<img src="https://example.com/a.png" alt="Figure"> and [local](file.txt)\n'
                '[angle](<https://example.com> "Title") ![angle image](<https://example.com/a.png> "Title")\n')
        self.source(text)
        (self.root/'file.txt').write_text('target')
        plan = self.plan(); plan['chunks'][0]['end'] = 3
        build(self.root, plan, self.vault)
        body = (self.root/'chunks/01-主题.md').read_text(encoding='utf-8')
        self.assertIn(text.splitlines()[0], body)
        self.assertIn(text.splitlines()[2], body)
        self.assertIn('<img src="https://example.com/a.png" alt="Figure">', body)
        self.assertIn('[local](<../file.txt>)', body)
        self.assertEqual(text, (self.root/'source.md').read_text(encoding='utf-8'))

    def test_html_table_images_rebase_nested_chunks_without_normalizing(self):
        (self.root/'images').mkdir()
        (self.root/'images/示意 & 图.png').write_bytes(b'image')
        for attribute in ('SRC="images/示意%20&amp;%20图.png?size=1&amp;x=2#figure"',
                          "src='images/示意%20&amp;%20图.png'",
                          'src=images/示意%20&amp;%20图.png'):
            text = '<table><tr><td><IMG width="200" '+attribute+' alt="x > y"></td></tr></table>\nMore prose.\n'
            self.source(text)
            plan = self.plan(); plan['chunks'][0]['path'] = '01-组/01-主题.md'
            with self.subTest(attribute=attribute):
                build(self.root, plan, self.vault)
                body = (self.root/'chunks/01-组/01-主题.md').read_text(encoding='utf-8')
                self.assertTrue(body.endswith(text.replace('images/', '../../images/')))
                self.assertEqual(text, (self.root/'source.md').read_text(encoding='utf-8'))

    def test_multiline_html_tag_and_remote_or_code_samples(self):
        text = ('<img\n src="local.png" width="20"/>\n'
                '<img src="//example.test/a.png"><img src="data:image/png;base64,abc">\n'
                '`<img src="missing.png">`\n```html\n<img src="missing.png">\n```\n')
        self.source(text); (self.root/'local.png').write_bytes(b'image')
        plan = self.plan(); plan['chunks'][0]['end'] = len(text.splitlines())
        build(self.root, plan, self.vault)
        body = (self.root/'chunks/01-主题.md').read_text(encoding='utf-8')
        self.assertTrue(body.endswith(text.replace('src="local.png"', 'src="../local.png"')))

    def test_commented_remote_html_image_stays_verbatim(self):
        text = '<!-- <img src="https://example.com/a.png"> -->\nMeaningful prose.\n'
        self.source(text)
        build(self.root, self.plan(), self.vault)
        self.assertTrue((self.root/'chunks/01-主题.md').read_text(encoding='utf-8').endswith(text))
        self.assertEqual(text, (self.root/'source.md').read_text(encoding='utf-8'))

    def test_html_src_surrounding_whitespace_uses_same_path_for_check_and_rebase(self):
        for depth, chunk in ((1, '01-主题.md'), (2, '01-组/01-主题.md')):
            for attribute in ('src=" a b.png "', "src='\t a b.png\t '",
                              'src=&#32;a&#32;b.png&#32;',
                              'src="&#32;a b.png?x=1&amp;y=2&#32;"'):
                with self.subTest(depth=depth, attribute=attribute):
                    text = '<img width="20" '+attribute+' alt="Keep > this">\nProse.\n'
                    self.source(text); (self.root/'a b.png').write_bytes(b'image')
                    plan = self.plan(); plan['chunks'][0]['path'] = chunk
                    build(self.root, plan, self.vault)
                    body = (self.root/'chunks'/chunk).read_text(encoding='utf-8')
                    from build_chunks import html_images, local_html_path
                    tags = html_images(body, 'fixture')
                    self.assertEqual(len(tags), 1)
                    _, _, start, end, value = tags[0]
                    self.assertEqual(local_html_path(value), '../'*depth+'a b.png')
                    self.assertNotIn(' ', body[start:end])
                    self.assertIn('width="20"', body)
                    self.assertIn('alt="Keep > this"', body)
                    if '?x=' in attribute:
                        self.assertTrue(value.endswith('?x=1&y=2'))
                    self.assertEqual(text, (self.root/'source.md').read_text(encoding='utf-8'))

    def test_html_whitespace_wrapped_missing_src_retains_old_result(self):
        build(self.root, self.plan(), self.vault)
        before = (self.root/'chunks/01-主题.md').read_bytes()
        for attribute in ('src=" missing.png "', 'src=&#32;missing.png&#32;'):
            self.source('<img '+attribute+'>\nProse.\n')
            with self.subTest(attribute=attribute), self.assertRaisesRegex(ValueError, 'img src missing or outside'):
                build(self.root, self.plan(), self.vault)
            self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())

    def test_html_missing_or_outside_image_preserves_previous_chunks(self):
        build(self.root, self.plan(), self.vault)
        before = (self.root/'chunks/01-主题.md').read_bytes()
        (self.vault/'outside.png').write_bytes(b'image')
        for value in ('missing.png', '../../../outside.png'):
            self.source('Prose <img src="'+value+'">\nMore prose.\n')
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'source.md:1: img src missing or outside'):
                build(self.root, self.plan(), self.vault)
            self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())

    def test_html_srcset_and_invalid_src_are_actionable(self):
        for tag, diagnostic in (
                ('<img src="https://example.com/a.png" srcset="local.png 2x">', 'img srcset'),
                ('<img src="">', 'one nonempty src'),
                ('<img src="one.png" src="two.png">', 'one nonempty src')):
            self.source('Meaningful prose ' + tag + '\nMore prose.\n')
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, diagnostic):
                build(self.root, self.plan(), self.vault)
            self.assertFalse((self.root/'chunks').exists())

    def test_html_preserves_markdown_occurrences_and_protects_shared_attachment(self):
        self.source('<img src="a.png"> ![first](a.png) ![second](b.png)\nOther prose.\n')
        for name in ('a.png', 'b.png'):
            (self.root/name).write_bytes(b'image')
        plan = self.plan()
        plan['images'] = [dict(file='source.md', occurrence=1, expected='a.png', action='delete',
                               authorized=True, reason='decoration', delete_file=True),
                          dict(file='source.md', occurrence=2, expected='b.png', action='rename', to='renamed.png')]
        result = build(self.root, plan, self.vault)
        body = (self.root/'chunks/01-主题.md').read_text(encoding='utf-8')
        self.assertIn('<img src="../a.png">', body)
        self.assertIn('![second](<../renamed.png>)', body)
        self.assertNotIn('![first]', body)
        self.assertFalse(result['attachment_actions'][0]['deleted'])
        self.assertIn('retained reference', result['attachment_actions'][0]['reason'])

    def test_html_allows_changed_chunk_but_retains_inbound_protection(self):
        self.source('<img src="a.png">\nMeaningful prose.\n')
        (self.root/'a.png').write_bytes(b'image')
        build(self.root, self.plan(), self.vault)
        self.source('<img src="a.png">\nChanged meaningful prose.\n')
        build(self.root, self.plan(), self.vault)
        before = (self.root/'chunks/01-主题.md').read_bytes()
        (self.vault/'note.md').write_text('[[intake/tmp/example/chunks/01-主题]]', encoding='utf-8')
        plan = self.plan(); plan['chunks'][0]['title'] = 'Changed title'
        with self.assertRaisesRegex(ValueError, 'reference to changed chunk'):
            build(self.root, plan, self.vault)
        self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())

    def test_unknown_html_in_other_notes_keeps_existing_scan_protection(self):
        build(self.root, self.plan(), self.vault)
        before = (self.root/'chunks/01-主题.md').read_bytes()
        plan = self.plan(); plan['chunks'][0]['title'] = 'Changed title'
        for markup in ('<img>', '<img src="a.png" srcset="b.png 2x">'):
            (self.vault/'note.md').write_text(markup, encoding='utf-8')
            with self.subTest(markup=markup), self.assertRaisesRegex(ValueError, 'unsupported reference syntax'):
                build(self.root, plan, self.vault)
            self.assertEqual(before, (self.root/'chunks/01-主题.md').read_bytes())

    def test_unknown_html_retains_physical_asset_without_blocking_first_build(self):
        self.source('Paragraph ![icon](a.png)\nOther prose.\n')
        (self.root/'a.png').write_bytes(b'image')
        (self.vault/'note.md').write_text('<img src="a.png" srcset="b.png 2x">', encoding='utf-8')
        plan = self.plan()
        plan['images'] = [dict(file='source.md', occurrence=1, expected='a.png', action='delete',
                               authorized=True, reason='decoration', delete_file=True)]
        result = build(self.root, plan, self.vault)
        self.assertTrue((self.root/'a.png').is_file())
        self.assertIn('unsupported reference syntax', result['attachment_actions'][0]['reason'])

    def test_same_chunk_footnote_works_and_split_dependency_fails(self):
        text = 'A meaningful fact[^a].\n\n[^a]: Complete supporting explanation.\n'
        self.source(text)
        plan = self.plan(); plan['chunks'][0]['end'] = 3
        build(self.root, plan, self.vault)
        self.assertIn(text, (self.root/'chunks/01-主题.md').read_text(encoding='utf-8'))
        plan['chunks'] = [dict(path='01-主题.md', title='主题', start=1, end=2),
                          dict(path='02-说明.md', title='说明', start=3, end=3)]
        with self.assertRaisesRegex(ValueError, 'reference and definition in the same chunk'):
            build(self.root, plan, self.vault)
        self.assertIn(text, (self.root/'chunks/01-主题.md').read_text(encoding='utf-8'))

    def test_complete_build_keeps_source_and_recovery(self):
        before = (self.root/'source.md').read_bytes()
        result = build(self.root, self.plan(), self.vault)
        self.assertEqual(before, (self.root/'source.md').read_bytes())
        self.assertIsNone(result['recovery_copy'])
        self.assertFalse(list(self.root.parent.glob('.*-previous')))
        self.assertIn('Second paragraph', (self.root/'chunks/01-主题.md').read_text(encoding='utf-8'))

    def test_missing_overlapping_reversed_ranges_leave_old(self):
        for ranges in [[(1,1)], [(1,1),(1,2)], [(2,2),(1,1)]]:
            with self.subTest(ranges=ranges):
                plan = self.plan()
                plan['chunks'] = [{'path':f'{i+1:02d}-主题.md', 'title':'主题', 'start':a, 'end':b} for i,(a,b) in enumerate(ranges)]
                with self.assertRaisesRegex(ValueError, 'range|uncovered'):
                    build(self.root, plan, self.vault)
                self.assertFalse((self.root/'chunks').exists())

    def test_insert_preserves_existing_paths_and_index_order(self):
        plan = self.plan()
        plan['chunks'] = [{'path':'20-开篇.md','title':'开篇','start':1,'end':1}, {'path':'10-结尾.md','title':'结尾','start':2,'end':2}]
        build(self.root, plan, self.vault)
        index = (self.root/'chunks/index.md').read_text(encoding='utf-8')
        self.assertLess(index.index('[20-开篇]'), index.index('[10-结尾]'))
        self.assertTrue(valid_chunk_component('02'))
        self.assertTrue(valid_chunk_component('20-开篇'))
        self.assertFalse(valid_chunk_component('20-不合法?'))

    def test_authorized_delete_shared_attachment_retained(self):
        self.source('Paragraph text. ![icon](images/a.png)\nOther meaning ![warning](images/a.png)\n')
        (self.root/'images').mkdir()
        (self.root/'images/a.png').write_bytes(b'fixture image')
        plan = self.plan()
        plan['images'] = [{'file':'source.md','occurrence':1,'expected':'images/a.png','action':'delete','authorized':True,'reason':'Decorative mark only'}]
        result = build(self.root, plan, self.vault)
        text = (self.root/'source.md').read_text(encoding='utf-8')
        self.assertNotIn('![icon]', text)
        self.assertIn('![warning]', text)
        self.assertTrue((self.root/'images/a.png').exists())
        self.assertTrue(result['retained_original_attachments'])

    def test_wrong_target_unauthorized_delete_and_unsupported_fail(self):
        self.source('Paragraph ![icon](a.png)\nMore text.\n')
        (self.root/'a.png').write_bytes(b'image')
        for expected, authorized in [('wrong.png',True), ('a.png',False)]:
            plan = self.plan()
            plan['images'] = [{'file':'source.md','occurrence':1,'expected':expected,'action':'delete','authorized':authorized,'reason':'decorative'}]
            with self.assertRaises(ValueError):
                build(self.root, plan, self.vault)
            self.assertIn('![icon]', (self.root/'source.md').read_text())
        self.source('Paragraph ![[a.png]]\nMore text.\n')
        with self.assertRaisesRegex(ValueError,'unsupported image'):
            build(self.root, self.plan(), self.vault)

    def test_rename_copies_target_and_rebases_chunk(self):
        self.source('Paragraph ![icon](a.png)\nMore text.\n')
        (self.root/'a.png').write_bytes(b'image')
        plan = self.plan()
        plan['images'] = [{'file':'source.md','occurrence':1,'expected':'a.png','action':'rename','to':'images/流程.png'}]
        build(self.root, plan, self.vault)
        self.assertEqual(b'image',(self.root/'images/流程.png').read_bytes())
        self.assertIn('../images/流程.png', (self.root/'chunks/01-主题.md').read_text(encoding='utf-8'))

    def test_nested_group_order_and_no_gap_requirement(self):
        self.source('First body.\nSecond body.\nThird body.\n')
        plan = self.plan()
        plan['chunks'] = [
            {'path':'30-开头.md','title':'开头','start':1,'end':1},
            {'path':'10-分组/40-中段.md','title':'中段','start':2,'end':2},
            {'path':'20-结尾.md','title':'结尾','start':3,'end':3}]
        build(self.root,plan,self.vault)
        index=(self.root/'chunks/index.md').read_text(encoding='utf-8')
        self.assertLess(index.index('[30-开头]'),index.index('[10-分组]'))
        self.assertLess(index.index('[10-分组]'),index.index('[20-结尾]'))

    def test_equal_size_change_does_not_inherit_exception(self):
        plan=self.plan()
        plan['chunks'][0].update(reviewed=True,size_reason='Independent topic')
        build(self.root,plan,self.vault)
        build(self.root,self.plan(),self.vault)
        self.assertIn('accepted-under', (self.root/'chunks/index.md').read_text(encoding='utf-8'))
        self.source((self.root/'source.md').read_text().replace('First','Third'))
        build(self.root,self.plan(),self.vault)
        self.assertNotIn('accepted-under', (self.root/'chunks/index.md').read_text(encoding='utf-8'))

    def test_image_edit_preserves_crlf_and_other_bytes(self):
        original=b'Paragraph ![icon](a.png)\r\nOther prose.\r\n'
        (self.root/'source.md').write_bytes(original)
        (self.root/'a.png').write_bytes(b'image')
        plan=self.plan()
        plan['images']=[{'file':'source.md','occurrence':1,'expected':'a.png','action':'delete','authorized':True,'reason':'decoration'}]
        build(self.root,plan,self.vault)
        self.assertEqual(original.replace(b'![icon](a.png)',b''),(self.root/'source.md').read_bytes())

    def test_missing_local_image_rejected_before_publication(self):
        self.source('Text ![missing](absent.png)\nSecond body.\n')
        with self.assertRaisesRegex(ValueError,'missing or outside'):
            build(self.root,self.plan(),self.vault)
        self.assertFalse((self.root/'chunks').exists())

    def test_old_numeric_name_in_prose_does_not_block(self):
        build(self.root,self.plan(),self.vault)
        (self.vault/'note.md').write_text('The 01-主题 wording is ordinary prose.', encoding='utf-8')
        plan=self.plan(); plan['chunks'][0]['path']='03-新名.md'
        build(self.root,plan,self.vault)
        self.assertTrue((self.root/'chunks/03-新名.md').exists())

    def test_explicit_physical_delete_and_shared_alias_protection(self):
        for retained in [False, True]:
            with self.subTest(retained=retained):
                self.source('Paragraph ![icon](a.png)\nOther prose.\n')
                (self.root/'a.png').write_bytes(b'image')
                note=self.vault/'.private'/'note.md'
                if retained:
                    note.parent.mkdir(exist_ok=True)
                    note.write_text('![[a.png|warning]]',encoding='utf-8')
                plan=self.plan()
                plan['images']=[{'file':'source.md','occurrence':1,'expected':'a.png','action':'delete','authorized':True,'reason':'decoration','delete_file':True}]
                result=build(self.root,plan,self.vault)
                self.assertEqual(retained,(self.root/'a.png').exists())
                self.assertEqual(not retained,result['attachment_actions'][0]['deleted'])

    def test_concurrent_writer_is_rejected(self):
        lock=self.root.parent/('.'+self.root.name+'-build.lock')
        lock.write_text('fixture owner')
        with self.assertRaisesRegex(ValueError,'another build'):
            build(self.root,self.plan(),self.vault)
        self.assertEqual('fixture owner',lock.read_text())

    def test_removed_old_basename_wikilink_blocks_rebuild(self):
        plan=self.plan(); plan['chunks'][0]['path']='01-old.md'
        build(self.root,plan,self.vault)
        (self.vault/'note.md').write_text('[[01-old|cited evidence]]',encoding='utf-8')
        plan=self.plan(); plan['chunks'][0]['path']='02-new.md'
        with self.assertRaisesRegex(ValueError,'reference to changed chunk'):
            build(self.root,plan,self.vault)
        self.assertTrue((self.root/'chunks/01-old.md').exists())

    def test_titled_external_link_retains_asset(self):
        self.source('Paragraph ![icon](a.png)\nOther prose.\n')
        (self.root/'a.png').write_bytes(b'image')
        (self.vault/'note.md').write_text('[diagram](intake/tmp/example/a.png "Diagram title")',encoding='utf-8')
        plan=self.plan()
        plan['images']=[{'file':'source.md','occurrence':1,'expected':'a.png','action':'delete','authorized':True,'reason':'decoration','delete_file':True}]
        result=build(self.root,plan,self.vault)
        self.assertTrue((self.root/'a.png').exists())
        self.assertIn('retained reference',result['attachment_actions'][0]['reason'])

    def test_titled_source_link_rejected_before_moving(self):
        self.source('Paragraph [diagram](a.png "Diagram title")\nOther prose.\n')
        (self.root/'a.png').write_bytes(b'image')
        with self.assertRaisesRegex(ValueError,'unsupported inline link'):
            build(self.root,self.plan(),self.vault)
        self.assertFalse((self.root/'chunks').exists())

    def test_old_chunk_asset_is_preserved(self):
        self.source('Paragraph ![diagram](chunks/assets/a.png)\nOther prose.\n')
        (self.root/'chunks/assets').mkdir(parents=True)
        (self.root/'chunks/assets/a.png').write_bytes(b'original attachment')
        build(self.root,self.plan(),self.vault)
        self.assertEqual(b'original attachment',(self.root/'chunks/assets/a.png').read_bytes())
        self.assertIn('../chunks/assets/a.png',(self.root/'chunks/01-主题.md').read_text(encoding='utf-8'))

    def test_system_ancestor_alias_is_allowed(self):
        import build_chunks
        with patch.object(build_chunks,'linked_boundary',side_effect=lambda p:p==self.vault.parent):
            build(self.root,self.plan(),self.vault)
        self.assertTrue((self.root/'chunks').exists())

    def test_windows_names_and_bracket_label(self):
        self.assertFalse(valid_chunk_component('01-bad"name'))
        self.assertFalse(valid_chunk_component('01-bad|name'))
        plan=self.plan(); plan['chunks'][0]['path']='01-合法]标题.md'
        build(self.root,plan,self.vault)
        self.assertTrue((self.root/'chunks/01-合法]标题.md').exists())
        index=(self.root/'chunks/index.md').read_text(encoding='utf-8')
        self.assertIn('&#93;',index)
        self.assertIn('[source.md](../source.md)',index)
        self.assertIn('inclusive source-line ranges',index)

    def test_code_image_examples_are_not_missing_assets(self):
        self.source('Real body text.\n```markdown\n![sample](missing.png)\n```\nInline `![sample](also-missing.png)` example.\n')
        plan=self.plan(); plan['chunks'][0]['end']=5
        result=build(self.root,plan,self.vault)
        self.assertEqual('warn',result['audit'])

    def test_absolute_image_is_rejected_and_root_link_is_not_rebased(self):
        self.source('Text ![outside](/outside.png)\nOther prose.\n')
        with self.assertRaisesRegex(ValueError,'missing or outside'):
            build(self.root,self.plan(),self.vault)
        self.source('Text [root note](/note.md)\nOther prose.\n')
        build(self.root,self.plan(),self.vault)
        self.assertIn('[root note](/note.md)',(self.root/'chunks/01-主题.md').read_text(encoding='utf-8'))

    def test_source_headings_have_a_content_description(self):
        self.source('# Source heading\nFirst prose.\n## Second heading\nSecond prose.\n')
        plan=self.plan(); plan['chunks'][0]['end']=4
        build(self.root,plan,self.vault)
        self.assertIn('Complete source lines 1-4',(self.root/'chunks/index.md').read_text(encoding='utf-8'))

    def test_removed_group_index_reference_blocks(self):
        plan=self.plan(); plan['chunks'][0]['path']='01-group/01-old.md'
        build(self.root,plan,self.vault)
        (self.vault/'note.md').write_text('[[intake/tmp/example/chunks/01-group/index|group evidence]]',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'reference to changed chunk'):
            build(self.root,self.plan(),self.vault)
        self.assertTrue((self.root/'chunks/01-group/index.md').exists())

    def test_canvas_reference_retains_physical_asset(self):
        self.source('Paragraph ![icon](a.png)\nOther prose.\n')
        (self.root/'a.png').write_bytes(b'image')
        (self.vault/'diagram.canvas').write_text('{"nodes":[{"type":"file","file":"intake/tmp/example/a.png"}]}',encoding='utf-8')
        plan=self.plan()
        plan['images']=[{'file':'source.md','occurrence':1,'expected':'a.png','action':'delete','authorized':True,'reason':'decoration','delete_file':True}]
        result=build(self.root,plan,self.vault)
        self.assertTrue((self.root/'a.png').exists())
        self.assertIn('non-Markdown',result['attachment_actions'][0]['reason'])

    def test_linked_ancestor_rejected_before_read(self):
        import build_chunks
        ancestor=self.root.parent
        with patch.object(build_chunks,'linked_boundary',side_effect=lambda p:p==ancestor):
            with self.assertRaisesRegex(ValueError,'junction'):
                build(self.root,self.plan(),self.vault)

    def test_replacement_failure_restores_previous(self):
        original = Path.rename
        def interrupted(path, to):
            if '-build-' in path.name and not path.name.endswith('-previous'):
                raise OSError('simulated interrupted publication')
            return original(path, to)
        with patch.object(Path,'rename',interrupted):
            with self.assertRaises(OSError):
                build(self.root,self.plan(),self.vault)
        self.assertTrue((self.root/'source.md').exists())
        self.assertFalse((self.root/'chunks').exists())

    def test_changed_cited_chunk_blocks_and_old_remains(self):
        build(self.root,self.plan(),self.vault)
        (self.vault/'note.md').write_text('[[intake/tmp/example/chunks/01-主题]]', encoding='utf-8')
        plan=self.plan(); plan['chunks'][0]['path']='03-新名.md'
        with self.assertRaisesRegex(ValueError,'note.md'):
            build(self.root,plan,self.vault)
        self.assertTrue((self.root/'chunks/01-主题.md').exists())


if __name__ == '__main__':
    unittest.main()
