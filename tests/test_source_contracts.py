from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SourceContractTest(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_markitdown_dependency_and_public_commands(self) -> None:
        pyproject = self.read("pyproject.toml")
        self.assertIn(
            "markitdown[audio-transcription,az-doc-intel,docx,outlook,pdf,pptx,xls,xlsx,youtube-transcription]>=0.1.6",
            pyproject,
        )
        self.assertNotIn("markitdown[all]", pyproject)
        self.assertNotIn("az-content-understanding", pyproject)

        surfaces = (
            self.read(".agents/skills/markitdown-skill/SKILL.md")
            + self.read(
                ".agents/skills/source-extraction/references/providers/markitdown/setup.md"
            )
            + self.read(
                ".agents/skills/source-extraction/references/providers/markitdown/usage.md"
            )
            + self.read(".agents/skills/markitdown-skill/scripts/batch_convert.py")
            + self.read(".env.example")
        )
        for stale_text in (
            "--llm-client",
            "--llm-model",
            "MARKITDOWN_OCR_MODEL",
            "OPENAI_API_KEY",
            "AZURE_DOCUMENT_INTELLIGENCE_KEY",
        ):
            self.assertNotIn(stale_text, surfaces)
        self.assertIn("--use-plugins", surfaces)
        self.assertIn("--list-plugins", surfaces)
        self.assertIn("AZURE_API_KEY", surfaces)

        removed_files = (
            "README.md",
            "POST_INSTALL.md",
            "USAGE-GUIDE.md",
            "reference.md",
            "package.json",
            "_meta.json",
        )
        skill_root = ROOT / ".agents/skills/markitdown-skill"
        for filename in removed_files:
            self.assertFalse((skill_root / filename).exists(), filename)


    def test_source_routes_and_public_output_paths(self) -> None:
        skill = self.read(".agents/skills/source-extraction/SKILL.md")
        for relative in ("intake-lifecycle.md", "source-kinds.md", "pdf-preflight.md",
                         "large-source-chunking.md", "contract.md"):
            self.assertIn(relative, skill)
            self.assertTrue((ROOT / ".agents/skills/source-extraction/references" / relative).is_file())
        lifecycle = self.read(".agents/skills/source-extraction/references/intake-lifecycle.md")
        for token in ("source.md", "summary.md", "manifest.md", "chunks/index.md",
                      "reviews/source-review/YYYY-MM-DD.md", "intake/logs/YYYY-MM-DD.md",
                      "inbox/web/<source-language-page-title>--<url-hash>.md"):
            self.assertIn(token, lifecycle)
        for outcome in ("digested", "needs-review", "ignored", "unsupported"):
            self.assertIn(f"raw/{outcome}/", lifecycle)

    def test_defuddle_public_capture_commands(self) -> None:
        skill = self.read(".agents/skills/defuddle/SKILL.md")
        usage = self.read(".agents/skills/source-extraction/references/providers/defuddle/usage.md")
        self.assertIn("defuddle parse <url> --json", skill)
        self.assertNotIn("defuddle parse <url> --json --md", skill)
        for text in (skill, usage):
            self.assertIn("contentMarkdown", text)
        self.assertIn("inbox/web/", usage)
        self.assertIn("defuddle parse <url> --md -o <output.md>", skill)

    def test_review_size_values_are_documented(self) -> None:
        chunking = self.read(".agents/skills/source-extraction/references/large-source-chunking.md")
        for value in ("accepted-under", "accepted-over", "reviewed"):
            self.assertIn(value, chunking)
        # Actual size, naming, preservation and scanner behavior is covered by
        # audit/chunk/Obsidian fixture tests, not source-code substring checks.

    def test_canonical_page_types_are_documented(self) -> None:
        wiki = self.read("WIKI.md")
        for value in ("source", "entity", "concept", "claim", "synthesis"):
            self.assertIn(f"`{value}`", wiki)
        for value in ("artifact", "question"):
            self.assertIn(f"`type: {value}`", wiki)


if __name__ == "__main__":
    unittest.main()
