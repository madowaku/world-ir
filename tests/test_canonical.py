from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from world_ir.canonical import (
    canonical_bytes,
    canonical_json,
    canonicalize,
    certainty_band,
    e0_equivalent,
)


ROOT = Path(__file__).resolve().parents[1]


def load_example(name: str) -> dict:
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def two_event_document() -> dict:
    return {
        "world_ir_version": "0.1.0",
        "id": "two-event-source-a",
        "source": {"text": "A dog chased a cat and the cat slept.", "language": "en", "channel": "text"},
        "utterance": {"kind": "assertion"},
        "entities": [
            {"id": "e1", "type": "animal", "concept": "DOG", "quantifier": {"kind": "indefinite"}},
            {"id": "e2", "type": "animal", "concept": "CAT", "quantifier": {"kind": "indefinite"}},
        ],
        "frames": [
            {
                "id": "f1",
                "frame_type": "event",
                "predicate": "CHASE",
                "roles": [
                    {"role": "AGENT", "value": {"entity_ref": "e1"}},
                    {"role": "PATIENT", "value": {"entity_ref": "e2"}},
                ],
                "polarity": "positive",
                "tense": "past",
                "aspect": "simple",
                "modality": "asserted",
                "certainty": 0.99,
            },
            {
                "id": "f2",
                "frame_type": "event",
                "predicate": "SLEEP",
                "roles": [{"role": "EXPERIENCER", "value": {"entity_ref": "e2"}}],
                "polarity": "positive",
                "tense": "past",
                "aspect": "simple",
                "modality": "asserted",
                "certainty": 1.0,
            },
        ],
        "links": [{"type": "before", "from": "f1", "to": "f2"}],
        "fidelity": {"status": "lossless", "lost_features": [], "notes": []},
    }


class CanonicalizationTests(unittest.TestCase):
    def test_three_dog_ran_examples_have_same_e0_form(self) -> None:
        docs = [
            load_example("dog-ran.ja.json"),
            load_example("dog-ran.en.json"),
            load_example("dog-ran.zh.json"),
        ]
        forms = [canonical_bytes(doc) for doc in docs]
        self.assertEqual(forms[0], forms[1])
        self.assertEqual(forms[1], forms[2])

    def test_local_ids_and_collection_order_do_not_change_e0(self) -> None:
        original = two_event_document()
        changed = deepcopy(original)
        changed["entities"] = list(reversed(changed["entities"]))
        changed["frames"] = list(reversed(changed["frames"]))
        for frame in changed["frames"]:
            frame["roles"] = list(reversed(frame["roles"]))

        entity_ids = {"e1": "e91", "e2": "e17"}
        frame_ids = {"f1": "f88", "f2": "f12"}
        for entity in changed["entities"]:
            entity["id"] = entity_ids[entity["id"]]
        for frame in changed["frames"]:
            old = frame["id"]
            frame["id"] = frame_ids[old]
            for role in frame["roles"]:
                ref = role["value"].get("entity_ref")
                if ref:
                    role["value"]["entity_ref"] = entity_ids[ref]
        for link in changed["links"]:
            link["from"] = frame_ids[link["from"]]
            link["to"] = frame_ids[link["to"]]

        self.assertTrue(e0_equivalent(original, changed))
        canonical = canonicalize(changed)
        self.assertEqual([e["id"] for e in canonical["entities"]], ["e1", "e2"])
        self.assertEqual([f["id"] for f in canonical["frames"]], ["f1", "f2"])

    def test_provenance_and_names_are_ignored(self) -> None:
        left = load_example("dog-ran.en.json")
        right = deepcopy(left)
        right["id"] = "totally-different-source-id"
        right["source"]["text"] = "THE DOG RAN!"
        right["source"]["language"] = "en-US"
        right["entities"][0]["names"] = [{"language": "en", "text": "doggo"}]
        right["frames"][0]["source_spans"] = [{"start": 0, "end": 3}]
        right["extensions"] = {"compiler": {"name": "another-model", "version": "999"}}
        right["fidelity"]["notes"] = ["Human-readable note only"]
        self.assertTrue(e0_equivalent(left, right))

    def test_certainty_values_in_same_band_are_e0_equivalent(self) -> None:
        left = load_example("dog-ran.en.json")
        right = deepcopy(left)
        left["frames"][0]["certainty"] = 0.96
        right["frames"][0]["certainty"] = 0.999
        self.assertTrue(e0_equivalent(left, right))

    def test_certainty_crossing_band_changes_e0(self) -> None:
        left = load_example("dog-ran.en.json")
        right = deepcopy(left)
        left["frames"][0]["certainty"] = 0.94
        right["frames"][0]["certainty"] = 0.95
        self.assertFalse(e0_equivalent(left, right))

    def test_polarity_and_modality_are_meaning_bearing(self) -> None:
        base = load_example("dog-ran.en.json")
        negative = deepcopy(base)
        negative["frames"][0]["polarity"] = "negative"
        probable = deepcopy(base)
        probable["frames"][0]["modality"] = "probable"
        self.assertFalse(e0_equivalent(base, negative))
        self.assertFalse(e0_equivalent(base, probable))

    def test_lost_features_are_sorted_but_meaning_bearing(self) -> None:
        left = load_example("dog-ran.en.json")
        right = deepcopy(left)
        left["fidelity"] = {
            "status": "lossy",
            "lost_features": ["deixis", "honorific_level"],
            "notes": [],
        }
        right["fidelity"] = {
            "status": "lossy",
            "lost_features": ["honorific_level", "deixis"],
            "notes": ["Different prose"],
        }
        self.assertTrue(e0_equivalent(left, right))
        other = deepcopy(right)
        other["fidelity"]["lost_features"] = ["deixis"]
        self.assertFalse(e0_equivalent(left, other))

    def test_canonical_json_is_compact_deterministic_utf8(self) -> None:
        doc = load_example("dog-ran.ja.json")
        text = canonical_json(doc)
        self.assertEqual(text.encode("utf-8"), canonical_bytes(doc))
        self.assertNotIn("source", json.loads(text))
        self.assertIn("犬", doc["source"]["text"])
        self.assertNotIn("\\u", text)
        self.assertEqual(text, canonical_json(doc))

    def test_certainty_band_boundaries(self) -> None:
        expected = {
            0.00: "very_unlikely",
            0.19: "very_unlikely",
            0.20: "unlikely",
            0.39: "unlikely",
            0.40: "unresolved",
            0.59: "unresolved",
            0.60: "probable",
            0.79: "probable",
            0.80: "highly_probable",
            0.94: "highly_probable",
            0.95: "asserted",
            1.00: "asserted",
        }
        for value, band in expected.items():
            with self.subTest(value=value):
                self.assertEqual(certainty_band(value), band)


if __name__ == "__main__":
    unittest.main()
