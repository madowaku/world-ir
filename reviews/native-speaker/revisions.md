# Seed corpus revision log

All semantic or utterance changes made during corpus review are recorded here. AI preflight is not native-speaker verification.

## WIR-EQ-100

**Source:** AI preflight (#16)  
**Human native review:** pending (#13, #14, #15)

### Before

- `ja`: `布団が吹っ飛んだ。`
- `en`: `The futon flew away. (Japanese pun.)`
- `zh-Hans`: `被子飞走了。（日语双关语）`

### After

- `ja`: `布団が吹っ飛んだ。`
- `en`: `The futon flew away.`
- `zh-Hans`: `被子飞走了。`

### Reason

The English and Chinese inputs contained metalinguistic explanations that were absent from the Japanese utterance. Those annotations made the three input utterances non-comparable for reasons unrelated to the intended wordplay boundary. The explanation now lives in `notes`, while the translations preserve only the literal event.

This change does **not** assert that the English or Chinese translations have been approved by native speakers. They remain pending human review.
