from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

EXPECTED_CASE_IDS = [f"WIR-EQ-{index:03d}" for index in range(1, 101)]
EXPECTED_LANGUAGES = {"ja", "en", "zh-Hans"}
EXPECTED_LEVELS = {"E1", "E2", "unsupported"}
EXPECTED_PART_COUNT = 10
EXPECTED_CASES_PER_PART = 10


@dataclass(frozen=True)
class IntegrityReport:
    errors: tuple[str, ...]
    example_count: int = 0
    part_count: int = 0
    case_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if self.ok:
            return (
                "repository integrity: OK "
                f"(schema=1 examples={self.example_count} "
                f"parts={self.part_count} cases={self.case_count})"
            )
        return f"repository integrity: FAIL ({len(self.errors)} error(s))"


def _load_json(path: Path, root: Path, errors: list[str]) -> Any | None:
    label = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    if not path.is_file():
        errors.append(f"{label}: missing file")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        if isinstance(exc, json.JSONDecodeError):
            detail = f"invalid JSON at line {exc.lineno}, column {exc.colno}"
        else:
            detail = "not valid UTF-8"
        errors.append(f"{label}: {detail}")
        return None


def _validate_schema(root: Path, errors: list[str]) -> dict[str, Any] | None:
    path = root / "schema" / "world-ir-v0.1.schema.json"
    schema = _load_json(path, root, errors)
    if schema is None:
        return None
    if not isinstance(schema, dict):
        errors.append("schema/world-ir-v0.1.schema.json: schema root must be an object")
        return None
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # jsonschema exposes multiple schema-error subclasses.
        errors.append(
            "schema/world-ir-v0.1.schema.json: invalid Draft 2020-12 schema: "
            f"{exc.message if hasattr(exc, 'message') else str(exc)}"
        )
        return None
    return schema


def _validate_examples(
    root: Path, schema: dict[str, Any] | None, errors: list[str]
) -> int:
    examples_dir = root / "examples"
    if not examples_dir.is_dir():
        errors.append("examples: missing directory")
        return 0

    files = sorted(path for path in examples_dir.rglob("*.json") if path.is_file())
    if not files:
        errors.append("examples: no JSON examples found")
        return 0

    validator = Draft202012Validator(schema) if schema is not None else None
    for path in files:
        document = _load_json(path, root, errors)
        if document is None or validator is None:
            continue
        validation_errors = sorted(validator.iter_errors(document), key=lambda err: list(err.path))
        if validation_errors:
            first = validation_errors[0]
            location = ".".join(str(part) for part in first.path) or "<root>"
            errors.append(
                f"{path.relative_to(root).as_posix()}: schema validation failed at "
                f"{location}: {first.message}"
            )
    return len(files)


def _validate_manifest_structure(manifest: Any, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(manifest, dict):
        errors.append("tests/equivalence-100.json: manifest root must be an object")
        return []

    if manifest.get("count") != 100:
        errors.append(
            "tests/equivalence-100.json: count must be 100 "
            f"(got {manifest.get('count')!r})"
        )

    parts = manifest.get("parts")
    if not isinstance(parts, list):
        errors.append("tests/equivalence-100.json: parts must be an array")
        return []
    if len(parts) != EXPECTED_PART_COUNT:
        errors.append(
            "tests/equivalence-100.json: expected 10 parts "
            f"(got {len(parts)})"
        )

    normalized: list[dict[str, Any]] = []
    seen_files: set[str] = set()
    for index, part in enumerate(parts, 1):
        if not isinstance(part, dict):
            errors.append(f"tests/equivalence-100.json: part {index} must be an object")
            continue
        filename = part.get("file")
        if not isinstance(filename, str) or not filename:
            errors.append(f"tests/equivalence-100.json: part {index} has invalid file")
            continue
        if filename in seen_files:
            errors.append(f"tests/equivalence-100.json: duplicate part file {filename}")
        seen_files.add(filename)
        if part.get("count") != EXPECTED_CASES_PER_PART:
            errors.append(
                f"tests/equivalence-100.json: {filename} count must be 10 "
                f"(got {part.get('count')!r})"
            )
        normalized.append(part)
    return normalized


def _validate_case(case: Any, source: str, errors: list[str]) -> str | None:
    if not isinstance(case, dict):
        errors.append(f"{source}: case must be an object")
        return None

    case_id = case.get("id")
    if not isinstance(case_id, str):
        errors.append(f"{source}: case id must be a string")
        return None

    level = case.get("expected_level")
    if level not in EXPECTED_LEVELS:
        errors.append(
            f"{source}: {case_id} expected_level must be one of "
            f"{sorted(EXPECTED_LEVELS)} (got {level!r})"
        )

    inputs = case.get("inputs")
    if not isinstance(inputs, list):
        errors.append(f"{source}: {case_id} inputs must be an array")
        return case_id

    languages: list[str] = []
    for item in inputs:
        if not isinstance(item, dict):
            errors.append(f"{source}: {case_id} input must be an object")
            continue
        language = item.get("language")
        text = item.get("text")
        if isinstance(language, str):
            languages.append(language)
        if not isinstance(text, str) or not text:
            errors.append(f"{source}: {case_id} input text must be a non-empty string")

    language_set = set(languages)
    if language_set != EXPECTED_LANGUAGES or len(languages) != len(EXPECTED_LANGUAGES):
        errors.append(
            f"{source}: {case_id} languages must be exactly "
            f"{sorted(EXPECTED_LANGUAGES)} (got {languages!r})"
        )
    return case_id


def _validate_seed_suite(root: Path, errors: list[str]) -> tuple[int, int]:
    manifest_path = root / "tests" / "equivalence-100.json"
    manifest = _load_json(manifest_path, root, errors)
    if manifest is None:
        return 0, 0

    parts = _validate_manifest_structure(manifest, errors)
    all_ids: list[str] = []
    loaded_parts = 0

    for part in parts:
        filename = part["file"]
        path = root / "tests" / filename
        payload = _load_json(path, root, errors)
        if payload is None:
            continue
        loaded_parts += 1
        if not isinstance(payload, list):
            errors.append(f"tests/{filename}: case file root must be an array")
            continue
        if len(payload) != EXPECTED_CASES_PER_PART:
            errors.append(
                f"tests/{filename}: expected 10 cases (got {len(payload)})"
            )

        part_ids: list[str] = []
        for case in payload:
            case_id = _validate_case(case, f"tests/{filename}", errors)
            if case_id is not None:
                all_ids.append(case_id)
                part_ids.append(case_id)

        if part_ids:
            expected_first = part.get("first_id")
            expected_last = part.get("last_id")
            if part_ids[0] != expected_first:
                errors.append(
                    f"tests/{filename}: first id must match manifest "
                    f"{expected_first!r} (got {part_ids[0]!r})"
                )
            if part_ids[-1] != expected_last:
                errors.append(
                    f"tests/{filename}: last id must match manifest "
                    f"{expected_last!r} (got {part_ids[-1]!r})"
                )

    duplicates = sorted({case_id for case_id in all_ids if all_ids.count(case_id) > 1})
    if duplicates:
        preview = ", ".join(duplicates[:5])
        errors.append(f"tests: duplicate case id(s): {preview}")

    if all_ids != EXPECTED_CASE_IDS:
        missing = [case_id for case_id in EXPECTED_CASE_IDS if case_id not in all_ids]
        unexpected = [case_id for case_id in all_ids if case_id not in EXPECTED_CASE_IDS]
        if missing:
            errors.append(f"tests: missing case id(s): {', '.join(missing[:5])}")
        if unexpected:
            errors.append(f"tests: unexpected case id(s): {', '.join(unexpected[:5])}")
        if not missing and not unexpected:
            errors.append("tests: case ids are not in exact WIR-EQ-001..WIR-EQ-100 order")

    return loaded_parts, len(all_ids)


def check_repository_integrity(root: Path | str) -> IntegrityReport:
    """Validate repository data assets without invoking the compiler or evaluator."""
    root_path = Path(root).resolve()
    errors: list[str] = []
    schema = _validate_schema(root_path, errors)
    example_count = _validate_examples(root_path, schema, errors)
    part_count, case_count = _validate_seed_suite(root_path, errors)
    return IntegrityReport(
        errors=tuple(errors),
        example_count=example_count,
        part_count=part_count,
        case_count=case_count,
    )
