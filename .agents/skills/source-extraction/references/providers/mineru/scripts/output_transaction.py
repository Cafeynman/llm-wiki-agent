"""Stage provider output and publish only explicitly recorded files.

Ownership lives in existing provider JSON reports. A backup of affected files
survives an interrupted publication; no directory is inferred to be disposable.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from functools import wraps
from pathlib import Path, PurePosixPath

OWNER = "mineru-output-v1"


def safe_path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if not parts.parts or parts.is_absolute() or ".." in parts.parts or "\\" in relative or any(":" in p for p in parts.parts):
        raise RuntimeError(f"unsafe output path: {relative}")
    # The caller-selected root may sit below a platform alias such as /var.
    # Trust its resolved parent, but never follow a link at or inside the root.
    if root.is_symlink() or root.is_junction():
        raise RuntimeError(f"linked output path is not supported: {root}")
    root = root.absolute()
    root = root.parent.resolve() / root.name
    target = root.joinpath(*parts.parts)
    path = target
    while True:
        if path.is_symlink() or path.is_junction():
            raise RuntimeError(f"linked output path is not supported: {path}")
        if path == root:
            break
        path = path.parent
    return target


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_record(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise RuntimeError(f"unowned output conflict: {path}") from exc
    if not isinstance(record, dict) or record.get("output_owner") != OWNER or not isinstance(record.get("owned_files"), dict):
        raise RuntimeError(f"unowned output conflict: {path}; use a fresh output directory for legacy results")
    return record


def publish_group(stage: Path, target: Path, report_name: str, files: list[Path], *, replace: bool = True) -> None:
    """Replace one source/report group, rolling back any failed filesystem write."""
    target.mkdir(parents=True, exist_ok=True)
    report = safe_path(target, report_name)
    lock = safe_path(target, ".mineru-publish.lock")
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise RuntimeError(f"output publication already active or interrupted: {lock}; inspect recovery directories before retrying") from exc
    with handle:
        handle.write(str(os.getpid()))
    backup = None
    try:
        previous = read_record(report)
        old_files = previous.get("owned_files", {})
        for name, expected in old_files.items():
            path = safe_path(target, name)
            if path.exists() and (not path.is_file() or digest(path) != expected):
                raise RuntimeError(f"modified owned output conflict: {path}")
        new_files = {p.relative_to(stage).as_posix(): digest(p) for p in files if p != stage / report_name}
        for name in new_files:
            path = safe_path(target, name)
            if path.exists() and name not in old_files:
                raise RuntimeError(f"unowned output conflict: {path}")
        metadata = json.loads((stage / report_name).read_text(encoding="utf-8"))
        metadata["output_owner"] = OWNER
        metadata["owned_files"] = new_files if replace else {**old_files, **new_files}
        (stage / report_name).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        affected = set(new_files) | ({*old_files} if replace else set()) | {report_name}
        for name in affected:
            safe_path(target, name)
        backup = Path(tempfile.mkdtemp(prefix=".mineru-recovery-", dir=target.parent))
        existing = sorted(name for name in affected if (target / name).exists())
        recovery = {"target": str(target.absolute()), "affected": sorted(affected), "existing": existing, "phase": "preparing"}
        recovery_path = backup / "recovery.json"
        recovery_path.write_text(json.dumps(recovery), encoding="utf-8")
        for name in existing:
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target / name, saved)
        recovery["phase"] = "recoverable"
        recovery_path.write_text(json.dumps(recovery), encoding="utf-8")
        try:
            for name in sorted(affected - {report_name}):
                path = target / name
                if name in new_files:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(stage / name, path)
                else:
                    path.unlink(missing_ok=True)
            os.replace(stage / report_name, report)
        except BaseException:
            for name in affected:
                path = target / name
                if name in existing:
                    shutil.copy2(backup / name, path)
                else:
                    path.unlink(missing_ok=True)
            recovery["phase"] = "restored"
            recovery_path.write_text(json.dumps(recovery), encoding="utf-8")
            raise
        recovery["phase"] = "published"
        recovery_path.write_text(json.dumps(recovery), encoding="utf-8")
        shutil.rmtree(backup)
        backup = None
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"output publication failed at {target}; recovery: {backup or 'not needed'}: {exc}") from exc
    finally:
        lock.unlink(missing_ok=True)


def publish_tree(stage: Path, target: Path, folders: list[str]) -> None:
    # Source reports own extracted files; batch reports always own root responses.
    errors = []
    needs_review = False
    batch_names = ("batch.json", "batch-result.zip", "response.json")
    batch_paths = {stage / name for name in batch_names}
    for relative in folders:
        report = stage / relative / "result.json"
        if not report.exists():
            continue
        folder = report.parent
        destination = target / folder.relative_to(stage)
        try:
            metadata = json.loads(report.read_text(encoding="utf-8"))
            needs_review = needs_review or bool(metadata.get("needs_review"))
            success = (folder / "source.md").is_file() and not metadata.get("extraction_error") and metadata.get("status", "completed") == "completed"
            if success:
                files = [p for p in folder.rglob("*") if p.is_file() and p not in batch_paths]
                publish_group(folder, destination, "result.json", files)
            else:
                # Keep last successful extraction and its report intact on failure.
                name = "last-failure.json" if (destination / "result.json").exists() else "result.json"
                if name != report.name:
                    report.rename(folder / name)
                publish_group(folder, destination, name, [], replace=False)
        except (RuntimeError, OSError, ValueError) as exc:
            errors.append(f"{destination}: {exc}")
    root_files = [stage / name for name in batch_names if (stage / name).is_file()]
    refresh_report = False
    if not root_files and not errors and (target / "batch.json").exists():
        try:
            refresh_report = read_record(safe_path(target, "batch.json")).get("output_owner") == OWNER
        except RuntimeError:
            # An unrelated batch report is outside this invocation's write scope.
            pass
    if root_files or errors or refresh_report:
        batch_path = stage / "batch.json"
        metadata = json.loads(batch_path.read_text(encoding="utf-8")) if batch_path.exists() else {"needs_review": needs_review}
        if errors:
            metadata["publication_errors"] = errors.copy()
            metadata["needs_review"] = True
        batch_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            publish_group(stage, target, "batch.json", root_files)
        except (RuntimeError, OSError, ValueError) as exc:
            errors.append(f"{target / 'batch.json'}: {exc}")
    if errors:
        raise RuntimeError("output publication failed: " + "; ".join(errors))


def staged_output(function):
    @wraps(function)
    def run(*args, **kwargs):
        output = Path(kwargs["output_dir"])
        safe_path(output, "source.md")
        output.parent.mkdir(parents=True, exist_ok=True)
        paths = kwargs.get("file_paths") or [item["path"] for item in kwargs.get("file_specs", [])]
        folders = [""] if len(paths) == 1 else [Path(path).stem for path in paths]
        if len({name.casefold() for name in folders}) != len(folders):
            raise RuntimeError("duplicate output directory names in requested files")
        with tempfile.TemporaryDirectory(prefix=".mineru-stage-", dir=output.parent) as temporary:
            stage = Path(temporary)
            try:
                result = function(*args, **{**kwargs, "output_dir": stage})
            except (RuntimeError, OSError, ValueError) as exc:
                try:
                    publish_tree(stage, output, folders)
                except (RuntimeError, OSError, ValueError) as publication_error:
                    raise RuntimeError(f"provider failed: {exc}; reporting/publication also failed: {publication_error}") from exc
                raise RuntimeError(str(exc)) from exc
            publish_tree(stage, output, folders)
            return result
    return run


def write_report(output: Path, name: str, metadata: dict) -> None:
    safe_path(output, name)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".mineru-stage-", dir=output.parent) as temporary:
        stage = Path(temporary)
        (stage / name).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        publish_group(stage, output, name, [], replace=False)
