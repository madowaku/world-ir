"""World IR v0.1 reference compiler, comparison, and evaluation API."""

from .canonical import canonical_bytes, canonical_json, canonicalize, e0_equivalent
from .compiler import compile_utterance, semantic_core, validate_document
from .evaluation import (
    SuiteIntegrityError,
    evaluate_case,
    evaluate_seed_suite,
    format_text_report,
    load_seed_suite,
)

__all__ = [
    "SuiteIntegrityError",
    "canonical_bytes",
    "canonical_json",
    "canonicalize",
    "compile_utterance",
    "e0_equivalent",
    "evaluate_case",
    "evaluate_seed_suite",
    "format_text_report",
    "load_seed_suite",
    "semantic_core",
    "validate_document",
]
