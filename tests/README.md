# World IR v0.1 Seed Evaluation

The v0.1 seed suite contains **100 design-level cross-lingual test cases**. It is a research seed, not a gold linguistic corpus.

`equivalence-100.json` is the suite manifest. The actual cases are split into ten review-friendly files under `cases/`, with ten cases per file:

```text
tests/
├─ README.md
├─ equivalence-100.json
└─ cases/
   ├─ 001-010.json
   ├─ 011-020.json
   ├─ 021-030.json
   ├─ 031-040.json
   ├─ 041-050.json
   ├─ 051-060.json
   ├─ 061-070.json
   ├─ 071-080.json
   ├─ 081-090.json
   └─ 091-100.json
```

Each case contains:

- `id`
- `category`
- `expected_level`
- three source inputs (`ja`, `en`, `zh-Hans`)
- `target_semantics`, a compact human-readable target
- `notes`

## Expected levels

- `E1`: the v0.1 semantic core should normalize to equivalent meaning without declared loss.
- `E2`: the shared proposition should be compatible and the compiler/evaluator should explicitly report a meaningful loss or unresolved distinction.
- `unsupported`: a conforming implementation should refuse to pretend the case is solved.

## Executable evaluator

Issue #3 makes the suite executable:

```bash
world-ir-eval
world-ir-eval --details
world-ir-eval --json > report.json
```

The harness validates the manifest before evaluation: exactly 100 contiguous unique IDs, ten referenced case files, and exactly one `ja`, `en`, and `zh-Hans` input per case.

Case outcomes include:

- `pass_e1`
- `pass_e2`
- `pass_unsupported`
- `not_covered`
- `partial_support`
- `semantic_mismatch`
- `unexpected_loss`
- `invalid_output`
- `compiler_error`
- `unsupported_violation`
- `false_equivalence`

`not_covered` is not treated as success, but it is preferable to invented semantics. The current seed compiler intentionally covers only WIR-EQ-001 and abstains elsewhere.

For E2, the evaluator compares canonical semantic content separately from `fidelity`: equivalent content plus an explicit `lossy`/`unknown` status or named `lost_features` can pass E2. Equivalent content with no loss marker is classified as **false equivalence**.

## Metrics

The report includes:

1. schema-valid rate among emitted documents
2. full three-language coverage rate
3. E1 strict and covered semantic match rates
4. E2 loss-detection precision, strict recall, and covered recall
5. unsupported-case abstention rate
6. false-equivalence count, rate, and case IDs
7. per-case compiler/validation diagnostics

Use `--fail-on-false-equivalence` when false equivalence should make a command fail:

```bash
world-ir-eval --fail-on-false-equivalence
```

The most dangerous failure is not “unsupported.” It is **silently declaring two meanings equivalent after discarding a meaningful distinction**.

## Review note

The Japanese, English, and Simplified Chinese sentences are seed data. Before using the suite as a benchmark, have each language reviewed by native speakers and record revisions.
