from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MaintenanceFeedbackContractTest(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_wiki_owns_detailed_report_routing_and_agents_owns_disclosure(self) -> None:
        wiki = self.read("WIKI.md")
        agents = self.read("AGENTS.md")
        wiki_text = " ".join(wiki.split())
        agents_text = " ".join(agents.split())

        self.assertIn("wiki-maintenance-feedback", wiki)
        self.assertIn("brief disclosure", wiki_text)
        self.assertIn("Materiality alone does not require a detailed package", wiki)
        self.assertIn("do not override an explicit report request", wiki_text)
        self.assertIn("does not authorize investigation, reproduction, repair", wiki_text)
        self.assertIn("not the defect's continuing-state owner", wiki_text)

        self.assertIn("## Foundation Defect Disclosure", agents)
        self.assertIn("must not be handled silently", agents_text)
        self.assertIn("credible but unconfirmed", agents_text)
        self.assertIn("immediately state the observation", agents_text)
        self.assertIn("action paused to avoid expanding the risk", agents_text)
        self.assertIn("do not call it a confirmed defect", agents_text)
        self.assertIn("the `Maintain Wiki` route in `WIKI.md`", agents_text)
        self.assertIn("does not grant permission", agents_text)
        self.assertNotIn("fixed-in-worktree", agents)
        self.assertNotIn("fixed-in-commit", agents)
        for duplicated_negative_trigger in (
            "Ordinary typos",
            "isolated broken links",
            "expected validation failures",
            "transient environment failures",
        ):
            self.assertNotIn(duplicated_negative_trigger, agents)

    def test_skill_packages_existing_evidence_without_becoming_a_debugger(self) -> None:
        skill = self.read(".agents/skills/wiki-maintenance-feedback/SKILL.md")
        skill_text = " ".join(skill.split())

        self.assertIn("name: wiki-maintenance-feedback", skill)
        frontmatter = skill.split("---", 2)[1]
        self.assertIn("Use only after WIKI.md routes the current work to this skill", frontmatter)
        for copied_trigger_condition in (
            "when the user asks",
            "confirmed reusable",
            "brief disclosure is insufficient",
        ):
            self.assertNotIn(copied_trigger_condition, frontmatter.lower())
        for copied_route_condition in (
            "when the user explicitly requests a maintainer-ready",
            "confirmed a reusable wiki-foundation defect",
            "brief disclosure cannot safely and accurately",
        ):
            self.assertNotIn(copied_route_condition, skill.lower())
        self.assertIn("packages and sanitizes existing findings and evidence", skill)
        self.assertIn(
            "does not investigate, reproduce, diagnose, fix, persist, track, or send",
            skill,
        )
        self.assertIn("Follow the `Maintain Wiki` route in `WIKI.md`", skill)
        self.assertIn("Do not restate or broaden its threshold here", skill)
        self.assertIn("Do not investigate, reproduce, diagnose, or repair", skill_text)
        self.assertIn("This skill never executes a reproduction attempt", skill)
        self.assertIn("report-template.md", skill)
        self.assertNotIn("use the smallest synthetic fixture", skill.lower())
        self.assertNotIn("prefer a synthetic minimal fixture", skill.lower())

        skill_root = ROOT / ".agents/skills/wiki-maintenance-feedback"
        packaged_files = {
            path.relative_to(skill_root).as_posix()
            for path in skill_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            packaged_files,
            {"SKILL.md", "references/report-template.md"},
        )

    def test_fixture_contract_reuses_only_existing_owning_workflow_evidence(self) -> None:
        skill = self.read(".agents/skills/wiki-maintenance-feedback/SKILL.md")
        template = self.read(
            ".agents/skills/wiki-maintenance-feedback/references/report-template.md"
        )
        skill_text = " ".join(skill.split())

        # No existing fixture: the report has a stable truthful value and the
        # reporting skill performs no fixture lifecycle or execution work.
        self.assertIn("When none exists, record `none`", skill)
        self.assertIn("Existing owning-workflow fixture: <sanitized reference or none>", template)
        self.assertIn("does not create, modify, execute, or re-execute a fixture", skill_text)

        # Existing fixture: reuse is limited to evidence already produced by
        # the owning workflow and does not mutate or transmit the source item.
        self.assertIn("already created by the evidence-producing owning workflow", skill_text)
        self.assertIn("sanitized reference or the minimum necessary excerpt", skill_text)
        self.assertIn("does not authorize changing the original fixture", skill_text)
        self.assertIn("does not authorize attaching or transmitting it", skill_text)

    def test_report_contract_separates_truthful_state_and_authorization(self) -> None:
        skill = self.read(".agents/skills/wiki-maintenance-feedback/SKILL.md")
        template = self.read(
            ".agents/skills/wiki-maintenance-feedback/references/report-template.md"
        )
        surfaces = skill + template

        for marker in (
            "fixed-in-worktree",
            "fixed-in-commit",
            "mitigated",
            "unresolved",
            "not-established",
            "reproduced",
            "observed-only",
            "blocked",
            "confirmed",
            "probable",
            "unknown",
        ):
            self.assertIn(marker, surfaces)

        for heading in (
            "## Summary",
            "## Discovery Context",
            "## Expected And Actual",
            "## Impact",
            "## Reproduction Or Blocking Evidence",
            "## Evidence And Cause",
            "## Disposition",
            "## Verification",
            "## Authorization Ledger",
            "## Next Action And Owner",
            "## Redaction And Attachment Scope",
        ):
            self.assertIn(heading, template)

        for permission in (
            "Repair authorization",
            "Persistence authorization",
            "Tracking create/update authorization",
            "External-transmission authorization",
        ):
            self.assertIn(permission, template)

        self.assertIn("net current state", skill)
        self.assertIn(
            "the fix is present in the report object's net current working tree",
            skill,
        )
        self.assertIn("bounded measure reduces impact or recurrence", skill)
        self.assertIn("underlying defect remains", skill)
        self.assertIn("This includes no attempt", skill)
        self.assertIn("an attempted reproduction could not complete", skill)
        self.assertIn("previous fix was reverted or cancelled", skill)
        self.assertIn("must not invent commands, output, or exit codes", skill)
        self.assertIn("unassessed", template)
        self.assertIn("four independent permissions", skill)
        self.assertIn("Finding confirmation: confirmed | unconfirmed", template)
        self.assertIn("reproduction state does not by itself establish or negate", template.lower())
        self.assertIn("completed attempt that did not reproduce", skill)
        self.assertIn("static contract violation", skill)
        self.assertIn("independently establishes that the defect exists", skill)
        self.assertIn("Evidence-producing owner / authorization", template)
        self.assertIn("`executed` maps to `reproduced` only when", template)
        self.assertIn(
            "`not-executed` (including no attempt) maps to `observed-only`",
            template,
        )

    def test_tracking_persistence_and_external_transmission_remain_separate(self) -> None:
        wiki = self.read("WIKI.md")
        skill = self.read(".agents/skills/wiki-maintenance-feedback/SKILL.md")
        skill_text = " ".join(skill.split())

        self.assertIn("response only", skill_text)
        self.assertIn("must not initialize a vault", skill_text)
        self.assertIn("must not silently overwrite", skill_text)
        self.assertIn("current workspace", skill_text)
        self.assertIn("must not query an external tracker", skill_text)
        self.assertIn("record `none`", skill_text)
        self.assertIn("untrusted evidence", skill_text)
        self.assertIn("<workspace>/", skill)
        self.assertIn("materially changes", skill_text)
        self.assertIn("fresh authorization", skill_text)
        self.assertIn("at most three fields", skill_text)
        self.assertIn("current response only; no persistent report reference", skill_text)
        self.assertIn("requires separately authorized persistence", skill_text)
        self.assertNotIn("scripts/", skill)
        self.assertNotIn("issue API", skill)
        self.assertNotIn("sender", skill.lower())
        self.assertIn("`questions/`", wiki)
        self.assertIn("`logs/wiki.md`", wiki)

    def test_docs_and_package_inventory_publish_the_same_user_contract(self) -> None:
        usage = self.read("docs/usage.md")
        usage_zh = self.read("docs/usage.zh-CN.md")
        inventory = self.read("scripts/package-files.txt")

        self.assertIn("maintainer-ready feedback", usage)
        self.assertIn("material, reusable foundation defect", usage)
        self.assertIn("维护人员可直接使用的反馈", usage_zh)
        self.assertIn("材料性、可复用的底座缺陷", usage_zh)
        self.assertIn("response only by default", usage)
        self.assertIn("默认只在响应中返回", usage_zh)

        for packaged_file in (
            ".agents/skills/wiki-maintenance-feedback/SKILL.md",
            ".agents/skills/wiki-maintenance-feedback/references/report-template.md",
        ):
            self.assertIn(packaged_file, inventory)


if __name__ == "__main__":
    unittest.main()
