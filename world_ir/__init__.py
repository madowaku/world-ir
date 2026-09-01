"""World IR v0.1 reference compiler, comparison, evaluation, and integrity API."""

from .canonical import canonical_bytes, canonical_json, canonicalize, e0_equivalent
from .compiler import compile_utterance, semantic_core, validate_document
from .evaluation import (
    SuiteIntegrityError,
    evaluate_case,
    evaluate_seed_suite,
    format_text_report,
    load_seed_suite,
)
from .integrity import IntegrityReport, check_repository_integrity

__all__ = [
    "IntegrityReport",
    "SuiteIntegrityError",
    "canonical_bytes",
    "canonical_json",
    "canonicalize",
    "check_repository_integrity",
    "compile_utterance",
    "e0_equivalent",
    "evaluate_case",
    "evaluate_seed_suite",
    "format_text_report",
    "load_seed_suite",
    "semantic_core",
    "validate_document",
]
