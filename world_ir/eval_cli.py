from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluation import SuiteIntegrityError, evaluate_seed_suite, format_text_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="world-ir-eval",
        description="Evaluate the World IR v0.1 100-case seed suite.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to a seed-suite manifest (defaults to tests/equivalence-100.json).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the complete machine-readable report as JSON.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Include non-passing per-case diagnostics in text output.",
    )
    parser.add_argument(
        "--fail-on-false-equivalence",
        action="store_true",
        help="Exit with status 1 when any false-equivalence case is detected.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = evaluate_seed_suite(manifest_path=args.manifest)
    except (SuiteIntegrityError, OSError, json.JSONDecodeError) as exc:
        print(f"world-ir-eval: suite error: {exc}")
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(format_text_report(report, details=args.details))

    if args.fail_on_false_equivalence and report["summary"]["false_equivalence"]["count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
