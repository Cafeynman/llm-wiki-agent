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

    def test_live_url_has_one_capture_route(self) -> None:
        defuddle_skill = self.read(".agents/skills/defuddle/SKILL.md")
        defuddle_usage = self.read(
            ".agents/skills/source-extraction/references/providers/defuddle/usage.md"
        )
        defuddle_setup = self.read(
            ".agents/skills/source-extraction/references/providers/defuddle/setup.md"
        )
        wiki = self.read("WIKI.md")
        agents = self.read("AGENTS.md")

        self.assertIn("defuddle parse <url> --json --md", defuddle_skill)
        self.assertIn(
            "defuddle parse https://example.com --json --md", defuddle_setup
        )
        self.assertIn("inbox/web/", defuddle_usage)
        self.assertNotIn("-o intake/tmp", defuddle_skill + defuddle_usage)
        self.assertIn("sole exception", wiki)
        self.assertIn("live-URL source captures", agents)

    def test_provider_attachments_share_intake_lifecycle(self) -> None:
        wiki = self.read("WIKI.md")
        contract = self.read(".agents/skills/source-extraction/references/contract.md")
        mineru = self.read(
            ".agents/skills/source-extraction/references/providers/mineru/usage.md"
        )

        for content in (wiki, contract, mineru):
            self.assertIn("same intake folder", content)
            self.assertIn("promote", content.lower())
            self.assertIn("delete", content.lower())
        self.assertIn("does not authorize OCR", wiki)

    def test_archive_has_one_lifecycle_outcome(self) -> None:
        wiki = self.read("WIKI.md")
        source_kinds = self.read(
            ".agents/skills/source-extraction/references/source-kinds.md"
        )

        self.assertIn("one Source Review Gate outcome", wiki)
        self.assertIn("one raw-state destination", wiki)
        self.assertIn("every inspected member and its disposition", wiki)
        self.assertIn("one lifecycle source", source_kinds)
        self.assertNotIn("classify each useful member separately", source_kinds)

    def test_chunk_paths_are_numeric_and_titles_remain_content(self) -> None:
        wiki = self.read("WIKI.md")
        chunking = self.read(
            ".agents/skills/source-extraction/references/large-source-chunking.md"
        )
        audit = self.read(
            ".agents/skills/source-extraction/scripts/audit_chunks.py"
        )

        for content in (wiki, chunking):
            self.assertIn("`01.md`", content)
            self.assertIn("`01/`", content)
            self.assertIn("exact source", content.lower())
        self.assertIn("invalid_chunk_path_component", audit)
        self.assertIn("non_sequential_chunk_path_components", audit)
        for stale_text in (
            "source-provided order token, keep the source title",
            "generated numeric prefixes",
            "mixed_generated_prefix_in_sibling_group",
            "intrinsic order tokens",
        ):
            self.assertNotIn(stale_text, wiki + chunking + audit)

    def test_page_type_values_are_scoped(self) -> None:
        wiki = self.read("WIKI.md")

        self.assertIn("For canonical knowledge pages under `wiki/`", wiki)
        self.assertIn("`source`, `entity`, `concept`, `claim`, or `synthesis`", wiki)
        self.assertIn("`type: artifact` and `type: question`", wiki)


if __name__ == "__main__":
    unittest.main()
