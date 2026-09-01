from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from world_ir.compiler import UnsupportedUtteranceError, compile_utterance
from world_ir.evaluation import (
    SuiteIntegrityError,
    evaluate_case,
    evaluate_seed_suite,
    format_text_report,
    load_seed_suite,
)


class EvaluationHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_seed_suite()
        cls.by_id = {case["id"]: case for case in cls.cases}

    def _fake_document(
        self,
        text: str,
        language: str,
        *,
        fidelity_status: str = "lossless",
        lost_features: list[str] | None = None,
    ) -> dict:
        document = deepcopy(compile_utterance("The dog ran.", "en"))
        document["id"] = f"fake-{language}"
        document["source"] = {"text": text, "language": language, "channel": "text"}
        document["fidelity"] = {
            "status": fidelity_status,
            "lost_features": list(lost_features or []),
            "notes": [],
        }
        return document

    def test_seed_suite_loads_exactly_100_ordered_cases(self) -> None:
        self.assertEqual(len(self.cases), 100)
        self.assertEqual(
            [case["id"] for case in self.cases],
            [f"WIR-EQ-{index:03d}" for index in range(1, 101)],
        )
        for case in self.cases:
            self.assertEqual(
                [item["language"] for item in case["inputs"]],
                ["ja", "en", "zh-Hans"],
            )

    def test_current_reference_compiler_passes_case_001(self) -> None:
        report = evaluate_case(self.by_id["WIR-EQ-001"])
        self.assertEqual(report["outcome"], "pass_e1")
        self.assertTrue(report["semantic_equivalent"])
        self.assertTrue(report["e0_equivalent"])
        self.assertFalse(report["loss_detected"])

    def test_current_reference_compiler_abstains_on_all_expected_unsupported_cases(self) -> None:
        report = evaluate_seed_suite()
        unsupported = report["summary"]["unsupported"]
        self.assertGreater(unsupported["total"], 0)
        self.assertEqual(unsupported["passed_abstentions"], unsupported["total"])
        self.assertEqual(unsupported["abstention_rate"], 1.0)
        self.assertEqual(report["summary"]["false_equivalence"]["count"], 0)

    def test_e2_pass_requires_explicit_loss_detection(self) -> None:
        case = self.by_id["WIR-EQ-091"]

        def compiler(text: str, language: str) -> dict:
            return self._fake_document(
                text,
                language,
                fidelity_status="lossy",
                lost_features=["cultural_pragmatics"],
            )

        report = evaluate_case(case, compiler=compiler)
        self.assertEqual(report["outcome"], "pass_e2")
        self.assertTrue(report["semantic_equivalent"])
        self.assertTrue(report["loss_detected"])
        self.assertEqual(report["loss_features"], ["cultural_pragmatics"])

    def test_e2_without_loss_marker_is_false_equivalence(self) -> None:
        case = self.by_id["WIR-EQ-091"]

        def compiler(text: str, language: str) -> dict:
            return self._fake_document(text, language)

        report = evaluate_case(case, compiler=compiler)
        self.assertEqual(report["outcome"], "false_equivalence")
        self.assertTrue(report["false_equivalence"])

    def test_expected_unsupported_compiled_as_equivalent_is_false_equivalence(self) -> None:
        case = self.by_id["WIR-EQ-095"]

        def compiler(text: str, language: str) -> dict:
            return self._fake_document(text, language)

        report = evaluate_case(case, compiler=compiler)
        self.assertEqual(report["outcome"], "false_equivalence")
        self.assertTrue(report["false_equivalence"])

    def test_mixed_language_support_is_reported(self) -> None:
        case = self.by_id["WIR-EQ-002"]

        def compiler(text: str, language: str) -> dict:
            if language != "ja":
                raise UnsupportedUtteranceError("not implemented")
            return self._fake_document(text, language)

        report = evaluate_case(case, compiler=compiler)
        self.assertEqual(report["outcome"], "partial_support")
        self.assertEqual(
            [attempt["status"] for attempt in report["attempts"]],
            ["compiled", "unsupported", "unsupported"],
        )

    def test_suite_loader_rejects_duplicate_ids(self) -> None:
        template = {
            "id": "WIR-EQ-001",
            "category": "test",
            "expected_level": "E1",
            "inputs": [
                {"language": "ja", "text": "a"},
                {"language": "en", "text": "a"},
                {"language": "zh-Hans", "text": "a"},
            ],
            "target_semantics": "TEST",
            "notes": "",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "cases").mkdir()
            cases = [deepcopy(template), deepcopy(template)]
            (root / "cases" / "001-002.json").write_text(
                json.dumps(cases), encoding="utf-8"
            )
            manifest = {
                "suite": "test",
                "count": 2,
                "parts": [
                    {
                        "file": "cases/001-002.json",
                        "first_id": "WIR-EQ-001",
                        "last_id": "WIR-EQ-001",
                        "count": 2,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(SuiteIntegrityError, "duplicate"):
                load_seed_suite(manifest_path)

    def test_text_report_contains_required_metrics(self) -> None:
        text = format_text_report(evaluate_seed_suite())
        self.assertIn("schema-valid", text)
        self.assertIn("E1:", text)
        self.assertIn("E2 loss detection:", text)
        self.assertIn("unsupported abstention:", text)
        self.assertIn("false equivalence:", text)


if __name__ == "__main__":
    unittest.main()
