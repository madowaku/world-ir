from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from world_ir.compiler import (
    UnsupportedLanguageError,
    UnsupportedUtteranceError,
    compile_utterance,
    semantic_core,
    validate_document,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = {
    "ja": ROOT / "examples" / "dog-ran.ja.json",
    "en": ROOT / "examples" / "dog-ran.en.json",
    "zh-Hans": ROOT / "examples" / "dog-ran.zh.json",
}


class CompilerTests(unittest.TestCase):
    def test_seed_examples_compile_to_schema_valid_ir(self) -> None:
        for language, path in EXAMPLES.items():
            example = json.loads(path.read_text(encoding="utf-8"))
            document = compile_utterance(example["source"]["text"], language)
            validate_document(document)
            self.assertEqual(document["source"]["text"], example["source"]["text"])
            self.assertEqual(document["source"]["language"], language)

    def test_seed_examples_share_the_same_semantic_core(self) -> None:
        cores = []
        for language, path in EXAMPLES.items():
            example = json.loads(path.read_text(encoding="utf-8"))
            cores.append(
                semantic_core(
                    compile_utterance(example["source"]["text"], language)
                )
            )
        self.assertEqual(cores[0], cores[1])
        self.assertEqual(cores[1], cores[2])

    def test_source_text_is_preserved_exactly(self) -> None:
        text = "  犬が走った。  "
        document = compile_utterance(text, "ja")
        self.assertEqual(document["source"]["text"], text)

    def test_compiler_metadata_is_outside_semantic_core(self) -> None:
        document = compile_utterance("The dog ran.", "en")
        self.assertIn("compiler", document["extensions"])
        self.assertNotIn("extensions", semantic_core(document))

    def test_unknown_utterance_is_rejected_instead_of_guessed(self) -> None:
        with self.assertRaises(UnsupportedUtteranceError):
            compile_utterance("The cat slept.", "en")

    def test_unsupported_language_is_rejected(self) -> None:
        with self.assertRaises(UnsupportedLanguageError):
            compile_utterance("Le chien a couru.", "fr")

    def test_cli_emits_valid_json(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "world_ir", "狗跑了。", "--lang", "zh-Hans"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        validate_document(payload)
        self.assertEqual(payload["frames"][0]["predicate"], "RUN")

    def test_cli_fails_cleanly_for_unknown_text(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "world_ir", "猫睡了。", "--lang", "zh-Hans"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Refusing to guess semantics", proc.stderr)


if __name__ == "__main__":
    unittest.main()
