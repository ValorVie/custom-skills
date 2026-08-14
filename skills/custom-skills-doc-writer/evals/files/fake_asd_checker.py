#!/usr/bin/env python3
"""Test fixture for the optional ASD checker interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--document", type=Path, required=True)
    check.add_argument("--standard-pdf", type=Path, required=True)
    check.add_argument("--format", choices=("json",), required=True)
    args = parser.parse_args()

    if not args.document.is_absolute() or not args.document.is_file():
        parser.error("--document must be an existing absolute file")
    if not args.standard_pdf.is_absolute() or not args.standard_pdf.is_file():
        parser.error("--standard-pdf must be an existing absolute file")

    document_text = args.document.read_text(encoding="utf-8")
    no_findings = "ASD_FIXTURE_NO_FINDINGS" in document_text
    missing_line = "ASD_FIXTURE_MISSING_LINE" in document_text
    missing_category = "ASD_FIXTURE_MISSING_CATEGORY" in document_text
    missing_message = "ASD_FIXTURE_MISSING_MESSAGE" in document_text
    marker = Path(f"{args.document}.checker-invoked")
    marker.write_text(json.dumps({"argv": sys.argv[1:]}) + "\n", encoding="utf-8")
    findings = [] if no_findings else [{
        "line": 1,
        "category": "synthetic-test-finding",
        "message": "Review the editable English prose.",
    }]
    if missing_line:
        del findings[0]["line"]
    if missing_category:
        del findings[0]["category"]
    if missing_message:
        del findings[0]["message"]
    print(json.dumps({"schema_version": 1, "status": "checked", "findings": findings}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
