import sys
from pathlib import Path
import tempfile
import unittest

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

if __name__ == "__main__":
    unittest.main()
