"""Read-only structural closeout audit for one lifecycle source."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

from audit_intake_file import AuditArgumentError, AuditArgumentParser, DEFAULT_LARGE_SOURCE_THRESHOLD, inspect_markdown
from audit_chunks import inspect_chunks
from chunk_contract import DEFAULT_SMALL_CHUNK_THRESHOLD

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "obsidian-wiki-lint" / "scripts"))
import lint_wiki as lint
from markdown_code import mask_markdown_code
from obsidian_links import WIKILINK_RE, split_wikilink

STATES = ("digested", "needs-review", "ignored", "unsupported")
NOT_CHECKED = ["semantic source quality and acceptance", "source-card substantive completeness", "review and log completeness", "link heading/block anchors", "external URL reachability", "reference-style and HTML links"]


def safe_path(vault: Path, path: Path) -> Path:
    """Reject links before resolving, including links in ancestors of missing paths."""
    path = Path(os.path.abspath(path))
    if not path.is_relative_to(vault):
        raise ValueError(f"path outside vault: {path}")
    for part in (path, *path.parents):
        if part == vault:
            break
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError(f"linked path is not supported: {part}")
    if not path.resolve().is_relative_to(vault):
        raise ValueError(f"path outside vault: {path}")
    return path


def markdown_files(vault: Path, folder: Path):
    """Walk only the selected intake tree; never follow linked children."""
    for directory, dirs, files in os.walk(folder, onerror=lambda error: (_ for _ in ()).throw(error)):
        for name in dirs + files:
            safe_path(vault, Path(directory) / name)
        for name in sorted(files):
            if name.endswith(".md"):
                yield Path(directory) / name


def link_lookup_files(vault: Path):
    """Index names only for basename resolution; skip linked and ignored trees."""
    files = []
    for directory, dirs, names in os.walk(vault):
        root = Path(directory)
        dirs[:] = [name for name in dirs if name not in lint.SKIP_DIRS
                   and not (root / name).is_symlink()
                   and not (hasattr(root / name, "is_junction") and (root / name).is_junction())]
        files.extend(root / name for name in names if name.endswith(".md") and not (root / name).is_symlink())
    return files

def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot read UTF-8 Markdown {path}: {error}") from error

def inspect_closeout(vault: Path, source: str) -> dict:
    result = {"schema": 1, "source": source, "scope": "structural-only", "status": "pass", "errors": [], "warnings": [], "not_checked": NOT_CHECKED.copy()}

    def add(code, path, message, warning=False):
        result["warnings" if warning else "errors"].append({"code": code, "path": str(path), "message": message})

    try:
        vault = vault.resolve()
        if not vault.is_dir():
            raise ValueError(f"vault is not a directory: {vault}")
        safe_path(vault, vault)
        identity = PurePosixPath(source.replace("\\", "/"))
        parts = identity.parts
        if identity.is_absolute() or len(parts) < 3 or parts[0] != "raw" or parts[1] not in STATES or ".." in parts or ":" in source:
            raise ValueError(f"source must be vault-relative raw/<state>/<original-file>, without traversal: {source}")
        state = parts[1]
        relative = Path(*parts[2:])
        selected = safe_path(vault, vault / Path(*parts))
        if not selected.is_file():
            raise ValueError(f"source file does not exist: {selected}")
        with selected.open("rb") as stream:
            stream.read(1)
        result["source"] = selected.relative_to(vault).as_posix()
        result["state"] = state
        found = []
        for candidate_state in STATES:
            candidate = safe_path(vault, vault / "raw" / candidate_state / relative)
            if candidate.exists():
                found.append(candidate.relative_to(vault).as_posix())
        if len(found) != 1:
            add("multiple_raw_states", result["source"], f"source exists in {len(found)} states: {', '.join(found)}")
        inbox = safe_path(vault, vault / "inbox" / relative)
        if inbox.exists():
            add("inbox_residue", inbox.relative_to(vault).as_posix(), "handled source remains in inbox")
        # Only two accepted originals prove an intake/card identity conflict.
        digested_sibling = False
        pending_sibling = False
        for base in [vault / "inbox", *(vault / "raw" / name for name in STATES)]:
            parent = safe_path(vault, base / relative.parent)
            if parent.is_dir():
                for sibling in parent.iterdir():
                    if not sibling.is_dir() and sibling.name != relative.name and sibling.stem == relative.stem:
                        is_digested = base == vault / "raw/digested"
                        digested_sibling = digested_sibling or is_digested
                        pending_sibling = pending_sibling or base == vault / "raw/needs-review"
                        add("source_identity_collision", sibling.relative_to(vault).as_posix(),
                            "different originals map to the same intake/card path; manually confirm ownership before accepting another source",
                            warning=not (state == "digested" and is_digested))
        stem = relative.with_suffix("")
        temporary = safe_path(vault, vault / "intake/tmp" / stem)
        if state != "needs-review" and temporary.exists():
            if pending_sibling:
                add("temporary_output_ownership_uncertain", temporary.relative_to(vault).as_posix(),
                    "a needs-review same-stem original also exists; confirm ownership before cleaning temporary output", warning=True)
            else:
                add("temporary_residue", temporary.relative_to(vault).as_posix(), "completed source retains temporary intake output")
        accepted = safe_path(vault, vault / "intake/processed" / stem)
        card = safe_path(vault, vault / "wiki/sources" / stem.parent / (stem.name + ".md"))
        if state != "digested":
            for candidate in (accepted, card):
                if candidate.exists():
                    if digested_sibling:
                        add("accepted_output_ownership_uncertain", candidate.relative_to(vault).as_posix(),
                            "a digested same-stem original also exists; manually confirm which original owns this output", warning=True)
                    else:
                        add("accepted_state_conflict", candidate.relative_to(vault).as_posix(), f"accepted output exists for raw state {state}")
        else:
            required = [accepted / name for name in ("source.md", "summary.md", "manifest.md")] + [card]
            texts = {}
            for path in required:
                safe_path(vault, path)
                if not path.is_file():
                    add("missing_required_file", path.relative_to(vault).as_posix(), "digested source requires this intake file or matching source card")
                else:
                    text = read_utf8(path)
                    texts[path] = text
                    if not text.strip():
                        add("empty_required_file", path.relative_to(vault).as_posix(), "required Markdown file is empty")
            scoped = list(markdown_files(vault, accepted)) if accepted.is_dir() else []
            if card in texts:
                scoped.append(card)
            for path in scoped:
                if path not in texts:
                    texts[path] = read_utf8(path)
            source_md = accepted / "source.md"
            if source_md in texts:
                audit = inspect_chunks(accepted, DEFAULT_SMALL_CHUNK_THRESHOLD, DEFAULT_LARGE_SOURCE_THRESHOLD) if (accepted / "chunks").exists() else inspect_markdown(source_md, DEFAULT_LARGE_SOURCE_THRESHOLD)
                for category in ("errors", "warnings"):
                    for issue in audit[category]:
                        issue_path = Path(issue["path"])
                        if not issue_path.is_absolute():
                            issue_path = accepted / issue_path
                        add(issue["code"], issue_path.relative_to(vault).as_posix(), issue["message"], category == "warnings")
            lookup = None
            for path, content in texts.items():
                rel = path.relative_to(vault).as_posix()
                maintained = lint.uses_page_contract(vault, path)
                if maintained:
                    for check in (lint.lint_frontmatter_sources, lint.lint_frontmatter_tags, lint.lint_table_wikilink_aliases, lint.lint_bare_traceability_paths, lint.lint_footnote_references, lint.lint_source_card_placeholders):
                        for message in check(content, rel):
                            add("markdown_contract", rel, message)
                masked = mask_markdown_code(content)
                targets = [(split_wikilink(match.group(1)), True) for match in WIKILINK_RE.finditer(masked)]
                targets += [(match.group(1).strip(), False) for match in lint.MD_LINK_RE.finditer(masked)]
                for target, wiki in targets:
                    if not target or target.startswith("//") or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                        continue
                    # Only basename wikilinks need a vault filename lookup, not content reads.
                    if wiki and "/" not in lint.normalize_link_path(target) and lookup is None:
                        lookup = lint.build_lookup(link_lookup_files(vault), vault)
                    files, stems = lookup if lookup is not None else (set(), {})
                    resolution = lint.resolve_target(vault, target, files, stems) if wiki else lint.resolve_markdown_target(vault, rel, target, files)
                    if resolution:
                        resolved, directory = resolution
                        try:
                            destination = safe_path(vault, vault / resolved)
                        except ValueError as error:
                            add("broken_result_link", rel, f"invalid link target {target}: {error}")
                            continue
                        if not (destination.is_dir() if directory else destination.is_file()):
                            add("broken_result_link", rel, f"link target does not exist: {target} (resolved: {resolved})")
    except (ValueError, OSError, UnicodeError) as error:
        add("invalid_input", source, f"cannot audit source: {error}")
        result["status"] = "input-error"
    if result["status"] != "input-error":
        result["status"] = "fail" if result["errors"] else "warn" if result["warnings"] else "pass"
    for category in ("errors", "warnings"):
        result[category].sort(key=lambda issue: (issue["path"], issue["code"], issue["message"]))
    return result


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    parser = AuditArgumentParser(description=__doc__)
    parser.add_argument("source", help="Vault-relative raw/<state>/<original-file>")
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    try:
        args = parser.parse_args(arguments)
        result = inspect_closeout(args.vault, args.source)
    except AuditArgumentError as error:
        result = {"schema": 1, "source": None, "scope": "structural-only", "status": "input-error", "errors": [{"code": "invalid_arguments", "path": "", "message": str(error)}], "warnings": [], "not_checked": NOT_CHECKED.copy()}
    if "--json" in arguments:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Source closeout: {result['status']} (structural-only)")
        for category in ("errors", "warnings"):
            for issue in result[category]:
                print(f"{category}: {issue['path']}: {issue['code']}: {issue['message']}")
        print("Not checked: " + "; ".join(result["not_checked"]))
    return 2 if result["status"] == "input-error" else 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
