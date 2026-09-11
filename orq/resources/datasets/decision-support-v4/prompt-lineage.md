# Decision-support-quality prompt lineage

Prompt iteration numbers describe the analytical prompt history. They are distinct from Orq's
semantic resource versions.

| Prompt | Meaning | Exact local source | Hosted Orq version | Hosted checksum |
|---|---|---|---|---|
| v1 | Original baseline rubric used for the first jury run | `jury-baseline/evaluator-prompt.txt` | Not hosted | — |
| v2 | First human-rules revision used for the diagnostic second jury | `jury-human-rules-v1/evaluator-prompt.txt` | `1.0.0` | `ca4a7cfc9e1af721` |
| v3 | Current revision derived from all 30 confirmed development labels | `prompt-v3.md` and `../../evaluators/jury/decision-support-quality.yaml` | `1.0.1` | `d76043efb73cc08c` |

Orq version `1.0.0` was created with prompt v2 on 7 September 2026. The repository sync updated the
same evaluator to prompt v3 as Orq version `1.0.1` on 8 September 2026. Both hosted versions remain
available in the evaluator's immutable version history. A reconciliation after the v3 update
returns `noop`, meaning the current repository YAML and hosted latest version match.

Prompt v3 was measured on 8 September 2026 as run `<orq-id>`. Its immutable
tracked evidence and development-only analysis are under `jury-prompt-v3/`. It remains the active
shadow version but did not pass the development alignment gate.
