# Native-speaker review protocol

This directory records human review of the World IR seed corpus.

## Important distinction

AI or automated review is **preflight only**. It can find obvious structural mismatches, added information, annotations embedded in one language, or likely naturalness problems. It MUST NOT be recorded as native-speaker verification.

A language is `verified` only when a human native speaker has reviewed the case and the reviewer identity/reference is recorded.

## Per-case questions

For every language in every case, reviewers should answer:

1. Is the utterance natural in isolation for the intended reading?
2. Is it genuinely compatible with the other language inputs?
3. Does it add or omit meaning that would affect semantic comparison?
4. Are ambiguity, deixis, register, politeness, irony, scope, or cultural conventions relevant?
5. Does `target_semantics` preserve the important distinction?
6. Is `expected_level` (`E1`, `E2`, `unsupported`) defensible?

## Status values

- `pending`: no human native-speaker review yet
- `verified`: reviewed and accepted by a human native speaker
- `revision_requested`: reviewed by a human native speaker and needs a change
- `revised_verified`: revised and then accepted by a human native speaker

AI preflight uses a separate `preflight` field and never changes human status.

## Revision log rule

Every semantic change to a seed case MUST record:

- case ID
- language(s) affected
- before / after text or metadata
- reason
- whether the change came from AI preflight or human native review
- related issue / PR

## Priority

Review WIR-EQ-081 through WIR-EQ-100 first. These intentionally stress coreference, deixis, cultural pragmatics, honorifics, sarcasm, indirect speech acts, emoji, and wordplay.

Tracking issues:

- #13 Japanese native review
- #14 English native review
- #15 Simplified Chinese native review
- #16 AI preflight audit
- #5 parent review issue
