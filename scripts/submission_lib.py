from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "calm-trade-growth-harness"
MAX_PACKAGE_BYTES = 100 * 1024 * 1024
ALLOWED_LOG_EXTENSIONS = {".md", ".txt", ".json", ".jsonl"}
FORBIDDEN_PATH_PARTS = {
    "_dev",
    ".git",
    ".agents",
    ".calm-trade",
    "dist",
    "__pycache__",
}
FORBIDDEN_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
}
EDITED_LOG_MARKERS = ("EDITED_LOG", "[EDITED]", "[REDACTED]", "REDACTED_FOR_SUBMISSION")
SECRET_RULES = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("openai_api_key", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----")),
]


class SubmissionError(ValueError):
    """Raised when submission packaging or verification fails."""


@dataclass(frozen=True)
class ScanFinding:
    path: str
    line_number: int
    category: str


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_forbidden_path(relative_path: PurePosixPath) -> bool:
    return any(part in FORBIDDEN_PATH_PARTS for part in relative_path.parts) or any(
        part in FORBIDDEN_FILE_NAMES or part.startswith(".env.") for part in relative_path.parts
    )


def _iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def _jsonl_has_disallowed_edited_marker(line: str) -> bool:
    """Ignore marker names quoted by exported tool commands, not log content."""
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return any(marker in line for marker in EDITED_LOG_MARKERS)

    def walk(value: object, path: tuple[str, ...]) -> bool:
        if isinstance(value, dict):
            return any(walk(child, path + (str(key),)) for key, child in value.items())
        if isinstance(value, list):
            return any(walk(child, path + (str(index),)) for index, child in enumerate(value))
        if not isinstance(value, str):
            return False
        if path[-2:] == ("item", "command"):
            return False
        return any(marker in value for marker in EDITED_LOG_MARKERS)

    return walk(payload, ())


def _scan_text_bytes(data: bytes, relative_path: str, *, edited_log_check: bool) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    text = data.decode("utf-8", errors="replace")
    for line_number, line in enumerate(text.splitlines(), start=1):
        for category, pattern in SECRET_RULES:
            if pattern.search(line):
                findings.append(ScanFinding(relative_path, line_number, category))
        if edited_log_check:
            if relative_path.endswith(".jsonl"):
                has_edited_marker = _jsonl_has_disallowed_edited_marker(line)
            else:
                has_edited_marker = any(marker in line for marker in EDITED_LOG_MARKERS)
            if has_edited_marker:
                findings.append(ScanFinding(relative_path, line_number, "edited_log_marker"))
    return findings


def _format_findings(findings: list[ScanFinding]) -> str:
    parts = [f"{finding.path}:{finding.line_number} [{finding.category}]" for finding in findings]
    return "; ".join(parts)


def _read_bytes(path: Path) -> bytes:
    with path.open("rb") as handle:
        return handle.read()


def _collect_plugin_entries() -> list[tuple[Path, PurePosixPath]]:
    if not PLUGIN_ROOT.exists():
        raise SubmissionError(f"plugin root is missing: {PLUGIN_ROOT}")
    entries: list[tuple[Path, PurePosixPath]] = []
    for path in _iter_files(PLUGIN_ROOT):
        relative = PurePosixPath("src") / path.relative_to(PLUGIN_ROOT).as_posix()
        if _is_forbidden_path(relative):
            continue
        entries.append((path, relative))
    return entries


def _collect_log_entries(log_root: Path) -> list[tuple[Path, PurePosixPath]]:
    if not log_root.exists() or not log_root.is_dir():
        raise SubmissionError(f"log directory is missing: {log_root}")
    entries: list[tuple[Path, PurePosixPath]] = []
    for path in _iter_files(log_root):
        if path.suffix.lower() not in ALLOWED_LOG_EXTENSIONS:
            raise SubmissionError(f"unsupported log extension: {path.name}")
        relative = PurePosixPath("logs") / path.relative_to(log_root).as_posix()
        if _is_forbidden_path(relative):
            raise SubmissionError(f"forbidden log path included: {relative.as_posix()}")
        entries.append((path, relative))
    if not entries:
        raise SubmissionError("log directory must contain at least one allowed file")
    return entries


def _write_zip(entries: list[tuple[PurePosixPath, bytes]], out_path: Path) -> None:
    with tempfile.NamedTemporaryFile(prefix="submission-", suffix=".zip", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for relative_path, data in entries:
                archive.writestr(relative_path.as_posix(), data)
        if temp_path.stat().st_size > MAX_PACKAGE_BYTES:
            raise SubmissionError("package exceeds 100 MB limit")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(temp_path), str(out_path))
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _write_sha_manifest(entries: list[tuple[PurePosixPath, bytes]], package_path: Path, manifest_path: Path) -> None:
    lines = [f"{file_sha256(package_path)}  {package_path.name}"]
    for relative_path, data in entries:
        lines.append(f"{bytes_sha256(data)}  {relative_path.as_posix()}")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_package_report(
    *,
    package_path: Path,
    report_path: Path,
    log_root: Path,
    log_entries: list[tuple[Path, PurePosixPath]],
    all_entries: list[tuple[PurePosixPath, bytes]],
    test_only: bool,
) -> None:
    label = "TEST_ONLY" if test_only else "FINAL"
    lines = [
        "# Package Report",
        "",
        f"- Package: `{package_path}`",
        f"- Package label: `{label}`",
        f"- Log source: `{log_root}`",
        f"- Secret scan: `PASS`",
        f"- Entry count: `{len(all_entries)}`",
        f"- Log file count: `{len(log_entries)}`",
        f"- ZIP size bytes: `{package_path.stat().st_size}`",
        "",
        "## Log SHA-256",
        "",
    ]
    for source_path, relative_path in log_entries:
        lines.append(f"- `{relative_path.as_posix()}` `{file_sha256(source_path)}`")
    if test_only:
        lines.extend(["", "This package uses synthetic fixture logs and must not be submitted."])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_submission(logs: str, out: str, *, test_only: bool = False) -> dict[str, object]:
    log_root = Path(logs).expanduser().resolve()
    out_path = Path(out).expanduser().resolve()
    readme_path = (REPO_ROOT / "README.md").resolve()
    if not readme_path.exists():
        raise SubmissionError("top-level README.md is required")

    plugin_entries = _collect_plugin_entries()
    log_entries = _collect_log_entries(log_root)
    if not any(relative != PurePosixPath("src/.codex-plugin/plugin.json") for _, relative in plugin_entries):
        raise SubmissionError("package requires at least one non-manifest plugin component")

    packaged_entries: list[tuple[PurePosixPath, bytes]] = []
    findings: list[ScanFinding] = []

    for source_path, relative_path in plugin_entries:
        data = _read_bytes(source_path)
        packaged_entries.append((relative_path, data))
        findings.extend(_scan_text_bytes(data, relative_path.as_posix(), edited_log_check=False))

    readme_data = _read_bytes(readme_path)
    packaged_entries.append((PurePosixPath("README.md"), readme_data))
    findings.extend(_scan_text_bytes(readme_data, "README.md", edited_log_check=False))

    for source_path, relative_path in log_entries:
        data = _read_bytes(source_path)
        packaged_entries.append((relative_path, data))
        findings.extend(_scan_text_bytes(data, relative_path.as_posix(), edited_log_check=True))

    if findings:
        raise SubmissionError(f"secret or edited-log scan failed: {_format_findings(findings)}")

    archive_paths = {relative.as_posix() for relative, _ in packaged_entries}
    if "src/.codex-plugin/plugin.json" not in archive_paths:
        raise SubmissionError("package requires src/.codex-plugin/plugin.json")
    if not any(path.startswith("logs/") for path in archive_paths):
        raise SubmissionError("package requires non-empty logs directory")

    _write_zip(packaged_entries, out_path)
    manifest_path = out_path.parent / "SHA256SUMS.txt"
    report_path = out_path.parent / "package-report.md"
    _write_sha_manifest(packaged_entries, out_path, manifest_path)
    _write_package_report(
        package_path=out_path,
        report_path=report_path,
        log_root=log_root,
        log_entries=log_entries,
        all_entries=packaged_entries,
        test_only=test_only,
    )
    return {
        "ok": True,
        "package_path": str(out_path),
        "sha256_manifest": str(manifest_path),
        "package_report": str(report_path),
        "test_only": test_only,
        "zip_sha256": file_sha256(out_path),
        "zip_size_bytes": out_path.stat().st_size,
        "log_count": len(log_entries),
    }


def _load_sha_manifest(manifest_path: Path) -> dict[str, str]:
    if not manifest_path.exists():
        raise SubmissionError(f"SHA256 manifest is missing: {manifest_path}")
    entries: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        digest, name = stripped.split("  ", 1)
        entries[name] = digest
    return entries


def _verify_archive_paths(names: list[str]) -> None:
    allowed_roots = {"src", "logs"}
    for name in names:
        pure_path = PurePosixPath(name)
        if pure_path.is_absolute():
            raise SubmissionError(f"archive path must not be absolute: {name}")
        if ".." in pure_path.parts:
            raise SubmissionError(f"archive path escapes package root: {name}")
        if _is_forbidden_path(pure_path):
            raise SubmissionError(f"forbidden path found in archive: {name}")
        if pure_path.parts[0] not in allowed_roots and name != "README.md":
            raise SubmissionError(f"unexpected top-level archive entry: {name}")


def _verify_required_entries(names: list[str]) -> None:
    if "README.md" not in names:
        raise SubmissionError("archive is missing top-level README.md")
    if "src/.codex-plugin/plugin.json" not in names:
        raise SubmissionError("archive is missing src/.codex-plugin/plugin.json")
    if not any(name.startswith("src/") and name != "src/.codex-plugin/plugin.json" for name in names):
        raise SubmissionError("archive requires at least one non-manifest plugin component")
    if not any(name.startswith("logs/") and not name.endswith("/") for name in names):
        raise SubmissionError("archive requires at least one log file")


def verify_submission(zip_path: str, *, allow_test_only: bool = False, max_package_bytes: int = MAX_PACKAGE_BYTES) -> dict[str, object]:
    archive_path = Path(zip_path).expanduser().resolve()
    if not archive_path.exists():
        raise SubmissionError(f"archive is missing: {archive_path}")
    if archive_path.stat().st_size > max_package_bytes:
        raise SubmissionError("package exceeds 100 MB limit")

    manifest_path = archive_path.parent / "SHA256SUMS.txt"
    report_path = archive_path.parent / "package-report.md"
    manifest = _load_sha_manifest(manifest_path)
    if not report_path.exists():
        raise SubmissionError(f"package report is missing: {report_path}")
    report_text = report_path.read_text(encoding="utf-8")
    if "- Secret scan: `PASS`" not in report_text:
        raise SubmissionError("package report does not record a PASS secret scan")
    is_test_only = "Package label: `TEST_ONLY`" in report_text
    if is_test_only and not allow_test_only:
        raise SubmissionError("TEST_ONLY package requires --allow-test-only")

    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        _verify_archive_paths(names)
        _verify_required_entries(names)

        findings: list[ScanFinding] = []
        for name in names:
            if name.endswith("/"):
                continue
            data = archive.read(name)
            if manifest.get(name) != bytes_sha256(data):
                raise SubmissionError(f"SHA-256 mismatch for archive entry: {name}")
            findings.extend(_scan_text_bytes(data, name, edited_log_check=name.startswith("logs/")))

    if manifest.get(archive_path.name) != file_sha256(archive_path):
        raise SubmissionError(f"SHA-256 mismatch for archive file: {archive_path.name}")
    if findings:
        raise SubmissionError(f"secret or edited-log scan failed: {_format_findings(findings)}")

    return {
        "ok": True,
        "archive_path": str(archive_path),
        "sha256_manifest": str(manifest_path),
        "package_report": str(report_path),
        "test_only": is_test_only,
        "zip_sha256": file_sha256(archive_path),
        "zip_size_bytes": archive_path.stat().st_size,
    }


def add_common_parser_flags(parser: argparse.ArgumentParser) -> None:
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
