from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "reviews" / "native-speaker" / "081-100.json"
ALLOWED_HUMAN_STATUSES = {
    "pending",
    "verified",
    "revision_requested",
    "revised_verified",
}
VERIFIED_STATUSES = {"verified", "revised_verified"}
ALLOWED_PREFLIGHT = {
    "ok",
    "ok_boundary",
    "review_needed",
    "revision_candidate",
    "revision_applied",
}


class NativeReviewLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_priority_scope_has_exactly_081_through_100(self) -> None:
        ids = [case["id"] for case in self.data["cases"]]
        expected = [f"WIR-EQ-{i:03d}" for i in range(81, 101)]
        self.assertEqual(ids, expected)

    def test_human_languages_are_explicit(self) -> None:
        self.assertEqual(set(self.data["human_review"]), {"ja", "en", "zh-Hans"})

    def test_human_review_statuses_are_known(self) -> None:
        for language, record in self.data["human_review"].items():
            with self.subTest(language=language):
                self.assertIn(record["status"], ALLOWED_HUMAN_STATUSES)

    def test_verified_status_requires_human_provenance(self) -> None:
        for language, record in self.data["human_review"].items():
            if record["status"] in VERIFIED_STATUSES:
                with self.subTest(language=language):
                    self.assertTrue(record.get("reviewer"))
                    self.assertTrue(record.get("reference"))

    def test_ai_preflight_never_implies_human_verification(self) -> None:
        for case in self.data["cases"]:
            with self.subTest(case=case["id"]):
                self.assertIn(case["preflight"], ALLOWED_PREFLIGHT)
                self.assertTrue(case["findings"])


if __name__ == "__main__":
    unittest.main()
