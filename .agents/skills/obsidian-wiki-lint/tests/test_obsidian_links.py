import sys
from pathlib import Path
import unittest


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from obsidian_links import (
    WIKILINK_RE,
    build_wikilink_inner,
    parse_wikilink_inner,
    split_wikilink,
)


class TestObsidianLinks(unittest.TestCase):
    def test_single_closing_bracket_inside_target_does_not_end_link(self):
        text = "Before [[intake/processed/国家电网生[2009]133号/source]] after"

        matches = list(WIKILINK_RE.finditer(text))

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].group(0), "[[intake/processed/国家电网生[2009]133号/source]]")
        self.assertEqual(matches[0].group(1), "intake/processed/国家电网生[2009]133号/source")
        self.assertEqual(matches[0].span(), (7, len(text) - 6))

    def test_alias_heading_block_and_embed_parts_are_preserved(self):
        text = "![[folder/目标]片#^block|显示名]]"
        match = next(WIKILINK_RE.finditer(text))
        parts = parse_wikilink_inner(match.group(1))

        self.assertEqual(parts.target, "folder/目标]片")
        self.assertEqual(parts.fragment, "#^block")
        self.assertEqual(parts.alias, "显示名")
        self.assertFalse(parts.alias_separator_escaped)
        self.assertEqual(build_wikilink_inner(parts, target="folder/目标]片-full"), "folder/目标]片-full#^block|显示名")

    def test_escaped_table_alias_separator_round_trips(self):
        parts = parse_wikilink_inner(r"folder/target#Heading\|Alias")

        self.assertEqual(parts.target, "folder/target")
        self.assertEqual(parts.fragment, "#Heading")
        self.assertEqual(parts.alias, "Alias")
        self.assertTrue(parts.alias_separator_escaped)
        self.assertEqual(build_wikilink_inner(parts), r"folder/target#Heading\|Alias")

    def test_compatibility_split_returns_target_without_fragment_or_alias(self):
        self.assertEqual(split_wikilink("folder/target#Heading|Alias"), "folder/target")

    def test_explicit_empty_alias_is_preserved(self):
        parts = parse_wikilink_inner("folder/target|")

        self.assertTrue(parts.has_alias)
        self.assertEqual(parts.alias, "")
        self.assertEqual(build_wikilink_inner(parts, target="folder/target-full"), "folder/target-full|")

    def test_sub_masks_complete_links_and_leaves_unclosed_text(self):
        text = "A [[one]name]] B [[unclosed"

        self.assertEqual(WIKILINK_RE.sub(" ", text), "A   B [[unclosed")

    def test_unclosed_opener_does_not_hide_later_complete_link(self):
        text = "A [[unclosed B [[valid]target]] C"

        matches = list(WIKILINK_RE.finditer(text))

        self.assertEqual([match.group(0) for match in matches], ["[[valid]target]]"])
        self.assertEqual(WIKILINK_RE.sub(" ", text), "A [[unclosed B   C")


if __name__ == "__main__":
    unittest.main()
