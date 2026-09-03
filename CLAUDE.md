# Repository Guidance

## Maintain the Living Work Plan

For every task that changes implementation, hosted resources, evaluation behavior, CI, architecture, delivery status, or operational reality, read and maintain [the PyData 2026 evaluation delivery plan and task log](docs/superpowers/plans/2026-09-03-project-status-and-handoff.md).

When reality changes, update the plan in the same task and commit as the change. Keep all affected workstream statuses, acceptance evidence, architecture decisions, risks or blockers, integration state, status date, changelog entry, and next actions accurate. Preserve explicit dependencies and handoffs so the next agent can continue from Git alone.

Mark work `VERIFIED` or complete only after running the relevant checks, reviewing their fresh output, and recording the evidence required by the plan's status taxonomy. Code or configuration presence by itself is not completion evidence. Keep unfinished, unintegrated, or unvalidated work `ACTIVE`, `BLOCKED`, or `NOT STARTED` as appropriate.
