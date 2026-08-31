# World IR v0.1 Seed Evaluation

`equivalence-100.json` is a design-level seed suite, not a gold linguistic corpus.

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
2. E1 exact semantic match rate
3. E2 loss-detection precision/recall
4. unsupported-case abstention rate
5. false-equivalence rate

The most dangerous failure is not “unsupported.” It is **silently declaring two meanings equivalent after discarding a meaningful distinction**.

## Review note

The Japanese, English, and Simplified Chinese sentences are seed data. Before using the suite as a benchmark, have each language reviewed by native speakers and record revisions.
