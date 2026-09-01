# World IR

> **Compile meaning, not language.**

World IR is an experimental, language-independent intermediate representation for comparing meaning across human languages.

The v0.1 goal is intentionally small:

> Given semantically equivalent utterances in Japanese, English, and Chinese, can an AI compile them into the same inspectable semantic structure without discarding important differences?

World IR is **not** a new human language, a replacement for natural language, or a claim to have solved semantics. It is a testable IR for LLM-era semantic compilation.

## v0.1 scope

World IR v0.1 focuses on:

1. simple facts and events
2. relations
3. conditionals
4. epistemic modality / uncertainty
5. directives, requests, desires, and intentions

It also has seed tests for negation, quantification, coreference, deixis, pragmatics, and culturally loaded expressions so that failure boundaries are visible from day one.

## Reference compiler

Issue #1 adds the first executable compiler loop. It is deliberately tiny: v0.1 recognizes only the three `dog-ran` seed utterances and refuses unknown text rather than inventing semantics.

Install the project in editable mode from the repository root:

```bash
python -m pip install -e .
```

Compile one utterance:

```bash
python -m world_ir "犬が走った。" --lang ja
python -m world_ir "The dog ran." --lang en
python -m world_ir "狗跑了。" --lang zh-Hans
```

The CLI validates its output against `schema/world-ir-v0.1.schema.json` by default. Use `--no-validate` only for debugging.

Unknown utterances fail conservatively:

```bash
python -m world_ir "The cat slept." --lang en
# world-ir: The v0.1 reference compiler does not know this utterance. Refusing to guess semantics.
```

## Canonicalization and E0 comparison

Issue #2 adds a deterministic semantic comparison form. Canonicalization:

- removes provenance such as `source`, top-level `id`, compiler `extensions`, source spans, entity display names, and fidelity notes;
- regenerates local entity/frame IDs after semantic sorting;
- sorts entities, frames, roles, links, and lost-feature lists deterministically;
- converts numeric `certainty` values into the v0.1 comparison bands;
- preserves meaning-bearing fields such as polarity, modality, quantification, links, context, and fidelity losses;
- emits compact deterministic UTF-8 JSON.

Python API:

```python
from world_ir import canonical_bytes, canonical_json, canonicalize, e0_equivalent

canonical = canonicalize(document)
text = canonical_json(document)
digest_input = canonical_bytes(document)
same_e0 = e0_equivalent(document_a, document_b)
```

The Japanese, English, and Simplified Chinese `dog-ran` examples are E0-equivalent even though their source text and source-language metadata differ.

## 100-case evaluation harness

Issue #3 connects the compiler to the full seed suite and reports E1, E2, unsupported, coverage, validation, and false-equivalence metrics.

Run a compact report:

```bash
world-ir-eval
```

Show non-passing case diagnostics or emit machine-readable JSON:

```bash
world-ir-eval --details
world-ir-eval --json > report.json
```

The evaluator is conservative by design:

- `E1` passes only when all three languages compile to the same canonical semantic content without declared loss.
- `E2` passes when the shared semantic content is compatible **and** loss/uncertainty is explicitly reported through `fidelity`.
- `unsupported` passes only when all three languages abstain.
- an E2 or unsupported case that is silently flattened into one equivalent meaning is marked `false_equivalence`.

The current reference compiler still recognizes only WIR-EQ-001. The harness therefore exposes low capability coverage without converting honest abstention into invented success.

Programmatic API:

```python
from world_ir import evaluate_seed_suite, format_text_report

report = evaluate_seed_suite()
print(format_text_report(report, details=True))
```

## Repository integrity

Issue #4 adds an independent data-integrity gate. It does **not** invoke the compiler or evaluator, so broken fixtures cannot hide behind application code.

Run it locally:

```bash
world-ir-integrity --root .
```

A healthy repository prints one compact line:

```text
repository integrity: OK (schema=1 examples=3 parts=10 cases=100)
```

The checker fails on:

- an invalid JSON Schema Draft 2020-12 document;
- any example that is malformed JSON or schema-invalid;
- a missing or duplicated manifest part;
- malformed case JSON;
- missing, duplicated, unexpected, or reordered `WIR-EQ-001` through `WIR-EQ-100` IDs;
- case files that are not exactly 10 cases each;
- missing or duplicated `ja`, `en`, or `zh-Hans` inputs;
- invalid `expected_level` values.

GitHub Actions runs this as the separate **Repository integrity** workflow. Success stays compact; failures emit path-specific diagnostics.

## Native-speaker review status

Issue #5 tracks human review of the seed corpus before it is treated as a benchmark. AI inspection is explicitly separated from native-speaker verification.

Priority review currently covers WIR-EQ-081 through WIR-EQ-100:

- Japanese human native review: **pending** (#13)
- English human native review: **pending** (#14)
- Simplified Chinese human native review: **pending** (#15)
- AI preflight audit: recorded separately in `reviews/native-speaker/081-100.json` (#16)

`reviews/native-speaker/README.md` defines the review protocol, and `reviews/native-speaker/revisions.md` records the reason for every semantic corpus change. AI preflight can suggest or make purely structural corrections, but it MUST NOT mark a language as native-speaker verified.

Run all unit tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Repository layout

```text
world-ir/
├─ README.md
├─ SPEC.md
├─ pyproject.toml
├─ .github/workflows/
│  ├─ reference-compiler.yml
│  └─ repository-integrity.yml
├─ world_ir/
│  ├─ __init__.py
│  ├─ __main__.py
│  ├─ canonical.py
│  ├─ cli.py
│  ├─ compiler.py
│  ├─ eval_cli.py
│  ├─ evaluation.py
│  ├─ integrity.py
│  └─ integrity_cli.py
├─ reviews/native-speaker/
│  ├─ README.md
│  ├─ 081-100.json
│  └─ revisions.md
├─ schema/
│  └─ world-ir-v0.1.schema.json
├─ examples/
│  ├─ dog-ran.ja.json
│  ├─ dog-ran.en.json
│  └─ dog-ran.zh.json
└─ tests/
   ├─ README.md
   ├─ test_canonical.py
   ├─ test_compiler.py
   ├─ test_evaluation.py
   ├─ test_integrity.py
   ├─ equivalence-100.json
   └─ cases/
      ├─ 001-010.json
      ├─ 011-020.json
      ├─ ...
      └─ 091-100.json
```

## Minimal example

These three utterances:

- `ja`: 犬が走った。
- `en`: The dog ran.
- `zh-Hans`: 狗跑了。

should compile to structures whose semantic core is equivalent:

```json
{
  "predicate": "RUN",
  "roles": [
    {"role": "AGENT", "value": {"entity_ref": "e1"}}
  ],
  "polarity": "positive",
  "tense": "past",
  "modality": "asserted"
}
```

The entity is normalized as `DOG`. The source sentence and source language are always retained outside the semantic core.

## Design principles

- **Preserve before compressing.** If normalization would erase meaning, record the loss instead.
- **Keep the original.** World IR is an intermediate layer, not a substitute for source text.
- **AI-first, inspectable by humans.** Machines may generate it, but humans must be able to audit it.
- **Model-independent.** The format must not depend on one model's hidden embeddings or tokens.
- **Failure is data.** Unsupported or lossy cases are first-class evaluation results.
- **Symbols are identifiers, not English definitions.** `RUN` and `DOG` are bootstrap IDs in v0.1; future versions may replace them with stable URIs/registries.

## Prior art and standards

World IR should learn from, not pretend to replace, semantic representations such as AMR and UCCA. v0.1 uses:

- JSON as the interchange syntax
- JSON Schema Draft 2020-12 for structural validation
- BCP 47 language tags for source-language identifiers

Future versions may add JSON-LD-compatible identifiers or mappings.

## Status

**v0.1 experimental seed specification.**

The project should be judged by cross-lingual equivalence tests, fidelity, and useful failure reporting, not by how elegant the notation looks.
