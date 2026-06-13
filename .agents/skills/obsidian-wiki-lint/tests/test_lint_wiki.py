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
        (self.vault / "folder").mkdir()
        (self.vault / "folder" / "img.png").touch()
        
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

    def test_folder_flagged_broken(self):
        note_path = self.vault / "wiki" / "note.md"
        note_path.write_text("See [[folder]]", encoding="utf-8")
        
        (self.vault / "folder").mkdir()
        
        with patch("builtins.print") as mock_print:
            result = lint_wiki.lint(self.vault, self.scope)
            
        self.assertEqual(result, 1, "Lint should report broken links for folders.")
        # Ensure it was reported as broken
        broken_reported = any("Broken: folder.md" in (call[0][0] if call[0] else "") for call in mock_print.call_args_list)
        self.assertTrue(broken_reported, "Should report folder.md as broken since Obsidian expects a note.")

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

if __name__ == "__main__":
    unittest.main()
