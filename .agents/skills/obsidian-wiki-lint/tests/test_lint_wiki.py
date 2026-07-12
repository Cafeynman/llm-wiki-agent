import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

# Adjust sys.path to import the scripts
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import lint_wiki

class TestLintWiki(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        self.scope = "wiki"
        (self.vault / "wiki").mkdir()
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_attachment_not_flagged_broken(self):
        # Create a note
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[attachment.pdf]] and [another](folder/img.png)", encoding="utf-8")
        
        # Create the attachments
        (self.vault / "attachment.pdf").touch()
        (self.vault / "wiki" / "folder").mkdir()
        (self.vault / "wiki" / "folder" / "img.png").touch()
        
        # Run lint, capture stdout if needed, but we can just check the return value
        # lint() returns 1 if broken, 0 if clean
        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)
            
        self.assertEqual(result, 0, "Lint should not report broken links for existing attachments.")

    def test_broken_link_flagged(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[missing.pdf]]", encoding="utf-8")
        
        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)
            
        self.assertEqual(result, 1, "Lint should report broken links for missing files.")

    def test_empty_scope_returns_input_error(self):
        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 2, "Lint should fail when the requested scope has no Markdown pages.")
        error_reported = any(
            "No Markdown pages found under scope: wiki" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(error_reported)
        
    def test_md_link_prevents_orphan(self):
        note_path = self.vault / "wiki" / "entry.md"
        note_path.write_text("Link to [other](other.md)", encoding="utf-8")
        
        other_path = self.vault / "wiki" / "other.md"
        other_path.write_text("I am not an orphan.", encoding="utf-8")
        
        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)
            
        self.assertEqual(result, 0)
        # Verify that "Orphan: wiki/other.md" was not printed
        for call in mock_print.call_args_list:
            self.assertNotIn("Orphan: wiki/other.md", call[0][0] if call[0] else "")

    def test_nested_md_links_resolve_from_source_directory(self):
        section = self.vault / "wiki" / "section"
        section.mkdir()
        (section / "entry.md").write_text(
            "[Sibling](sibling.md) [Parent](../parent.md)",
            encoding="utf-8",
        )
        (section / "sibling.md").write_text("Sibling.", encoding="utf-8")
        (self.vault / "wiki" / "parent.md").write_text("Parent.", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0)
        output = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        self.assertNotIn("Orphan: wiki/section/sibling.md", output)
        self.assertNotIn("Orphan: wiki/parent.md", output)

    def test_vault_root_md_link_resolves_from_leading_slash(self):
        section = self.vault / "wiki" / "section"
        section.mkdir()
        (section / "entry.md").write_text(
            "[Root](/wiki/root.md)",
            encoding="utf-8",
        )
        (self.vault / "wiki" / "root.md").write_text("Root.", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0)
        output = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        self.assertNotIn("Orphan: wiki/root.md", output)

    def test_vault_root_md_link_normalizes_path_segments(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            "[Target](/wiki/section/../target.md)",
            encoding="utf-8",
        )
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0)
        output = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        self.assertNotIn("Orphan: wiki/target.md", output)

    def test_protocol_relative_md_link_is_external(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("[External](//wiki/target.md)", encoding="utf-8")
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0)
        output = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        self.assertNotIn("Broken:", output)
        self.assertIn("Orphan: wiki/target.md", output)

    def test_md_link_cannot_resolve_outside_vault(self):
        outside = self.vault.parent / f"{self.vault.name}-outside.md"
        outside.write_text("Outside.", encoding="utf-8")
        try:
            note_path = self.vault / "wiki" / "note.md"
            note_path.write_text(
                f"[Outside](../../{outside.name})",
                encoding="utf-8",
            )

            with patch("builtins.print") as mock_print:
                result = lint_wiki.lint(self.vault, self.scope)

            self.assertEqual(result, 1)
            output = "\n".join(
                call[0][0] for call in mock_print.call_args_list if call[0]
            )
            self.assertIn(f"Broken: ../{outside.name}", output)
        finally:
            outside.unlink(missing_ok=True)

    def test_wikilink_cannot_resolve_outside_vault(self):
        outside = self.vault.parent / f"{self.vault.name}-outside.md"
        outside.write_text("Outside.", encoding="utf-8")
        try:
            note_path = self.vault / "wiki" / "note.md"
            note_path.write_text(
                f"[[../{outside.name}]] [[wiki/../../{outside.name}]]",
                encoding="utf-8",
            )

            with patch("builtins.print") as mock_print:
                result = lint_wiki.lint(self.vault, self.scope)

            self.assertEqual(result, 1)
            output = "\n".join(
                call[0][0] for call in mock_print.call_args_list if call[0]
            )
            self.assertIn(f"Broken: ../{outside.name}", output)
        finally:
            outside.unlink(missing_ok=True)

    def test_wikilink_cannot_escape_and_reenter_vault(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            f"[[../{self.vault.name}/wiki/target.md]]",
            encoding="utf-8",
        )
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1)
        output = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        self.assertIn(f"Broken: ../{self.vault.name}/wiki/target.md", output)
        self.assertIn("Orphan: wiki/target.md", output)

    def test_markdown_link_cannot_escape_and_reenter_vault(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            f"[Target](../../{self.vault.name}/wiki/target.md)",
            encoding="utf-8",
        )
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1)
        output = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        self.assertIn(f"Broken: ../{self.vault.name}/wiki/target.md", output)
        self.assertIn("Orphan: wiki/target.md", output)

    def test_links_inside_code_are_ignored(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """Inline `[[wiki/missing-inline.md]]` and `[missing](missing-inline.md)`.

~~~markdown
[[wiki/missing-fence.md]]
[missing](missing-fence.md)
~~~
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0)
        output = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        self.assertNotIn("Broken:", output)

    def test_active_link_outside_code_remains_checked(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            "`[[wiki/example.md]]` but [[wiki/missing.md]].",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1)
        output = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        self.assertIn("Broken: wiki/missing.md", output)

    def test_folder_without_trailing_slash_flagged_broken(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[folder]]", encoding="utf-8")
        
        (self.vault / "folder").mkdir()
        
        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)
            
        self.assertEqual(result, 1, "Lint should report broken links for folders.")
        # Ensure it was reported as broken
        broken_reported = any("Broken: folder.md" in (call[0][0] if call[0] else "") for call in mock_print.call_args_list)
        self.assertTrue(broken_reported, "Should report folder.md as broken since Obsidian expects a note.")

    def test_wikilink_directory_with_trailing_slash_not_flagged_broken(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[wiki/folder/]]", encoding="utf-8")

        (self.vault / "wiki" / "folder").mkdir()

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should accept explicit directory links that point to existing directories.")

    def test_wikilink_directory_with_backslash_not_flagged_broken(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[wiki\\folder\\]]", encoding="utf-8")

        (self.vault / "wiki" / "folder").mkdir()

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should accept backslash-terminated explicit directory links.")

    def test_markdown_directory_link_with_trailing_slash_not_flagged_broken(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [folder](folder/)", encoding="utf-8")

        (self.vault / "wiki" / "folder").mkdir()

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should accept Markdown links to existing directories.")

    def test_missing_explicit_directory_flagged_broken_without_appending_markdown_suffix(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[wiki/missing/]]", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should report missing explicit directories.")
        broken_reported = any(
            (call[0][0] if call[0] else "") == "Broken: wiki/missing/"
            for call in mock_print.call_args_list
        )
        self.assertTrue(broken_reported, "Missing directory links should be reported without a .md suffix.")

    def test_explicit_directory_link_does_not_resolve_to_sibling_page(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[wiki/folder/]]", encoding="utf-8")

        (self.vault / "wiki" / "folder").mkdir()
        (self.vault / "wiki" / "folder.md").write_text("Sibling page.", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Existing directory links should not be resolved through sibling Markdown pages.")
        orphan_reported = any(
            "Orphan: wiki/folder.md" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(orphan_reported, "The sibling page should not receive incoming links from a directory link.")

    def test_encoded_space_directory_links_not_flagged_broken(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            "See [[wiki/My%20Folder/]] and [folder](/wiki/My%20Folder/).",
            encoding="utf-8",
        )

        (self.vault / "wiki" / "My Folder").mkdir()

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should decode URL-encoded spaces for explicit directory links.")

    def test_missing_frontmatter_intake_source_not_reported_broken(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources:
  - "[[intake/processed/source/source.md]]"
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Missing intake links in frontmatter sources should not be navigation failures.")

    def test_missing_body_intake_link_reported_broken(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("Processed [[intake/processed/source/source.md]].", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Missing intake links in body text should remain traceability failures.")
        broken_reported = any(
            "Broken: intake/processed/source/source.md" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(broken_reported)

    def test_frontmatter_sources_internal_paths_must_be_wikilinks(self):
        (self.vault / "raw" / "digested").mkdir(parents=True)
        (self.vault / "raw" / "digested" / "source.pdf").touch()
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources:
  - "raw/digested/source.pdf"
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should report internal source paths that are not wikilinks.")
        invalid_reported = any(
            "sources entry must be a quoted wikilink" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_sources_intake_paths_must_be_wikilinks(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources:
  - intake/processed/source/source.md
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should report bare intake source paths in frontmatter.")
        invalid_reported = any(
            "sources entry must be a quoted wikilink" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_sources_wikilinks_must_be_complete(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources:
  - "[[intake/processed/source/source.md"
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should report incomplete wikilinks in frontmatter sources.")
        invalid_reported = any(
            "sources entry must be a quoted wikilink" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_sources_allow_wikilinks_and_urls(self):
        (self.vault / "raw" / "digested").mkdir(parents=True)
        (self.vault / "raw" / "digested" / "source.pdf").touch()
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources:
  - "[[raw/digested/source.pdf]]"
  - "https://example.com/source"
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should accept wikilinked internal sources and quoted external URLs.")

    def test_frontmatter_sources_reject_unquoted_wikilinks(self):
        (self.vault / "raw" / "digested").mkdir(parents=True)
        (self.vault / "raw" / "digested" / "source.pdf").touch()
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources:
  - [[raw/digested/source.pdf]]
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject unquoted wikilink source entries.")
        invalid_reported = any(
            "sources entry must be a quoted wikilink" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_sources_allow_inline_sources_list(self):
        (self.vault / "raw" / "digested").mkdir(parents=True)
        (self.vault / "raw" / "digested" / "source.pdf").touch()
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources: ["[[raw/digested/source.pdf]]", "https://example.com/source"]
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should accept quoted inline source lists.")

    def test_frontmatter_sources_reject_unquoted_inline_wikilinks(self):
        (self.vault / "raw" / "digested").mkdir(parents=True)
        (self.vault / "raw" / "digested" / "source.pdf").touch()
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources: [[[raw/digested/source.pdf]]]
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject unquoted wikilinks in inline source lists.")
        invalid_reported = any(
            "sources entry must be a quoted wikilink" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_sources_reject_unquoted_inline_wikilink_scalar(self):
        (self.vault / "raw" / "digested").mkdir(parents=True)
        (self.vault / "raw" / "digested" / "source.pdf").touch()
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
sources: [[raw/digested/source.pdf]]
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject an unquoted inline wikilink scalar.")
        invalid_reported = any(
            "sources entry must be a quoted wikilink" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_tags_allow_no_space_tags(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
tags:
  - project
  - energy-policy
  - energy/policy
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should accept tags without whitespace.")

    def test_frontmatter_tags_reject_space_in_block_tag(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
tags:
  - "energy policy"
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject tags that contain spaces.")
        invalid_reported = any(
            "tags entry must not contain whitespace" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_tags_reject_space_in_inline_tag(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
tags: [project, "energy policy"]
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject inline tags that contain spaces.")
        invalid_reported = any(
            "tags entry must not contain whitespace" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_tags_allow_inline_list_with_comment(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
tags: [project, energy-policy] # browsing tags
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should accept inline tag lists with YAML comments.")

    def test_frontmatter_tags_reject_quoted_leading_or_trailing_space(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
tags:
  - " energy"
  - "policy "
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject quoted tags with leading or trailing whitespace.")
        invalid_reported = any(
            "tags entry must not contain whitespace" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_frontmatter_tags_reject_quoted_inline_leading_space(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """---
title: "Note"
tags: [project, " energy"]
---

Body.
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject quoted inline tags with preserved whitespace.")
        invalid_reported = any(
            "tags entry must not contain whitespace" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_table_wikilink_alias_requires_escaped_pipe(self):
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """| Source | Link |
| --- | --- |
| A | [[wiki/target.md|Target]] |
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject unescaped wikilink alias separators in tables.")
        invalid_reported = any(
            "wikilink alias separator must be escaped" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_single_column_table_wikilink_alias_requires_escaped_pipe(self):
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """| Link |
| --- |
| [[wiki/target.md|Target]] |
""",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should check wikilink aliases in single-column tables.")
        invalid_reported = any(
            "wikilink alias separator must be escaped" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_table_wikilink_alias_allows_escaped_pipe(self):
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """| Source | Link |
| --- | --- |
| A | [[wiki/target.md\\|Target]] |
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should accept escaped wikilink alias separators in tables.")

    def test_table_wikilink_alias_ignores_inline_code_example(self):
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """| Example |
| --- |
| `[[wiki/target.md|Target]]` |
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should ignore wikilink alias examples inside inline code.")

    def test_non_table_wikilink_alias_allows_unescaped_pipe(self):
        (self.vault / "wiki" / "target.md").write_text("Target.", encoding="utf-8")
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[wiki/target.md|Target]].", encoding="utf-8")

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should allow ordinary wikilink aliases outside Markdown tables.")

    def test_bare_traceability_path_requires_wikilink(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("Reviewed raw/digested/source.pdf for evidence.", encoding="utf-8")

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject bare internal traceability paths in body text.")
        invalid_reported = any(
            "internal traceability path must use a wikilink" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_parenthesized_or_bracketed_bare_traceability_path_requires_wikilink(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            "Reviewed (raw/digested/source.pdf) and [intake/processed/source/source.md].",
            encoding="utf-8",
        )

        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 1, "Lint should reject parenthesized or bracketed bare paths.")
        invalid_reported = any(
            "internal traceability path must use a wikilink" in (call[0][0] if call[0] else "")
            for call in mock_print.call_args_list
        )
        self.assertTrue(invalid_reported)

    def test_traceability_path_ignored_inside_inline_code_and_links(self):
        (self.vault / "raw" / "digested").mkdir(parents=True)
        (self.vault / "raw" / "digested" / "source.pdf").touch()
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """Inline example: `raw/digested/source.pdf`.
Wikilink: [[raw/digested/source.pdf]].
Markdown link: [source](/raw/digested/source.pdf).
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should ignore traceability paths inside code and links.")

    def test_traceability_path_ignored_inside_double_backtick_inline_code(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            "Inline example: ``raw/digested/source.pdf``.",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should ignore traceability paths inside double-backtick code.")

    def test_traceability_path_ignored_inside_code_block(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text(
            """```text
raw/digested/source.pdf
```
""",
            encoding="utf-8",
        )

        with patch("builtins.print"):
            result = lint_wiki.lint(self.vault, self.scope)

        self.assertEqual(result, 0, "Lint should ignore traceability path examples inside fenced code.")

if __name__ == "__main__":
    unittest.main()
