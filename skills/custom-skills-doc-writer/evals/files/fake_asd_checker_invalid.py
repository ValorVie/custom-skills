#!/usr/bin/env python3
"""Test fixture that returns malformed checker output."""

from __future__ import annotations

import argparse
from pathlib import Path


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

    marker = Path(f"{args.document}.checker-invoked")
    marker.write_text("invalid checker invoked\n", encoding="utf-8")
    print("this is not json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
