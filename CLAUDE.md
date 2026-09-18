# Repository Guidance

## Never Rewrite `outline-manual.md`

[`outline-manual.md`](outline-manual.md) holds Bauke's own handwritten notes. Read it, quote it,
and take direction from it, but never rewrite, restructure, reformat, or "bring it up to date".
It is allowed to be terse, incomplete, and out of step with the deck; that is what a personal
scratch file looks like, and its value is that it says what the author thought, in the author's
words.

When outline material needs to be written or corrected, put it in [`outline.md`](outline.md),
which is the maintained talk outline, and leave the manual notes alone. Only edit
`outline-manual.md` when Bauke explicitly asks for that specific file to be changed.

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
