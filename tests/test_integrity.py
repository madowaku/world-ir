from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from world_ir.integrity import check_repository_integrity


class RepositoryIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "schema").mkdir()
        (self.root / "examples").mkdir()
        (self.root / "tests" / "cases").mkdir(parents=True)
        self._write_fixture()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_json(self, relative: str, payload: object) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _case(self, index: int) -> dict[str, object]:
        return {
            "id": f"WIR-EQ-{index:03d}",
            "category": "fixture",
            "expected_level": "E1",
            "inputs": [
                {"language": "ja", "text": f"ja-{index}"},
                {"language": "en", "text": f"en-{index}"},
                {"language": "zh-Hans", "text": f"zh-{index}"},
            ],
            "target_semantics": "FIXTURE",
            "notes": "",
        }

    def _write_fixture(self) -> None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["ok"],
            "properties": {"ok": {"const": True}},
        }
        self._write_json("schema/world-ir-v0.1.schema.json", schema)
        self._write_json("examples/example.json", {"ok": True})

        parts = []
        for part_index in range(10):
            first = part_index * 10 + 1
            last = first + 9
            filename = f"cases/{first:03d}-{last:03d}.json"
            parts.append(
                {
                    "file": filename,
                    "first_id": f"WIR-EQ-{first:03d}",
                    "last_id": f"WIR-EQ-{last:03d}",
                    "count": 10,
                }
            )
            self._write_json(
                f"tests/{filename}",
                [self._case(index) for index in range(first, last + 1)],
            )
        self._write_json(
            "tests/equivalence-100.json",
            {"suite": "fixture", "count": 100, "parts": parts},
        )

    def test_clean_fixture_passes(self) -> None:
        report = check_repository_integrity(self.root)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.example_count, 1)
        self.assertEqual(report.part_count, 10)
        self.assertEqual(report.case_count, 100)
        self.assertEqual(
            report.summary(),
            "repository integrity: OK (schema=1 examples=1 parts=10 cases=100)",
        )

    def test_missing_case_file_fails_concisely(self) -> None:
        (self.root / "tests" / "cases" / "021-030.json").unlink()
        report = check_repository_integrity(self.root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("tests/cases/021-030.json: missing file" in error for error in report.errors),
            report.errors,
        )

    def test_malformed_json_fails_with_location(self) -> None:
        path = self.root / "tests" / "cases" / "031-040.json"
        path.write_text('[{"id":', encoding="utf-8")
        report = check_repository_integrity(self.root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any(
                "tests/cases/031-040.json: invalid JSON at line" in error
                for error in report.errors
            ),
            report.errors,
        )

    def test_duplicate_id_fails(self) -> None:
        path = self.root / "tests" / "cases" / "011-020.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        cases[0]["id"] = "WIR-EQ-010"
        self._write_json("tests/cases/011-020.json", cases)
        report = check_repository_integrity(self.root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("duplicate case id(s): WIR-EQ-010" in error for error in report.errors),
            report.errors,
        )

    def test_invalid_example_fails_schema_validation(self) -> None:
        self._write_json("examples/example.json", {"ok": False})
        report = check_repository_integrity(self.root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("examples/example.json: schema validation failed" in error for error in report.errors),
            report.errors,
        )

    def test_missing_language_fails(self) -> None:
        path = self.root / "tests" / "cases" / "041-050.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        cases[0]["inputs"] = cases[0]["inputs"][:2]
        self._write_json("tests/cases/041-050.json", cases)
        report = check_repository_integrity(self.root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any(
                "WIR-EQ-041 languages must be exactly" in error
                for error in report.errors
            ),
            report.errors,
        )

    def test_invalid_expected_level_fails(self) -> None:
        path = self.root / "tests" / "cases" / "051-060.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        cases[0]["expected_level"] = "E0"
        self._write_json("tests/cases/051-060.json", cases)
        report = check_repository_integrity(self.root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("WIR-EQ-051 expected_level" in error for error in report.errors),
            report.errors,
        )

    def test_manifest_duplicate_part_file_fails(self) -> None:
        path = self.root / "tests" / "equivalence-100.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest[1] if isinstance(manifest, list) else None
        manifest["parts"][1]["file"] = manifest["parts"][0]["file"]
        self._write_json("tests/equivalence-100.json", manifest)
        report = check_repository_integrity(self.root)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("duplicate part file" in error for error in report.errors),
            report.errors,
        )


if __name__ == "__main__":
    unittest.main()
