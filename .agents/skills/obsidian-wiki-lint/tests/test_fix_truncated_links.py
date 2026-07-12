import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fix_truncated_links


class TestFixTruncatedLinks(unittest.TestCase):
    def test_write_changes_active_link_and_preserves_code_examples(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("intake/processed/example")
            target_abs = vault / target_dir
            target_abs.mkdir(parents=True)
            (target_abs / "complete-source.md").write_text(
                "Target.", encoding="utf-8"
            )

            source_file = Path("wiki/source.md")
            source_abs = vault / source_file
            source_abs.parent.mkdir()
            source_abs.write_text(
                """Active [[intake/processed/example/complete]].
Inline `[[intake/processed/example/complete]]`.

```markdown
[[intake/processed/example/complete]]
[sample](intake/processed/example/complete)
```
""",
                encoding="utf-8",
            )

            with patch("builtins.print"):
                result = fix_truncated_links.fix_links(
                    vault, source_file, target_dir, write=True
                )

            self.assertEqual(result, 0)
            self.assertEqual(
                source_abs.read_text(encoding="utf-8"),
                """Active [[intake/processed/example/complete-source]].
Inline `[[intake/processed/example/complete]]`.

```markdown
[[intake/processed/example/complete]]
[sample](intake/processed/example/complete)
```
""",
            )

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target_dir = Path("intake/processed/example")
            target_abs = vault / target_dir
            target_abs.mkdir(parents=True)
            (target_abs / "complete-source.md").write_text(
                "Target.", encoding="utf-8"
            )

            source_file = Path("wiki/source.md")
            source_abs = vault / source_file
            source_abs.parent.mkdir()
            original = "[[intake/processed/example/complete]]"
            source_abs.write_text(original, encoding="utf-8")

            with patch("builtins.print"):
                result = fix_truncated_links.fix_links(
                    vault, source_file, target_dir, write=False
                )

            self.assertEqual(result, 0)
            self.assertEqual(source_abs.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
