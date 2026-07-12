import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

# Adjust sys.path to import the scripts
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import crosslink_concepts
from crosslink_concepts import Concept

class TestCrosslinkConcepts(unittest.TestCase):
    def test_link_line_cjk_boundary(self):
        concept = Concept(name="模型", target="wiki/concepts/模型.md")
        line = "这是一种语言模型，可以处理文字。"
        
        updated, count = crosslink_concepts.link_line(line, concept, 2)
        self.assertEqual(count, 1)
        self.assertIn("[[wiki/concepts/模型.md|模型]]", updated)

    def test_link_line_english_boundary(self):
        concept = Concept(name="model", target="wiki/concepts/model.md")
        line = "This is a language model, and modeling is fun."
        
        updated, count = crosslink_concepts.link_line(line, concept, 2)
        self.assertEqual(count, 1)
        # Should link "model" but NOT "modeling"
        self.assertIn("[[wiki/concepts/model.md|model]],", updated)
        self.assertNotIn("[[wiki/concepts/model.md|model]]ing", updated)
        
    def test_link_line_table_escape(self):
        concept = Concept(name="API", target="wiki/concepts/API.md")
        line = "| Command | Uses the API to |"
        
        updated, count = crosslink_concepts.link_line(line, concept, 1)
        self.assertEqual(count, 1)
        # Check that it escaped the pipe
        self.assertIn(r"[[wiki/concepts/API.md\|API]]", updated)

    def test_crosslink_file_optional_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            file_path = tmp_path / "test.md"
            file_path.write_text("The core rule is here.", encoding="utf-8")
            
            concept = Concept(name="rule", target="wiki/concepts/rule.md")
            
            updated, total = crosslink_concepts.crosslink_file(file_path, [concept], 2)
            
            self.assertEqual(total, 1)
            self.assertIn("[[wiki/concepts/rule.md|rule]]", updated)

    def test_build_concepts_discovers_nested_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            concepts_dir = Path("wiki/concepts")
            concepts_abs = vault / concepts_dir
            nested = concepts_abs / "subject"
            nested.mkdir(parents=True)
            (concepts_abs / "top.md").write_text(
                "---\ntitle: Top Concept\n---\n", encoding="utf-8"
            )
            (nested / "deep.md").write_text(
                "---\ntitle: Deep Concept\n---\n", encoding="utf-8"
            )

            concepts = crosslink_concepts.build_concepts(
                vault, concepts_dir, aliases={}
            )
            targets = {concept.name: concept.target for concept in concepts}

            self.assertEqual(targets["Top Concept"], "wiki/concepts/top")
            self.assertEqual(
                targets["Deep Concept"], "wiki/concepts/subject/deep"
            )

    def test_crosslink_updates_nested_page_with_full_target_and_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            concepts_dir = Path("wiki/concepts")
            concepts_abs = vault / concepts_dir
            nested = concepts_abs / "subject"
            nested.mkdir(parents=True)
            (concepts_abs / "target.md").write_text(
                "---\ntitle: Target Term\n---\n", encoding="utf-8"
            )
            source = nested / "source.md"
            source.write_text(
                "---\ntitle: Source Concept\n---\n\nTarget Term. Target Term. Target Term.",
                encoding="utf-8",
            )

            with patch("builtins.print"):
                result = crosslink_concepts.crosslink(
                    vault,
                    concepts_dir,
                    alias_file=None,
                    max_per_concept=2,
                    write=True,
                )

            self.assertEqual(result, 0)
            updated = source.read_text(encoding="utf-8")
            self.assertEqual(
                updated.count("[[wiki/concepts/target|Target Term]]"), 2
            )
            self.assertIn("]]. Target Term.", updated)

    def test_duplicate_concept_term_is_reported_and_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            concepts_dir = Path("wiki/concepts")
            concepts_abs = vault / concepts_dir
            (concepts_abs / "one").mkdir(parents=True)
            (concepts_abs / "two").mkdir()
            (concepts_abs / "one" / "first.md").write_text(
                "---\ntitle: Shared Term\n---\n", encoding="utf-8"
            )
            (concepts_abs / "two" / "second.md").write_text(
                "---\ntitle: Shared Term\n---\n", encoding="utf-8"
            )

            with patch("builtins.print") as mock_print:
                concepts = crosslink_concepts.build_concepts(
                    vault, concepts_dir, aliases={}
                )

            self.assertNotIn("Shared Term", {concept.name for concept in concepts})
            output = "\n".join(
                call[0][0] for call in mock_print.call_args_list if call[0]
            )
            self.assertIn("Ambiguous concept term skipped: Shared Term", output)

if __name__ == "__main__":
    unittest.main()
