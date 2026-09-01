from __future__ import annotations

import argparse
import json
import sys

from .compiler import (
    SUPPORTED_LANGUAGES,
    WorldIRCompilerError,
    compile_utterance,
    validate_document,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="world-ir",
        description="Minimal World IR v0.1 reference compiler.",
    )
    parser.add_argument("text", help="Source utterance to compile.")
    parser.add_argument(
        "--lang",
        required=True,
        choices=sorted(SUPPORTED_LANGUAGES),
        help="BCP 47 source language tag.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip JSON Schema validation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document = compile_utterance(args.text, args.lang)
        if not args.no_validate:
            validate_document(document)
    except (WorldIRCompilerError, RuntimeError) as exc:
        print(f"world-ir: {exc}", file=sys.stderr)
        return 2

    json.dump(document, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
