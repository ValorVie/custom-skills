#!/usr/bin/env python3
"""驗證選用檢查器的固定介面與測試資料，不評估 AI 或 ASD 符合性。"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


EVALS_DIR = Path(__file__).resolve().parent
FILES_DIR = EVALS_DIR / "files"
STANDARD_PDF = FILES_DIR / "synthetic-standard.pdf"
VALID_CHECKER = FILES_DIR / "fake_asd_checker.py"
INVALID_CHECKER = FILES_DIR / "fake_asd_checker_invalid.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def marker_for(document: Path) -> Path:
    return Path(f"{document}.checker-invoked")


def run_checker(
    document: Path,
    standard_pdf: Path | None,
    checker: Path | None,
) -> tuple[str, dict[str, object] | None, list[str] | None]:
    if standard_pdf is None or checker is None:
        return "not-checked", None, None

    paths_are_valid = (
        document.is_absolute()
        and document.is_file()
        and standard_pdf.is_absolute()
        and standard_pdf.is_file()
        and checker.is_absolute()
        and checker.is_file()
        and os.access(checker, os.X_OK)
    )
    if not paths_are_valid:
        return "tool-failure", None, None

    arguments = [
        str(checker),
        "check",
        "--document",
        str(document),
        "--standard-pdf",
        str(standard_pdf),
        "--format",
        "json",
    ]
    result = subprocess.run(
        arguments,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        return "tool-failure", None, arguments

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return "tool-failure", None, arguments

    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 1
        or payload.get("status") != "checked"
        or not isinstance(payload.get("findings"), list)
    ):
        return "tool-failure", None, arguments

    findings = payload["findings"]
    for finding in findings:
        if (
            not isinstance(finding, dict)
            or type(finding.get("line")) is not int
            or finding["line"] < 1
            or not isinstance(finding.get("category"), str)
            or not finding["category"].strip()
            or not isinstance(finding.get("message"), str)
            or not finding["message"].strip()
        ):
            return "tool-failure", None, arguments

    status = "checked-with-findings" if findings else "checked-no-findings"
    return status, payload, arguments


def write_document(root: Path, name: str, content: str = "synthetic document\n") -> Path:
    case_dir = root / name
    case_dir.mkdir()
    document = case_dir / "document with spaces;not-run.md"
    document.write_text(content, encoding="utf-8")
    return document


def main() -> int:
    evals = json.loads((EVALS_DIR / "evals.json").read_text(encoding="utf-8"))
    require([case["id"] for case in evals["evals"]] == list(range(1, 10)), "eval ids")
    require(STANDARD_PDF.is_file(), "missing synthetic PDF")
    require(os.access(VALID_CHECKER, os.X_OK), "valid checker is not executable")
    require(os.access(INVALID_CHECKER, os.X_OK), "invalid checker is not executable")

    with tempfile.TemporaryDirectory(prefix="optional-asd-checker-") as temporary:
        root = Path(temporary)

        for name, pdf, checker in (
            ("no-tools", None, None),
            ("pdf-only", STANDARD_PDF, None),
            ("checker-only", None, VALID_CHECKER),
        ):
            document = write_document(root, name)
            status, _, _ = run_checker(document, pdf, checker)
            require(status == "not-checked", f"{name} status")
            require(not marker_for(document).exists(), f"{name} invoked checker")

        invalid_path_document = write_document(root, "invalid-path")
        status, _, _ = run_checker(
            invalid_path_document,
            root / "missing-standard.pdf",
            VALID_CHECKER,
        )
        require(status == "tool-failure", "invalid path status")
        require(not marker_for(invalid_path_document).exists(), "invalid path invoked checker")

        findings_document = write_document(root, "with-findings")
        status, payload, arguments = run_checker(
            findings_document,
            STANDARD_PDF,
            VALID_CHECKER,
        )
        require(status == "checked-with-findings", "finding status")
        require(payload is not None and payload["findings"][0]["line"] == 1, "finding line")
        marker = json.loads(marker_for(findings_document).read_text(encoding="utf-8"))
        require(marker["argv"] == arguments[1:], "checker argv")

        clean_document = write_document(
            root,
            "no-findings",
            "ASD_FIXTURE_NO_FINDINGS\n",
        )
        status, payload, _ = run_checker(clean_document, STANDARD_PDF, VALID_CHECKER)
        require(status == "checked-no-findings", "no findings status")
        require(payload is not None and payload["findings"] == [], "no findings payload")

        missing_line_document = write_document(
            root,
            "missing-line",
            "ASD_FIXTURE_MISSING_LINE\n",
        )
        status, _, _ = run_checker(
            missing_line_document,
            STANDARD_PDF,
            VALID_CHECKER,
        )
        require(status == "tool-failure", "missing line status")
        require(marker_for(missing_line_document).is_file(), "missing line checker was not called")

        for name, fixture in (
            ("missing-category", "ASD_FIXTURE_MISSING_CATEGORY\n"),
            ("missing-message", "ASD_FIXTURE_MISSING_MESSAGE\n"),
        ):
            document = write_document(root, name, fixture)
            status, _, _ = run_checker(document, STANDARD_PDF, VALID_CHECKER)
            require(status == "tool-failure", f"{name} status")
            require(marker_for(document).is_file(), f"{name} checker was not called")

        invalid_json_document = write_document(root, "invalid-json")
        status, _, _ = run_checker(
            invalid_json_document,
            STANDARD_PDF,
            INVALID_CHECKER,
        )
        require(status == "tool-failure", "invalid JSON status")
        require(marker_for(invalid_json_document).is_file(), "invalid checker was not called")

        nonzero_document = write_document(
            root,
            "nonzero-exit",
            "ASD_FIXTURE_NONZERO\n",
        )
        status, _, _ = run_checker(nonzero_document, STANDARD_PDF, INVALID_CHECKER)
        require(status == "tool-failure", "nonzero exit status")
        require(marker_for(nonzero_document).is_file(), "nonzero checker was not called")

    print("PASS optional checker interface fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
