Evaluating Agents at Scale: From 50 Examples to a Production Flywheel
LLM agents are reaching production faster than teams can evaluate them. A data-analysis agent that runs the right query but reports the wrong number, or returns the right number via a trajectory full of fabricated tool calls, passes superficial testing and fails in production.

This talk walks through evaluating such an agent end-to-end. Our running example: a data-analysis agent answering questions over a business dataset. We show how to grade three dimensions that agent evaluation requires and single-shot LLM evaluation ignores: final response, trajectory, and state changes.

We cover the full lifecycle:

Bootstrapping evaluation from 50 hand-reviewed examples when you have no labels.
Aligning an LLM-as-a-judge to human judgment with the same rigor you'd apply to outsourced annotators: dev/test splits, inter-rater agreement, Cohen's kappa.
Scaling to continuous online evaluation with CI integration, error analysis, and prompt optimization driven by natural-language feedback.
We also cover what we got wrong in earlier iterations and what we'd do differently today.

Attendees will leave with a process they can run on their own agent next week, and a clear rule for when to trust an automated judge at scale, and when to stop.

Why this talk
Building agents is easy; knowing whether they work is not. Most teams shipping LLM agents evaluate with vibes-based spot-checking or reach for academic benchmarks that don't reflect their workload. This talk gives you a different starting point: a methodology that has emerged from working on production agents over the last two years.

Agents break classical ML evaluation in several ways at once. Outputs are non-deterministic across multiple tool calls, trajectories branch, state mutates in external systems that must be checked rather than inferred, and "correctness" is judged along multiple axes simultaneously.

What does work is an iterative, human-in-the-loop process that looks a lot like how outsourced annotators used to be validated on Mechanical Turk, applied to LLM judges.

Running example
Throughout the talk we evaluate a data-analysis agent answering questions like "what's month-over-month revenue growth for EMEA in Q3?" Failure modes we grade against include wrong queries, right queries with wrong aggregations, hallucinated numbers reported without actually running anything, correct answers reached via invalid paths, and multi-turn context loss.

Outline (30 minutes, including 5 min Q&A)

The evaluation gap (3 min) — why agents break classical evaluation.

Start with humans, not infrastructure (5 min) — bootstrapping from ~50 hand-reviewed examples, binary pass/fail with written critiques, why this beats scored rubrics.

Align an LLM-as-a-judge (7 min) — treat the judge like a model you validate. Dev/test split applied to evaluation itself. Panel-of-judges to mitigate bias. A short live walkthrough.

Agent-specific evaluation (5 min) — three levels (single-step, full-turn, multi-turn) and three dimensions to grade (final response, trajectory, state changes). Handling non-determinism at scale.

Scaling: offline, online, continuous (4 min) — CI integration, error analysis as the dominant time spend, and a brief look at automated prompt optimization via natural-language feedback.

Takeaways and Q&A (6 min)

What you'll take away
A concrete process to bootstrap agent evaluation this week with ~50 examples and no ML infrastructure.
The alignment recipe for an LLM judge you can actually trust at scale.
How to evaluate trajectory and state, not just the final output.
A CI/production pattern for continuous evaluation.
Who this is for
Intermediate Python practitioners building or operating LLM agents in production. Not a "what is an agent" introductory talk.

What this talk is not
A product demo. A survey of benchmarks. An academic tour of the LLM-evaluation literature. The patterns work with any LLM SDK and any test runner.

Bauke  Brenninkmeijer
