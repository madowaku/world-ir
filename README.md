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

## Repository layout

```text
world-ir/
├─ README.md
├─ SPEC.md
├─ schema/
│  └─ world-ir-v0.1.schema.json
├─ examples/
│  ├─ dog-ran.ja.json
│  ├─ dog-ran.en.json
│  └─ dog-ran.zh.json
└─ tests/
   ├─ README.md
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
