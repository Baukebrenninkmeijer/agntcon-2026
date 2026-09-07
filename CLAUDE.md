# Repository Guidance

## Maintain the Living Work Plan

For every task that changes implementation, hosted resources, evaluation behavior, CI, architecture, delivery status, or operational reality, read and maintain [the PyData 2026 evaluation delivery plan and task log](docs/superpowers/plans/2026-09-03-project-status-and-handoff.md).

When reality changes, update the plan in the same task and commit as the change. Keep all affected workstream statuses, acceptance evidence, architecture decisions, risks or blockers, integration state, status date, changelog entry, and next actions accurate. Preserve explicit dependencies and handoffs so the next agent can continue from Git alone.

Mark work `VERIFIED` or complete only after running the relevant checks, reviewing their fresh output, and recording the evidence required by the plan's status taxonomy. Code or configuration presence by itself is not completion evidence. Keep unfinished, unintegrated, or unvalidated work `ACTIVE`, `BLOCKED`, or `NOT STARTED` as appropriate.

## Check Every Change Against the Talk's Contract

[`abstract.md`](abstract.md) is the promise made to the conference and the audience;
[`outline-manual.md`](outline-manual.md) is the structure the talk is being built to.
Together they are the contract. Before making any change to slides, narrative, running
example, evaluation scope, or supporting material, read both and state which part of the
contract the change serves.

Reject changes that do not map to something in those two files, even when the change is
individually good. A slide that is interesting but off-outline is drift, and drift is
what makes the talk run long and lose its through-line.

When a change genuinely belongs in the talk but the contract does not cover it, update
`abstract.md` or `outline-manual.md` first, in the same task, and say what was added or
dropped to make room. The 30-minute budget in the outline is fixed; new material has to
displace old material, not accumulate on top of it.

## Keep Live Credentials in the Primary Checkout

Treat the primary repository checkout's Git-ignored `.env` as the canonical
location for the project-scoped `ORQ_API_KEY` used by evaluatorq, the Orq SDK,
and application runs. A healthy OAuth session can make CLI trace reads work
while those run paths still have no API key; verify both authentication paths
independently and never infer one from the other.

Worktree-local `.env` files are ephemeral. Before closing a secondary
worktree, check whether its ignored `.env` is the only location of an active
project key. Recreate or move the required key into the primary checkout's
ignored `.env` before removal, without printing, logging, or committing it.
