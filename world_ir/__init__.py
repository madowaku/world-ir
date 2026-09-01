"""World IR v0.1 reference compiler and canonical comparison API."""

from .canonical import canonical_bytes, canonical_json, canonicalize, e0_equivalent
from .compiler import compile_utterance, semantic_core, validate_document

__all__ = [
    "canonical_bytes",
    "canonical_json",
    "canonicalize",
    "compile_utterance",
    "e0_equivalent",
    "semantic_core",
    "validate_document",
]
