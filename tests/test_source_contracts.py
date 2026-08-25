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
        usage_docs = self.read("docs/usage.md") + self.read("docs/usage.zh-CN.md")
        wiki = self.read("WIKI.md")
        lifecycle = self.read(
            ".agents/skills/source-extraction/references/intake-lifecycle.md"
        )

        self.assertIn("defuddle parse <url> --json", defuddle_skill)
        self.assertNotIn("defuddle parse <url> --json --md", defuddle_skill)
        self.assertIn("contentMarkdown", defuddle_skill)
        self.assertIn("contentMarkdown", defuddle_usage)
        self.assertIn("npm install -g defuddle@0.19.2", defuddle_setup)
        self.assertIn("request approval", defuddle_setup)
        self.assertIn("defuddle parse <url> --md -o <output.md>", defuddle_skill)
        self.assertIn("General Webpage Cleanup", defuddle_skill)
        self.assertIn("automatically", usage_docs)
        self.assertIn("自动安装", usage_docs)
        self.assertIn("inbox/web/", defuddle_usage)
        self.assertNotIn("-o intake/tmp", defuddle_skill + defuddle_usage)
        self.assertIn("sole exception", lifecycle)
        self.assertIn("source-extraction", wiki)
        self.assertIn("Generated live-URL captures", wiki)

    def test_provider_attachments_share_intake_lifecycle(self) -> None:
        wiki = self.read("WIKI.md")
        contract = self.read(".agents/skills/source-extraction/references/contract.md")
        lifecycle = self.read(
            ".agents/skills/source-extraction/references/intake-lifecycle.md"
        )
        mineru = self.read(
            ".agents/skills/source-extraction/references/providers/mineru/usage.md"
        )

        for content in (lifecycle, contract, mineru):
            self.assertIn("same intake folder", content)
            self.assertIn("promote", content.lower())
            self.assertIn("delete", content.lower())
        self.assertIn("does not authorize OCR", lifecycle)
        self.assertIn("text-first", wiki.lower())

    def test_archive_has_one_lifecycle_outcome(self) -> None:
        wiki = self.read("WIKI.md")
        lifecycle = self.read(
            ".agents/skills/source-extraction/references/intake-lifecycle.md"
        )
        source_kinds = self.read(
            ".agents/skills/source-extraction/references/source-kinds.md"
        )

        self.assertIn("Source Review Gate", wiki)
        self.assertIn("one Source Review Gate outcome", lifecycle)
        self.assertIn("one raw-state destination", lifecycle)
        self.assertIn("every inspected member and its disposition", lifecycle)
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

        self.assertIn("numeric", wiki)
        for content in (chunking,):
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

    def test_canonical_source_and_chunk_size_exception_contract(self) -> None:
        lifecycle = self.read(
            ".agents/skills/source-extraction/references/intake-lifecycle.md"
        )
        chunking = self.read(
            ".agents/skills/source-extraction/references/large-source-chunking.md"
        )
        source_audit = self.read(
            ".agents/skills/source-extraction/scripts/audit_intake_file.py"
        )
        chunk_audit = self.read(
            ".agents/skills/source-extraction/scripts/audit_chunks.py"
        )
        chunk_contract = self.read(
            ".agents/skills/source-extraction/scripts/chunk_contract.py"
        )
        recorder = self.read(
            ".agents/skills/source-extraction/scripts/record_chunk_exception.py"
        )

        self.assertIn("canonical accepted Markdown extraction", lifecycle)
        self.assertIn("do not overwrite, truncate, or reorder", lifecycle)
        self.assertIn("Excerpt-Type", lifecycle + chunking)
        self.assertNotIn("either contain the full extracted text", chunking)
        self.assertIn("default soft minimum is 2000", chunking)
        self.assertIn("hard maximum is 10000", chunking)
        self.assertIn("does not decide whether adjacent chunks can merge", chunking)
        self.assertIn("块 | 标题与覆盖范围 | 内容说明 | 规模与尺寸裁决 | 内容评审", chunking)
        self.assertIn("<!-- chunk-size-exceptions", chunking)
        self.assertIn("record_chunk_exception.py", chunking)
        self.assertIn('SCHEMA_VERSION = 2', source_audit)
        self.assertIn('SCHEMA_VERSION = 2', chunk_audit)
        self.assertIn('DEFAULT_SMALL_CHUNK_THRESHOLD = 2000', chunk_contract)
        self.assertIn('DEFAULT_SMALL_CHUNK_THRESHOLD', chunk_audit)
        self.assertIn("atomic_write_text", recorder)

    def test_manifest_is_thin_and_final_processed_markdown_is_linted(self) -> None:
        lifecycle = self.read(
            ".agents/skills/source-extraction/references/intake-lifecycle.md"
        )

        for required in (
            "canonical raw source link",
            "provider, profile or mode",
            "OCR, transcription, and frame-OCR state",
            "Source Review outcome",
            "intake-log link",
            "focused Obsidian lint",
        ):
            self.assertIn(required, lifecycle)
        self.assertIn("Do not copy chunk mapping", lifecycle)

    def test_wikilink_scanner_is_shared_and_source_card_placeholders_are_exact(self) -> None:
        lint = self.read(".agents/skills/obsidian-wiki-lint/scripts/lint_wiki.py")
        fixer = self.read(
            ".agents/skills/obsidian-wiki-lint/scripts/fix_truncated_links.py"
        )
        scanner = self.read(
            ".agents/skills/obsidian-wiki-lint/scripts/obsidian_links.py"
        )
        templates = self.read("docs/wiki-page-templates.md")
        quality = self.read(".agents/skills/wiki-quality-review/SKILL.md")

        self.assertNotIn('re.compile(r"\\[\\[([^\\]]+)\\]\\]")', lint + fixer)
        self.assertIn("from obsidian_links import WIKILINK_RE", lint)
        self.assertIn("from obsidian_links import WIKILINK_RE", fixer)
        self.assertIn('text.find("]]", start + 2)', scanner)
        self.assertIn("exact instructional placeholder", templates)
        self.assertIn("template placeholders reported by the standard lint", quality)
        self.assertIn("fixed number of bullets", quality)

    def test_page_type_values_are_scoped(self) -> None:
        wiki = self.read("WIKI.md")

        self.assertIn("For canonical knowledge pages under `wiki/`", wiki)
        self.assertIn("`source`, `entity`, `concept`, `claim`, or `synthesis`", wiki)
        self.assertIn("`type: artifact` and `type: question`", wiki)


if __name__ == "__main__":
    unittest.main()
