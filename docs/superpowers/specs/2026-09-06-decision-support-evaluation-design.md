# Decision-Support Evaluation Design

**Status:** Approved for implementation

## Purpose

Realign the PyData 2026 running example with the submitted abstract while moving the alignment
story away from reference-oriented answer correctness. The running example remains the analytics
agent and its fifty distinct situations. A new corpus version adds enough stakeholder and decision
context for humans and LLM judges to assess whether an answer is useful for a business decision.

The primary evaluator is `decision_support_quality`. It asks whether a response turns an analysis
into a clear, appropriately scoped input to the stakeholder's stated decision. There is no ideal
response, reference label, or hidden company knowledge for this rubric.

## Decisions

- The talk uses only the analytics agent. Podcast examples and podcast evaluation do not appear.
- Deterministic evaluation is not part of the new evaluation structure. Existing deterministic
  methods and artifacts may remain in the repository, but this work does not extend or feature
  them.
- Frozen v1, edge-v2, and v3 corpus definitions and run artifacts remain immutable historical
  evidence. The context-enriched dataset is corpus v4.
- The v4 baseline remains competent at querying and reporting data but receives no instruction to
  produce decision-ready analysis. This deliberately rudimentary communication baseline gives the
  alignment and improvement loop something real to discover.
- The agent interprets evidence by default. It recommends an action only when the user explicitly
  asks for a recommendation.
- Jury disagreement and within-model variation prioritize human annotation; they do not replace
  human judgment. The user annotates the prioritized rows and then expands coverage.
- CI regression checks and multi-agent prompt improvement appear only as future steps in the talk.
  They are not implemented by this work.

## Company Setting

The fictional company is **Sphere.com**, an Amsterdam-based, 500-person B2B wholesaler that sells
home appliances online to independent retailers, regional chains, and national retailers across the
four existing regions and fourteen countries in the dataset.

Sphere.com's catalog has four physical-appliance categories and eight products, mapped onto the
existing price bands:

- Small appliances: espresso machine and air purifier;
- Cleaning: robot vacuum and dishwasher;
- Laundry: washing machine and tumble dryer;
- Major appliances: refrigerator and heat pump.

The company grew quickly through 2024 and 2025. Ahead of annual planning, the board is questioning
the quality of that growth: whether discounts, refunds, cancellations, regional variation, and
product mix make headline revenue look healthier than the underlying business.

Recurring stakeholders are the CFO preparing the board narrative, the commercial director
allocating sales attention, category managers reviewing assortment, finance controllers
investigating refunds and margins, regional leads explaining performance, and revenue analysts
preparing supporting analysis. These roles provide context, but they are not crossed mechanically
with every scenario.

The dataset's category, product, and customer-segment values change to match this setting. Customer
segments become independent retailers, regional chains, and national retailers. The numerical
order facts, geography, dates, prices, quantities, discounts, costs, statuses, and refunds remain
deterministic. Corpus SQL, expected values, tests, documentation, and prompts that mention the old
technology catalog or segment labels must migrate together.

## Corpus v4

### Source and identity

Create `simulation-v4` from the fifty distinct analytical situations in v3. Preserve the underlying
metric, period, filter, conversation shape, executable oracle, and stable 30-dev/20-test split. Give
v4 records new IDs so they cannot be confused with the frozen v3 observations.

The v4 case definition contains a `DecisionContext` with four required fields:

- `stakeholder`: the person consuming the answer and their business role;
- `decision`: the concrete decision or preparation task the analysis supports;
- `delivery_setting`: for example a quick Slack update, executive briefing, analyst handoff, or
  audit note;
- `communication_need`: what must be foregrounded and what degree of explanation is useful.

All four fields are visible to the target agent in a natural user request. Nothing is supplied only
to the evaluator. Do not add a knowledge base, retrieval corpus, hidden target, or ideal response.

### Context quality

Each context must change what a useful answer emphasizes. Merely changing a job title or saying
"this is for a meeting" is insufficient. The fifty contexts are hand-authored per situation rather
than formed as a persona-by-scenario grid. Repeated delivery settings are allowed, but every case
retains a distinct analytical situation and a concrete decision.

Representative transformations:

1. `net-by-region-2025`: a regional lead preparing a performance review needs the weakest or most
   consequential region foregrounded, followed by the comparison.
2. `refund-share-apac`: a finance controller preparing a reconciliation note needs the denominator
   and interpretation-sensitive definitions made explicit.
3. `top-country-net`: a CFO preparing a board briefing needs the leading country and scope first,
   with technical detail demoted.
4. `missing-column`: a stakeholder facing an imminent meeting needs a plain statement that the
   requested metric is unavailable and a safe next step, not a substitute metric.
5. `ambiguous-best-product`: a decision-maker asking what to prioritize creates a genuine judgment
   about when clarification is necessary and when a bounded interpretation is useful.

### Baseline agent behavior

Keep the safety and evidence constraints that prevent fabricated data and unauthorized state
changes. Reduce output guidance to a rudimentary contract: answer the analytical question, report
the result, and include supporting SQL. Do not instruct the baseline to foreground decision impact,
adapt detail to stakeholders, interpret results for a decision, or recommend next steps.

Apply this baseline consistently to the hosted agent resource and the local system prompt so the
two execution paths do not teach different communication behavior.

## Subjective Evaluators

Replace the four reference-oriented LLM evaluator definitions in the active evaluatorq builder with
four subjective, independently alignable evaluators. Existing run artifacts and evaluator versions
remain historical evidence; no remote evaluator is mutated or deleted in this work.

All four evaluators use `pass`, `fail`, and deterministically routed `not_applicable`. They receive
the conversation, explicit decision context, tool evidence, and final response. They receive no
oracle, reference SQL, expected output, or ideal answer.

### 1. Decision-support quality — primary

Question:

> Does the response turn the analysis into a clear, appropriately scoped input to the stakeholder's
> stated decision, using sound judgment about emphasis, explanation, caveats, and next steps?

A response passes when it:

- foregrounds the result or comparison that matters to the stated decision;
- distinguishes observed evidence from interpretation;
- includes assumptions or caveats that could materially change the decision;
- gives enough explanation for the stated stakeholder and setting without obscuring the answer;
- recommends an action only when explicitly asked, and keeps that recommendation within the
  evidence.

A response fails when it materially impairs the decision by dumping results without a takeaway,
burying the relevant result in SQL or secondary detail, adding generic business advice, claiming a
cause or implication the evidence does not support, omitting decision-changing uncertainty, or
making an unsolicited prescriptive recommendation.

The evaluator does not independently recompute the answer or grade SQL semantics. A factual issue
matters only when it is visible in the supplied conversation and makes the decision support
misleading.

### 2. Assumption handling — secondary

Judge whether the agent used sound judgment about asking for clarification, proceeding with an
explicit bounded assumption, or refusing to guess. Pass when its choice is proportionate to how
much the ambiguity could change the decision; fail when it silently chooses a material definition,
asks an unnecessary blocking question, or proceeds with false certainty.

### 3. Audience-calibrated detail — secondary

Judge whether terminology, explanation depth, tone, and technical detail fit the stated stakeholder
and delivery setting. Pass and fail are based on usability, not a word-count threshold. This rubric
does not grade which business result was emphasized; that belongs to decision-support quality.

### 4. Insightfulness without overreach — secondary

Judge whether the response surfaces a useful implication or next investigative step supported by
the observed results. Fail generic filler, invented causal explanations, or recommendations that
require unavailable evidence. Mark `not_applicable` when neither the request nor its decision
context calls for interpretation beyond reporting the result.

Only `decision_support_quality` enters the first alignment cycle. The other three are defined and
testable but remain shadow evaluators until separately aligned.

## Evaluatorq Jury Contract

Build each subjective evaluator with evaluatorq's `llm_jury` using:

- three distinct judge models;
- `assignment="all"`;
- categorical labels `pass`, `fail`, and `not_applicable`;
- `aggregator="majority"`;
- `min_successful_judges=2`;
- structured output;
- three repetitions per judge for the alignment run.

Before a full run, execute a two-row smoke test. The full fifty-row run is a separately approved paid
operation of 450 judge calls: 50 rows x 3 judges x 3 repetitions.

The updated evaluatorq dependency must return the complete jury record for `assignment="all"` under
`EvaluationResult.raw_output["jury"]`. The required record includes:

- configured, successful, and failed judge counts;
- aggregate verdict and raw agreement;
- one vote per judge with model identity, aggregate verdict, representative explanation, raw
  repetition verdicts, abstention state, error, and failed-repetition count.

Repository tests must fail if the detailed jury record is absent or if repeated verdicts cannot be
joined to the corpus row and evaluator name. Do not rely on reconstructing primary experiment data
from observability spans after the run.

## Annotation and Alignment

The fifty v4 observations are the candidate annotation pool. Run the primary jury and prioritize
review using both:

1. within-model variation across the three repetitions; and
2. between-model disagreement on the same row.

Also sample several unanimous rows to look for confidently wrong consensus. Present disagreement as
an annotation accelerator, not as correctness or human alignment. The user labels the prioritized
rows first and then expands annotation coverage. Do not claim "fifty hand-reviewed examples" until
all fifty have actually received human review.

After an initial set of human labels exists, use the evaluator-alignment workflow to group disputed
boundaries, record the user's rules, rewrite the evaluator, and retest it. Agreement with humans is
reported only for the number of independently labelled rows available at that time. Cohen's kappa
requires overlapping independent human labels; jury agreement is not a substitute.

## Talk Structure Consequences

The story becomes:

1. Fifty analytics-agent observations give broad behavioral coverage but reference-oriented
   correctness does not expose the judgment problem the talk is about.
2. Context-enriched versions ask whether answers support real business decisions.
3. A rudimentary but analytically capable baseline produces answers that are often correct-looking
   and not decision-ready.
4. Repeated jury evaluation exposes both individual wobble and model disagreement.
5. Those rows focus scarce human attention; human decisions turn vague quality preferences into an
   explicit evaluator rubric.
6. Once aligned, the evaluator can become a CI regression check.
7. Later, separate agents can cluster critiques, propose prompt changes, and validate candidates;
   humans retain promotion authority.

The podcast pipeline, deterministic grader story, detailed CI implementation, and detailed
self-learning implementation are excluded.

## Verification

Implementation is accepted only when fresh checks show:

- v4 generation produces exactly fifty unique records with a stable 30-dev/20-test split;
- every v4 row has complete, agent-visible decision context and preserves its v3 analytical
  situation and oracle provenance;
- v1, edge-v2, v3, and their run artifacts are unchanged;
- the baseline prompts preserve safety/evidence behavior while containing no decision-support
  coaching;
- the active evaluator builder exposes exactly the four subjective rubric names and never projects
  oracle or reference fields into them;
- hosted evaluator YAML validation succeeds for the same four rubric contracts without applying
  remote changes;
- a fake-client jury test proves detailed per-model and per-repetition data returns for
  `assignment="all"`;
- focused tests, the full offline suite, Ruff, and `git diff --check` pass.

No live corpus generation, paid jury run, hosted-resource apply, CI workflow change, or autonomous
prompt mutation is authorized by this design.
