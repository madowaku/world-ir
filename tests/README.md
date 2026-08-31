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

- `E1`: the v0.1 semantic core should normalize to equivalent meaning.
- `E2`: the core should be compatible, but the compiler/evaluator should report a meaningful loss or unresolved distinction.
- `unsupported`: a conforming implementation should refuse to pretend the case is solved.

## Suggested scoring

Report at least:

1. schema-valid rate
2. E1 semantic match rate
3. E2 loss-detection precision/recall
4. unsupported-case abstention rate
5. false-equivalence rate

The most dangerous failure is not “unsupported.” It is **silently declaring two meanings equivalent after discarding a meaningful distinction**.

## Review note

The Japanese, English, and Simplified Chinese sentences are seed data. Before using the suite as a benchmark, have each language reviewed by native speakers and record revisions.
