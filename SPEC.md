# World IR v0.1 Specification

Status: Experimental seed specification  
Version: `0.1.0`

## 1. Purpose

World IR is an inspectable intermediate representation (IR) for compiling utterance meaning into a shared structure that can be compared across languages.

The central v0.1 research question is:

> Can semantically equivalent utterances in different human languages be normalized into the same semantic core while preserving source-specific information and explicitly reporting loss?

World IR v0.1 is designed for LLM-based parsers, evaluators, and agent systems. It is not intended as a complete theory of linguistic meaning.

## 2. Non-goals

v0.1 does not attempt to:

- replace natural language;
- define a complete ontology of the world;
- solve lexical ambiguity in all domains;
- preserve poetry, humor, politeness, implicature, or cultural nuance losslessly;
- encode every syntactic distinction;
- expose or standardize hidden model embeddings;
- claim semantic completeness.

Cases outside the supported scope MUST be marked `lossy`, `unknown`, or unsupported by the evaluator rather than silently flattened.

## 3. Normative vocabulary

The keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

A **compiler** converts a source utterance to World IR.

A **canonicalizer** removes non-semantic differences and produces a deterministic comparison form.

An **equivalence evaluator** compares two or more canonical semantic cores.

A **semantic core** consists of normalized entities, frames, semantic links, utterance kind, and meaning-bearing features such as polarity, tense, modality, and quantification.

**Provenance** includes the source text, source language, source spans, model metadata, and other information that MUST NOT determine semantic equivalence unless explicitly configured.

## 4. Document model

A World IR document MUST contain:

- `world_ir_version`
- `id`
- `source`
- `utterance`
- `entities`
- `frames`
- `links`
- `fidelity`

It MAY contain:

- `context`
- `extensions`

### 4.1 `world_ir_version`

For this specification the value MUST be `0.1.0`.

### 4.2 `source`

`source.text` MUST retain the original utterance exactly as supplied to the compiler.

`source.language` MUST use a BCP 47 language tag such as `ja`, `en`, `zh-Hans`, or `en-US`.

Source text is provenance. It is excluded from semantic equivalence.

### 4.3 `utterance`

`utterance.kind` identifies the communicative function after semantic normalization.

v0.1 values:

- `assertion`
- `question`
- `directive`
- `request`
- `intention`
- `wish`
- `exclamation`
- `fragment`

Surface grammar MUST NOT override semantic function. For example, “Could you close the door?” MAY normalize to `request` rather than `question` when used as an indirect request.

### 4.4 Entities

Entities represent discourse participants or referents.

Each entity MUST have:

- local `id`
- `type`
- `concept`

`concept` is a bootstrap symbolic identifier such as `DOG`, `PERSON`, or `TOKYO`.

The spelling of a v0.1 concept identifier is NOT its definition. It MUST be treated as an opaque symbol whose semantics are established by the World IR vocabulary or an external registry.

Entity names MAY retain language-specific surface forms.

Quantification MAY be represented with:

- `definite`
- `indefinite`
- `all`
- `some`
- `none`
- `numeric`
- `at_least`
- `at_most`
- `exactly`
- `most`
- `unspecified`

Scope-heavy quantification is only partially supported in v0.1.

### 4.5 Frames

Frames are the primary unit of meaning.

A frame MUST contain:

- `id`
- `frame_type`
- `predicate`
- `roles`
- `polarity`
- `tense`
- `aspect`
- `modality`
- `certainty`

`frame_type` is one of:

- `event`
- `state`
- `relation`
- `speech_act`

`predicate` is a normalized symbolic identifier such as `RUN`, `SLEEP`, `FATHER_OF`, `RAIN`, or `CLOSE`.

### 4.6 Roles

Roles connect a frame to an entity, another frame, or a literal.

Core v0.1 role labels include:

- `AGENT`
- `PATIENT`
- `THEME`
- `EXPERIENCER`
- `STIMULUS`
- `RECIPIENT`
- `SOURCE`
- `DESTINATION`
- `INSTRUMENT`
- `LOCATION`
- `POSSESSOR`
- `POSSESSED`
- `PARENT`
- `CHILD`
- `WHOLE`
- `PART`
- `VALUE`
- `TOPIC`
- `CONTENT`
- `ADDRESSEE`

Compilers SHOULD prefer these roles but MAY use extension identifiers.

### 4.7 Polarity

`polarity` is:

- `positive`
- `negative`

Negation scope is significant. If a compiler cannot reliably identify scope, it MUST mark the document `lossy` or `unknown` rather than guessing.

### 4.8 Tense and aspect

`tense` values:

- `past`
- `present`
- `future`
- `timeless`
- `unspecified`

`aspect` values:

- `simple`
- `progressive`
- `perfect`
- `habitual`
- `completed`
- `ongoing`
- `unspecified`

These are deliberately coarse.

### 4.9 Modality and certainty

`modality` values:

- `asserted`
- `possible`
- `probable`
- `necessary`
- `obligatory`
- `permitted`
- `desired`
- `intended`
- `requested`
- `commanded`
- `inferred`
- `reported`
- `unspecified`

`certainty` is a number from `0.0` to `1.0`.

Certainty values are calibration hints, not universal truth probabilities. Semantic equivalence SHOULD compare certainty by configured bands rather than require identical floating-point values.

Suggested default bands:

- `0.00–0.19`: very unlikely / very uncertain
- `0.20–0.39`: unlikely
- `0.40–0.59`: unresolved / maybe
- `0.60–0.79`: probable
- `0.80–0.94`: highly probable
- `0.95–1.00`: asserted / near-certain

### 4.10 Time

Time MAY be absolute or relative.

Relative time SHOULD be normalized against `context.reference_time` where available.

Example for “tomorrow”:

```json
{
  "anchor": "reference_time",
  "relation": "after",
  "offset": {"value": 1, "unit": "day"}
}
```

The lexical token `tomorrow`, `明日`, or `明天` SHOULD NOT be required for semantic equivalence after normalization.

### 4.11 Semantic links

Cross-frame semantics are represented by `links`.

Core v0.1 link types:

- `condition`
- `cause`
- `before`
- `after`
- `equivalent`
- `contrast`
- `conjunction`
- `disjunction`
- `coreference`
- `purpose`

For a conditional, `from` is the antecedent frame and `to` is the consequent frame.

### 4.12 Fidelity

Every document MUST contain a fidelity object.

`fidelity.status` is:

- `lossless`
- `lossy`
- `unknown`

`lossless` means no meaning-bearing distinction known to the compiler was intentionally discarded within the supported v0.1 scope. It does NOT claim philosophical or linguistic completeness.

If `lossy`, `lost_features` SHOULD name what was lost, for example:

- `honorific_level`
- `cultural_pragmatics`
- `sarcasm`
- `wordplay`
- `negation_scope`
- `quantifier_scope`
- `deixis`
- `coreference`

## 5. Context aliases

v0.1 permits these reserved references without declaring ordinary entities:

- `ctx:speaker`
- `ctx:addressee`
- `ctx:here`
- `ctx:reference_time`

Compilers SHOULD resolve them to concrete entities or values when context is available.

Unresolved context aliases make two utterances only conditionally comparable.

## 6. Canonicalization

A conforming canonicalizer MUST:

1. validate the input document against the v0.1 JSON Schema;
2. exclude provenance fields from the semantic comparison core;
3. normalize entity and frame IDs deterministically;
4. sort entities, frames, roles, and links deterministically;
5. retain meaning-bearing features;
6. retain unresolved ambiguity or fidelity-loss markers;
7. produce deterministic UTF-8 JSON for the same semantic structure.

### 6.1 ID normalization

Local IDs (`e1`, `f1`, etc.) carry no semantics.

Canonicalizers SHOULD renumber entities and frames after sorting by semantic content.

### 6.2 Ignored comparison fields

The default equivalence profile ignores:

- `source.text`
- `source.language`
- `source_spans`
- compiler/model metadata in extensions
- human-readable labels and names when the normalized referent is otherwise identical

### 6.3 Required comparison fields

The default equivalence profile compares:

- utterance kind
- entity concepts
- quantification
- frame predicates
- semantic roles
- polarity
- tense
- aspect
- modality
- certainty band
- normalized time
- semantic links
- unresolved ambiguity markers
- fidelity status and named losses

## 7. Equivalence levels

World IR v0.1 defines three evaluation levels.

### E0: exact canonical equivalence

Canonical semantic-core JSON is byte-identical.

Use for deterministic regression tests.

### E1: semantic equivalence

The same predicates, participants, semantic relations, polarity, temporal meaning, modality, quantification, and relevant scope are preserved.

Minor representational variation allowed by the spec MAY be normalized away.

This is the primary cross-lingual target.

### E2: compatible-with-loss

The principal proposition is shared, but one or more meaning-bearing distinctions are missing, ambiguous, culturally specific, pragmatic, or unsupported.

The evaluator MUST report the losses.

`unsupported` is not E2. It means the current representation cannot responsibly encode the case.

## 8. v0.1 supported semantic families

### 8.1 Simple events and states

Example:

- 犬が走った。
- The dog ran.
- 狗跑了。

Core:

`RUN(AGENT=DOG), tense=past, asserted`

### 8.2 Relations

Example:

- 太郎は花子の父親だ。
- Taro is Hanako's father.
- 太郎是花子的父亲。

Core:

`FATHER_OF(PARENT=TARO, CHILD=HANAKO)`

### 8.3 Conditionals

Example:

- 雨ならピクニックは中止だ。
- If it rains, the picnic is cancelled.
- 如果下雨，野餐就取消。

Core:

`RAIN` →[`condition`] `CANCEL(PATIENT=PICNIC)`

### 8.4 Epistemic modality

Example:

- 彼はたぶん来る。
- He will probably come.
- 他大概会来。

Core:

`COME(AGENT=PERSON), modality=probable`

### 8.5 Directives and intentions

Example:

- ドアを閉めてください。
- Please close the door.
- 请把门关上。

Core:

`CLOSE(AGENT=ctx:addressee, PATIENT=DOOR), utterance=request, modality=requested`

## 9. Known v0.1 hard cases

The following MUST NOT be silently treated as solved:

- pronoun/coreference ambiguity;
- deixis without context;
- quantifier-scope ambiguity;
- negation-scope ambiguity;
- irony and sarcasm;
- idioms whose pragmatic effect exceeds literal meaning;
- honorific and politeness distinctions;
- culturally specific speech acts;
- puns and sound-based meaning;
- multimodal meaning not present in the text input.

## 10. Compiler conformance

A v0.1 compiler is conforming if it:

- emits schema-valid World IR;
- preserves the exact source text;
- uses a valid BCP 47 language tag;
- emits at least one frame for supported non-fragment utterances;
- does not silently discard recognized meaning-bearing distinctions;
- marks loss/uncertainty when it cannot normalize safely.

## 11. Evaluator conformance

A v0.1 evaluator is conforming if it:

- distinguishes E0, E1, E2, and unsupported;
- ignores non-semantic provenance by default;
- reports feature mismatches;
- reports named losses for E2;
- does not convert unknown ambiguity into false certainty.

## 12. Seed test suite

`tests/equivalence-100.json` contains 100 cross-lingual seed cases in Japanese, English, and Chinese.

The suite is divided into:

1. simple facts
2. tense/aspect
3. negation
4. relations
5. conditionals
6. epistemic modality
7. directives/intentions
8. quantification
9. context/coreference
10. pragmatics/cultural boundaries

The first seven groups are primarily positive capability tests. The final three deliberately probe partial support and failure behavior.

## 13. Versioning

Backward-incompatible schema or semantic changes MUST increment the minor version before 1.0.

Patch versions MAY fix examples, wording, or schema defects without changing intended semantics.

## 14. Future directions

Potential v0.2 work:

- stable concept registry / URI scheme;
- explicit scope graphs;
- event coreference;
- discourse relations;
- provenance confidence per field;
- ambiguity lattices instead of one guessed parse;
- JSON-LD mappings;
- multimodal referents;
- benchmark tooling and canonical hash generation;
- native-speaker-reviewed multilingual corpora beyond Japanese, English, and Chinese.
