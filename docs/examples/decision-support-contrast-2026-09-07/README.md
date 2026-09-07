# Decision-support contrast: same question, same data, same number

Evidence for the talk's opening slide, "Two correct answers. One useful decision."

Both records are real agent runs against the Sphere v4 corpus and the deterministic
`sphere-orders-v1` DuckDB build. Neither answer is authored or edited.

- `with-decision-context.json` — the canonical v4 observation for
  `sphere-stakeholder--v4-total-gross-2025`. The prompt carries the stakeholder,
  the decision, the delivery setting, and the communication need. Judged by the
  `decision_support_quality` jury: pass, 3/3 judges, 100% raw agreement.
- `without-decision-context.json` — a rerun of the same case on 2026-09-07 with the
  decision context stripped from the first message, leaving only the analytical
  question. Not part of the canonical corpus and not jury-scored.

Both answers report $51,226,989.17 and both are analytically correct. Only the
context-carrying run labels the figure as booked rather than realized and offers the
comparison the stakeholder actually needs.

## Provenance

- Case definition: `orq/resources/datasets/simulation-cases-v4.jsonl`
- With context: `runs/v4-jury-20260907.jsonl`
- Without context: `runs/v4-nocontext-total-gross-20260907.jsonl`, produced by
  `scripts/run_simulation.py --case-id sphere-stakeholder--v4-total-gross-2025-nocontext`
  with `--evaluation-name pydata2026-v4-nocontext-contrast`. Same agent target and
  simulator model as the canonical run.
