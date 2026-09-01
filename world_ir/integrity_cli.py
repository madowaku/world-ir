from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .integrity import check_repository_integrity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="world-ir-integrity",
        description="Validate World IR repository schema, examples, and seed-suite integrity.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root (default: current directory).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = check_repository_integrity(Path(args.root))
    if report.ok:
        print(report.summary())
        return 0

    for error in report.errors:
        print(f"ERROR {error}", file=sys.stderr)
    print(report.summary(), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
