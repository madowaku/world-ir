from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import re
from typing import Any

SUPPORTED_LANGUAGES = frozenset({"ja", "en", "zh-Hans"})
COMPILER_NAME = "world-ir-reference"
COMPILER_VERSION = "0.1.0"


class WorldIRCompilerError(ValueError):
    """Base error for the reference compiler."""


class UnsupportedLanguageError(WorldIRCompilerError):
    """Raised when the requested language is outside the v0.1 compiler scope."""


class UnsupportedUtteranceError(WorldIRCompilerError):
    """Raised when the seed compiler cannot compile without guessing."""


def _normalize_for_match(text: str, language: str) -> str:
    candidate = text.strip()
    if language == "en":
        candidate = candidate.casefold()
    # Match punctuation-insensitively while preserving source.text exactly.
    candidate = re.sub(r"[。.!！]+$", "", candidate).strip()
    return candidate


_SEED_RULES = {
    ("ja", _normalize_for_match("犬が走った。", "ja")),
    ("en", _normalize_for_match("The dog ran.", "en")),
    ("zh-Hans", _normalize_for_match("狗跑了。", "zh-Hans")),
}


def _dog_ran_document(text: str, language: str) -> dict[str, Any]:
    safe_language = re.sub(r"[^A-Za-z0-9]+", "-", language).strip("-").lower()
    return {
        "world_ir_version": "0.1.0",
        "id": f"reference-dog-ran-{safe_language}",
        "source": {"text": text, "language": language, "channel": "text"},
        "utterance": {"kind": "assertion"},
        "entities": [
            {
                "id": "e1",
                "type": "animal",
                "concept": "DOG",
                "quantifier": {"kind": "definite"},
            }
        ],
        "frames": [
            {
                "id": "f1",
                "frame_type": "event",
                "predicate": "RUN",
                "roles": [{"role": "AGENT", "value": {"entity_ref": "e1"}}],
                "polarity": "positive",
                "tense": "past",
                "aspect": "simple",
                "modality": "asserted",
                "certainty": 1.0,
            }
        ],
        "links": [],
        "fidelity": {"status": "lossless", "lost_features": [], "notes": []},
        "extensions": {
            "compiler": {
                "name": COMPILER_NAME,
                "version": COMPILER_VERSION,
                "strategy": "seed-rule",
            }
        },
    }


def compile_utterance(text: str, language: str) -> dict[str, Any]:
    """Compile one supported utterance to World IR v0.1.

    v0.1 intentionally supports only the three dog-ran seed utterances.
    Unknown text is rejected instead of being assigned guessed semantics.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise UnsupportedLanguageError(
            f"Unsupported language {language!r}; expected one of "
            f"{', '.join(sorted(SUPPORTED_LANGUAGES))}."
        )
    if not isinstance(text, str) or not text.strip():
        raise UnsupportedUtteranceError("Input text must be a non-empty string.")

    key = (language, _normalize_for_match(text, language))
    if key not in _SEED_RULES:
        raise UnsupportedUtteranceError(
            "The v0.1 reference compiler does not know this utterance. "
            "Refusing to guess semantics."
        )

    return _dog_ran_document(text=text, language=language)


def semantic_core(document: dict[str, Any]) -> dict[str, Any]:
    """Return the comparison-relevant core for the Issue #1 smoke test."""
    return {
        "utterance": deepcopy(document["utterance"]),
        "entities": deepcopy(document["entities"]),
        "frames": deepcopy(document["frames"]),
        "links": deepcopy(document["links"]),
        "fidelity": deepcopy(document["fidelity"]),
    }


def repository_schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "schema" / "world-ir-v0.1.schema.json"


def validate_document(document: dict[str, Any], schema_path: Path | None = None) -> None:
    """Validate a compiled document against the repository's v0.1 schema."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError(
            "jsonschema is required for validation. Install the project dependencies."
        ) from exc

    path = schema_path or repository_schema_path()
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)
