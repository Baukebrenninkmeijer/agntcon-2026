# Decision-support v4 evaluation data

This directory is the durable, tracked copy of the accepted Sphere.com v4 evaluation artifacts. Runtime-generated call, item, thread, and saved-insight identifiers are replaced with stable row-local placeholders; analytical content, call/result linkage, judge votes, and repetition detail are preserved. Fingerprints and annotation identities are regenerated from that sanitized transcript.

- `../simulation-cases-v4.jsonl` — 50 authored simulation case definitions.
- `observations.jsonl` — 50 accepted observed conversations from the canonical retry.
- `jury-baseline/` — the original rubric run used to surface the first grey zones.
- `jury-human-rules-v1/` — the diagnostic rerun after adding the three human boundary rules.
- `human-labels-dev-v1.jsonl` — 30 human-confirmed development labels with written explanations;
  the 20-case test split remains sealed.
- `proposed-prompt-v2.md` — the accepted v2 prompt clarification derived from those labels.

Each jury version contains:

- `evaluator-prompt.txt` — the exact evaluator prompt used for that run.
- `jury-results.jsonl` — 50 complete `decision_support_quality` records, preserving three judges × three repetitions.
- `annotation/queue.json` — development-only disagreement/wobble review items plus five stable controls.
- `annotation/test_manifest.json` — identity-only records for the 20 sealed test cases.
- `annotation/jury_errors.json` — mechanically invalid jury records; empty in both versions.
- `annotation/manifest.json` — schema, readiness state, and hashes for the annotation files.

The observations and jury results are immutable evidence. Do not regenerate or edit them in place.
The confirmed development labels are a separate human artifact and must not be inferred from jury
votes. The ignored `runs/` copies remain only as working inputs for the currently running
annotation server.

## Provenance

- Accepted raw observation source SHA-256: `b890fd35d7ba34ae2ec9b787b443b6b020f7f8115229658e23f7a8e1119703db`
- Tracked sanitized observations SHA-256: `bf560f5cd94aa916110a03fc46cf006bbbe5e006e839680427aed481c67740ab`
- Baseline accepted raw jury SHA-256: `64713ea77b951ad880e11c3f30fbd0322933bb3676339e8b909fb0f113765d24`
- Baseline tracked jury SHA-256: `1c1a900fcbf33f84c1db9e9076a409c654e32614d6dfc0538762183dc81e1f69`
- Human-rules-v1 tracked jury SHA-256: `bbbddb22d3fbcc9fa71ff22ba39a76247bfd59170a3cbb5ae0a92569ef2a4a9f`
- Human-rules-v1 accepted raw jury SHA-256: `5a9915cf8e3130fb2e9f5419db482f86df79bde4203eb544450a51caa78ebec2`
- Annotation schema: `jury-annotation-v1`
