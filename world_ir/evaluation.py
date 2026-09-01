from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable

from .canonical import canonicalize
from .compiler import (
    UnsupportedLanguageError,
    UnsupportedUtteranceError,
    compile_utterance,
    validate_document,
)

EXPECTED_LANGUAGES = ("ja", "en", "zh-Hans")
EXPECTED_LEVELS = frozenset({"E1", "E2", "unsupported"})


class SuiteIntegrityError(ValueError):
    """Raised when the seed-suite manifest or case files are malformed."""


def repository_manifest_path() -> Path:
    return Path(__file__).resolve().parent.parent / "tests" / "equivalence-100.json"


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_seed_suite(manifest_path: Path | None = None) -> list[dict[str, Any]]:
    """Load and validate the split 100-case seed suite."""
    path = Path(manifest_path) if manifest_path is not None else repository_manifest_path()
    manifest = json.loads(path.read_text(encoding="utf-8"))

    declared_count = manifest.get("count")
    parts = manifest.get("parts")
    if not isinstance(declared_count, int) or declared_count <= 0:
        raise SuiteIntegrityError("manifest.count must be a positive integer")
    if not isinstance(parts, list) or not parts:
        raise SuiteIntegrityError("manifest.parts must be a non-empty list")

    cases: list[dict[str, Any]] = []
    for part in parts:
        if not isinstance(part, dict) or not isinstance(part.get("file"), str):
            raise SuiteIntegrityError("every manifest part must name a file")
        part_path = path.parent / part["file"]
        if not part_path.is_file():
            raise SuiteIntegrityError(f"missing case file: {part['file']}")
        loaded = json.loads(part_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise SuiteIntegrityError(f"case file is not a list: {part['file']}")
        if part.get("count") != len(loaded):
            raise SuiteIntegrityError(
                f"manifest count mismatch for {part['file']}: "
                f"expected {part.get('count')}, got {len(loaded)}"
            )
        if loaded:
            if part.get("first_id") != loaded[0].get("id"):
                raise SuiteIntegrityError(f"first_id mismatch for {part['file']}")
            if part.get("last_id") != loaded[-1].get("id"):
                raise SuiteIntegrityError(f"last_id mismatch for {part['file']}")
        cases.extend(loaded)

    if len(cases) != declared_count:
        raise SuiteIntegrityError(
            f"suite count mismatch: manifest declares {declared_count}, loaded {len(cases)}"
        )

    ids = [case.get("id") for case in cases]
    if len(set(ids)) != len(ids):
        raise SuiteIntegrityError("duplicate case IDs detected")
    expected_ids = [f"WIR-EQ-{index:03d}" for index in range(1, declared_count + 1)]
    if ids != expected_ids:
        raise SuiteIntegrityError("case IDs must be contiguous and ordered from WIR-EQ-001")

    for case in cases:
        case_id = case["id"]
        level = case.get("expected_level")
        if level not in EXPECTED_LEVELS:
            raise SuiteIntegrityError(f"{case_id}: invalid expected_level {level!r}")
        inputs = case.get("inputs")
        if not isinstance(inputs, list) or len(inputs) != len(EXPECTED_LANGUAGES):
            raise SuiteIntegrityError(f"{case_id}: expected exactly three language inputs")
        languages = tuple(item.get("language") for item in inputs)
        if languages != EXPECTED_LANGUAGES:
            raise SuiteIntegrityError(
                f"{case_id}: languages must be ordered as {EXPECTED_LANGUAGES}, got {languages}"
            )
        for item in inputs:
            if not isinstance(item.get("text"), str) or not item["text"]:
                raise SuiteIntegrityError(f"{case_id}: every input needs non-empty text")

    return cases


def _semantic_content(document: dict[str, Any]) -> dict[str, Any]:
    """Return canonical meaning without fidelity bookkeeping.

    E2 compares the shared proposition separately from explicit loss reporting,
    so fidelity is intentionally removed from this projection.
    """
    canonical = canonicalize(document)
    canonical.pop("fidelity", None)
    return canonical


def _has_loss(document: dict[str, Any]) -> bool:
    fidelity = document.get("fidelity", {})
    return (
        fidelity.get("status") in {"lossy", "unknown"}
        or bool(fidelity.get("lost_features"))
    )


def _loss_features(document: dict[str, Any]) -> list[str]:
    fidelity = document.get("fidelity", {})
    return sorted(set(fidelity.get("lost_features", [])))


def evaluate_case(
    case: dict[str, Any],
    *,
    compiler: Callable[[str, str], dict[str, Any]] = compile_utterance,
) -> dict[str, Any]:
    """Evaluate one tri-lingual case and return serializable diagnostics."""
    attempts: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    for item in case["inputs"]:
        language = item["language"]
        text = item["text"]
        attempt: dict[str, Any] = {"language": language, "text": text}
        try:
            document = compiler(text, language)
        except (UnsupportedUtteranceError, UnsupportedLanguageError) as exc:
            attempt.update({"status": "unsupported", "error": str(exc)})
        except Exception as exc:  # evaluator must surface unexpected compiler failures
            attempt.update(
                {
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        else:
            try:
                validate_document(document)
            except Exception as exc:
                attempt.update(
                    {
                        "status": "invalid",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            else:
                attempt["status"] = "compiled"
                documents.append(document)
        attempts.append(attempt)

    statuses = [attempt["status"] for attempt in attempts]
    all_compiled = all(status == "compiled" for status in statuses)
    all_unsupported = all(status == "unsupported" for status in statuses)

    semantic_equivalent: bool | None = None
    e0_equivalent: bool | None = None
    loss_detected = False
    loss_features: list[str] = []

    if all_compiled:
        semantic_forms = [_stable(_semantic_content(document)) for document in documents]
        full_forms = [_stable(canonicalize(document)) for document in documents]
        semantic_equivalent = len(set(semantic_forms)) == 1
        e0_equivalent = len(set(full_forms)) == 1
        loss_detected = any(_has_loss(document) for document in documents)
        loss_features = sorted(
            {feature for document in documents for feature in _loss_features(document)}
        )

    expected = case["expected_level"]
    false_equivalence = False

    if any(status == "error" for status in statuses):
        outcome = "compiler_error"
    elif any(status == "invalid" for status in statuses):
        outcome = "invalid_output"
    elif expected == "E1":
        if all_compiled and semantic_equivalent and e0_equivalent and not loss_detected:
            outcome = "pass_e1"
        elif all_unsupported:
            outcome = "not_covered"
        elif not all_compiled:
            outcome = "partial_support"
        elif loss_detected:
            outcome = "unexpected_loss"
        else:
            outcome = "semantic_mismatch"
    elif expected == "E2":
        if all_unsupported:
            outcome = "not_covered"
        elif not all_compiled:
            outcome = "partial_support"
        elif semantic_equivalent and loss_detected:
            outcome = "pass_e2"
        elif semantic_equivalent and not loss_detected:
            outcome = "false_equivalence"
            false_equivalence = True
        else:
            outcome = "semantic_mismatch"
    else:  # unsupported
        if all_unsupported:
            outcome = "pass_unsupported"
        elif all_compiled and semantic_equivalent:
            outcome = "false_equivalence"
            false_equivalence = True
        else:
            outcome = "unsupported_violation"

    return {
        "id": case["id"],
        "category": case["category"],
        "expected_level": expected,
        "outcome": outcome,
        "false_equivalence": false_equivalence,
        "all_compiled": all_compiled,
        "all_unsupported": all_unsupported,
        "semantic_equivalent": semantic_equivalent,
        "e0_equivalent": e0_equivalent,
        "loss_detected": loss_detected,
        "loss_features": loss_features,
        "attempts": attempts,
        "target_semantics": case.get("target_semantics", ""),
        "notes": case.get("notes", ""),
    }


def _summarize(case_reports: list[dict[str, Any]]) -> dict[str, Any]:
    expected_counts = {
        level: sum(report["expected_level"] == level for report in case_reports)
        for level in ("E1", "E2", "unsupported")
    }
    outcome_counts: dict[str, int] = {}
    for report in case_reports:
        outcome_counts[report["outcome"]] = outcome_counts.get(report["outcome"], 0) + 1

    attempts = [attempt for report in case_reports for attempt in report["attempts"]]
    emitted = sum(attempt["status"] in {"compiled", "invalid"} for attempt in attempts)
    valid = sum(attempt["status"] == "compiled" for attempt in attempts)
    all_compiled = sum(report["all_compiled"] for report in case_reports)

    e1_reports = [r for r in case_reports if r["expected_level"] == "E1"]
    e2_reports = [r for r in case_reports if r["expected_level"] == "E2"]
    unsupported_reports = [r for r in case_reports if r["expected_level"] == "unsupported"]

    e1_pass = sum(r["outcome"] == "pass_e1" for r in e1_reports)
    e1_covered = sum(r["all_compiled"] for r in e1_reports)
    e2_pass = sum(r["outcome"] == "pass_e2" for r in e2_reports)
    e2_covered = sum(r["all_compiled"] for r in e2_reports)
    unsupported_pass = sum(r["outcome"] == "pass_unsupported" for r in unsupported_reports)

    loss_predictions = [
        r
        for r in case_reports
        if r["expected_level"] in {"E1", "E2"}
        and r["all_compiled"]
        and r["loss_detected"]
    ]
    loss_true_positive = sum(r["expected_level"] == "E2" for r in loss_predictions)
    loss_false_positive = sum(r["expected_level"] == "E1" for r in loss_predictions)

    false_equivalence_reports = [r for r in case_reports if r["false_equivalence"]]
    false_equivalence_denominator = expected_counts["E2"] + expected_counts["unsupported"]

    return {
        "case_count": len(case_reports),
        "attempt_count": len(attempts),
        "expected_counts": expected_counts,
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "coverage": {
            "fully_compiled_cases": all_compiled,
            "fully_compiled_rate": _ratio(all_compiled, len(case_reports)),
            "compiled_outputs": valid,
            "emitted_outputs": emitted,
        },
        "schema_valid_rate": _ratio(valid, emitted),
        "e1": {
            "passed": e1_pass,
            "total": expected_counts["E1"],
            "fully_compiled": e1_covered,
            "strict_match_rate": _ratio(e1_pass, expected_counts["E1"]),
            "covered_match_rate": _ratio(e1_pass, e1_covered),
        },
        "e2_loss_detection": {
            "true_positive": loss_true_positive,
            "false_positive": loss_false_positive,
            "total_e2": expected_counts["E2"],
            "fully_compiled_e2": e2_covered,
            "precision": _ratio(loss_true_positive, loss_true_positive + loss_false_positive),
            "strict_recall": _ratio(loss_true_positive, expected_counts["E2"]),
            "covered_recall": _ratio(loss_true_positive, e2_covered),
            "passed": e2_pass,
        },
        "unsupported": {
            "passed_abstentions": unsupported_pass,
            "total": expected_counts["unsupported"],
            "abstention_rate": _ratio(unsupported_pass, expected_counts["unsupported"]),
        },
        "false_equivalence": {
            "count": len(false_equivalence_reports),
            "rate": _ratio(len(false_equivalence_reports), false_equivalence_denominator),
            "case_ids": [r["id"] for r in false_equivalence_reports],
        },
    }


def evaluate_seed_suite(
    *,
    compiler: Callable[[str, str], dict[str, Any]] = compile_utterance,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate all seed cases with one compiler implementation."""
    cases = load_seed_suite(manifest_path)
    case_reports = [evaluate_case(case, compiler=compiler) for case in cases]
    return {
        "suite": "World IR v0.1 seed equivalence suite",
        "summary": _summarize(case_reports),
        "cases": case_reports,
    }


def format_text_report(report: dict[str, Any], *, details: bool = False) -> str:
    """Render a compact human-readable evaluation report."""
    summary = report["summary"]

    def pct(value: float | None) -> str:
        return "n/a" if value is None else f"{value * 100:.1f}%"

    lines = [
        report["suite"],
        f"cases: {summary['case_count']} | attempts: {summary['attempt_count']}",
        (
            "coverage: "
            f"{summary['coverage']['fully_compiled_cases']}/{summary['case_count']} "
            f"({pct(summary['coverage']['fully_compiled_rate'])})"
        ),
        f"schema-valid emitted output: {pct(summary['schema_valid_rate'])}",
        (
            "E1: "
            f"{summary['e1']['passed']}/{summary['e1']['total']} strict "
            f"({pct(summary['e1']['strict_match_rate'])}); "
            f"covered={pct(summary['e1']['covered_match_rate'])}"
        ),
        (
            "E2 loss detection: "
            f"precision={pct(summary['e2_loss_detection']['precision'])}, "
            f"strict recall={pct(summary['e2_loss_detection']['strict_recall'])}, "
            f"covered recall={pct(summary['e2_loss_detection']['covered_recall'])}"
        ),
        (
            "unsupported abstention: "
            f"{summary['unsupported']['passed_abstentions']}/"
            f"{summary['unsupported']['total']} "
            f"({pct(summary['unsupported']['abstention_rate'])})"
        ),
        (
            "false equivalence: "
            f"{summary['false_equivalence']['count']} "
            f"({pct(summary['false_equivalence']['rate'])})"
        ),
    ]

    if details:
        lines.append("")
        lines.append("case diagnostics:")
        for case in report["cases"]:
            if case["outcome"] not in {"pass_e1", "pass_e2", "pass_unsupported"}:
                statuses = ", ".join(
                    f"{attempt['language']}={attempt['status']}" for attempt in case["attempts"]
                )
                lines.append(
                    f"- {case['id']} [{case['expected_level']}] "
                    f"{case['outcome']}: {statuses}"
                )
    return "\n".join(lines)
