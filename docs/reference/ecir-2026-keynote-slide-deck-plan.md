# Keynote Slide Deck Plan: Evaluating Generative AI & Agentic Systems

## Context
Keynote for Text2Story 2026 (March 29, Delft). Audience: PhDs and human annotators. Goal: teach evaluation of generative AI progressively -- from manual annotation fundamentals to cutting-edge prompt learning with RL. The talk should resonate with annotators by showing how LLMs *empower* (not replace) them, and with researchers by grounding everything in academic rigor.

---

## Critique of Current Storyline (notes.md)

**Strengths:**
- The analogy of treating LLM judges like Mechanical Turk workers is excellent -- it grounds the concept for annotators
- The progression from manual annotation -> LLM-as-a-judge -> alignment -> prompt optimization is sound
- Good practical advice (50-200 samples, panel of judges, don't self-evaluate)

**Weaknesses to address:**
1. **Missing foundation** -- jumps too quickly into ground truth datasets without establishing *why* evaluation matters and what makes generative output hard to evaluate. PhDs need the conceptual framing first.
2. **Criteria drift is absent** -- the most important academic finding (Shankar et al., CHI 2024) is that you *cannot* fully define evaluation criteria before seeing outputs. This should be a central theme.
3. **No decision framework** -- when to use direct scoring vs. pairwise vs. reference-based? The Eugene Yan decision tree fills this gap perfectly.
4. **Guardrails vs. evaluators distinction missing** -- important for the audience to understand the different roles.
5. **The "panel of judges" section** comes too late and feels disconnected -- it should flow naturally from the bias discussion within alignment.
6. **Prompt learning section is underdeveloped** -- needs to explain *how* English feedback becomes optimization signal.
7. **No concrete running example** -- a single example threaded through the talk would make it far more digestible.

---

## Proposed Slide Deck Structure

### Act 1: Foundations (Slides 1-8)
*"What are we even evaluating, and why is it hard?"*

**1. Title Slide**
- "Evaluating Generative AI & Agentic Systems: From Human Annotation to Automated Judges"
- Arian Pasquali, Orq.ai -- Text2Story 2026

**2. The Evaluation Problem**
- An LLM will always answer the same question in different ways
- The subjective nature of generative answers makes evaluation fundamentally different from classification
- Slide visual: same question, 3 different valid answers

**3. Running Example Introduction**
- Introduce a story summarization task (ties to Text2Story!)
- Show a source narrative and 2-3 candidate summaries of varying quality
- This example threads through the entire talk

**4. What Makes a "Good" Answer?**
- Too long? Too short? Hallucinating? Correct citations? Appropriate tone? Correct format?
- Key insight: these criteria feel obvious but are surprisingly hard to agree on
- Reference: Shankar et al. (2024) -- criteria drift

**5. The Evolution of Annotation**
- Traditional ML: thousands of labels
- Transfer learning: hundreds
- LLMs: few-shot, even zero-shot
- Visual: timeline/funnel showing decreasing annotation needs

**6. Evaluation Approaches: A Decision Framework**
- **Use Eugene Yan's decision tree diagram**
- Direct scoring (objective tasks: factuality, toxicity)
- Pairwise comparison (subjective tasks: tone, coherence)
- Reference-based (gold standard comparison)
- Key point: these are NOT interchangeable

**7. Choosing Metrics**
- Classification metrics (precision, recall, F1) -- for binary tasks
- Correlation metrics (Cohen's kappa, Kendall's tau, Spearman's rho)
- When to use which -- Cohen's kappa for categorical, Kendall's/Spearman's for ordinal
- Practical advice: prefer binary outputs + classification metrics (more actionable)

**8. Evaluators vs. Guardrails**
- Evaluators: async, post-generation, quality assessment (seconds-minutes)
- Guardrails: inline, runtime, safety filters (milliseconds)
- Different tools for different jobs
- Reference: LangChain readiness checklist (Phase 4)

---

### Act 2: Manual Evaluation & Annotation (Slides 9-14)
*"Start with humans. Always."*

**9. Ground Truth: The Ugly Truth**
- Majority of projects don't have usable data
- Two options: (1) build and collect logs, (2) find existing signals + synthetic expansion
- Anti-pattern: "Hey ChatGPT, generate 10 ground truth samples" (no diversity, not grounded)

**10. Building Good Synthetic Datasets**
- Take existing knowledge bases as context
- Generate question-answer pairs with diversity dimensions: difficulty, topics, user types, scenarios
- Domain expert validates usable pairs
- Quality over quantity: 20-50 hand-reviewed > hundreds unverified (LangChain)

**11. Annotation Guidelines**
- How does a human decide if an answer is good?
- Combine multiple annotators -> measure inter-rater agreement
- Low agreement = unclear guidelines -> iterate
- A few dozen examples might be enough
- Show the running example: 3 annotators scoring the story summaries

**12. The Mechanical Turk Analogy**
- How do we trust outsourced annotation?
  - Multiple annotators to reduce bias
  - Sufficient samples for statistical significance
  - Split dataset: small expert-annotated portion to validate outsourced work
- This is exactly how we should think about LLM annotators

**13. Manual LLM-as-a-Judge: Just Prompting**
- Before any framework: just prompt an LLM to evaluate
- Show a concrete prompt evaluating the story summary example
- Binary pass/fail with written critique (not 1-5 scales!)
- Reference: Hamel Husain -- "the real value comes from carefully examining your data"

**14. Why Binary > Likert Scales**
- Binary forces clarity, avoids false precision
- Faster, more accurate, lower cognitive load (DoorDash, Llama 2 paper)
- Classification metrics become directly applicable
- Critiques capture the nuance that scales pretend to capture

---

### Act 3: Human-LLM Alignment (Slides 15-21)
*"How do we trust the machine annotator?"*

**15. Criteria Drift: You Can't Pre-Define Everything**
- Shankar et al. (CHI 2024, arxiv 2404.12272): "It is impossible to completely determine evaluation criteria prior to human judging of LLM outputs"
- Circular dependency: need criteria to grade, but grading reveals criteria
- Implication: evaluation is inherently iterative
- This is the academic heart of the talk

**16. The Critique Shadowing Process (Hamel Husain)**
- Step 1: Find the domain expert (1-2 people)
- Step 2: Create diverse dataset (features x scenarios x personas)
- Step 3: Domain expert makes pass/fail + detailed critiques
- Step 4: Fix obvious errors, re-evaluate
- Step 5: Build LLM judge iteratively -- compare, refine, converge
- Visual: the iterative loop diagram

**17. Alignment Workflow**
- Human annotates a small dataset (few dozen)
- Split into dev/test (like the old times!)
- Measure LLM-human agreement
- Target: LLM-human correlation matches human-human correlation
- Show metrics on the running example

**18. What "Aligned" Looks Like**
- >90% agreement between LLM judge and domain expert
- Precision AND recall matter (not just raw agreement)
- Confusion matrix: TP/FP/TN/FN
- Once aligned -> trust the LLM to annotate at scale

**19. Mitigating Bias: Panel of Judges**
- Same principle as multiple human annotators
- 3 models from different providers (mitigate training bias, perplexity bias, RLHF bias)
- Majority vote (discrete) or average (numerical)
- Anti-pattern: never evaluate a model's output with the same model
- Reference: PoLL paper -- 3 smaller judges > 1 GPT-4

**20. Statistical Rigor**
- Minimum 50 annotated samples
- Ideally ~200 per data segment
- Confidence intervals before declaring improvement
- Non-determinism: pass@k and pass^k metrics (LangChain)

**21. The AlignEval Tool (Eugene Yan)**
- Practical implementation of these principles
- Upload data -> label (binary) -> evaluate LLM judge -> optimize
- After 20 labels: evaluation mode unlocks
- 50-100 labels recommended
- Show the tool interface / workflow diagram

---

### Act 4: Automation & Optimization (Slides 22-27)
*"From manual iteration to systematic improvement"*

**22. From Manual to Automated: The Eval Pipeline**
- Offline evals (pre-deployment, curated datasets)
- Online evals (continuous, production traces)
- Ad-hoc evals (exploratory, ingested traces)
- CI/CD integration: code-based graders in CI, LLM judges in preview/prod

**23. Error Analysis: Where 60-80% of Effort Should Go**
- Open-coding methodology: gather failures, review without pre-categorization, build taxonomy
- Root cause framework: prompt problem, tool design problem, model limitation, unknown
- Real example: Witan Labs -- single extraction bug moved benchmark from 50% to 73%
- Reference: LangChain Phase 1

**24. Prompt Optimization**
- The annotation guideline *becomes* the LLM judge prompt
- Iterating on this prompt = iterating on evaluation quality
- Manual prompt refinement based on disagreement patterns
- Decompose: 5 specialized evaluators > 1 "correctness" evaluator

**25. Prompt Learning: RL with English Feedback (Arize)**
- Core idea: replace gradient-based updates with natural language feedback
- Each explanation is "information-rich" -- learn from individual examples
- The 4-phase loop:
  1. Evaluation -> pass/fail + critique
  2. Explanation generation
  3. Metaprompt processes critiques -> add/merge/rewrite/expire instructions
  4. Instructions integrated into prompt
- Visual: the feedback loop architecture diagram

**26. Prompt Learning Results**
- Instruction learning: 0% -> 100% (10 rules, 5 loops)
- Big Bench Hard: ~10% improvement on saturated benchmark
- 10-100x faster than current ecosystem
- Counter-intuitive: training scores can drop while test improves

**27. The Future: Continuous Self-Improving Evaluation**
- Long-lived agents with evolving policies
- Production flywheel: failures -> dataset -> eval improvement -> better agent
- Human effort naturally decreases as systems improve (but never reaches zero)
- Hamel: "Never eliminate humans completely -- LLMs must align to something"

---

### Act 5: Closing (Slides 28-30)

**28. Key Takeaways**
1. Start simple: manual review of 20-50 examples before building infrastructure
2. Binary pass/fail + written critiques > complex scoring rubrics
3. Criteria drift is real -- evaluation is iterative, not upfront
4. Align LLM judges to humans the same way you'd validate outsourced annotators
5. Prompt learning turns evaluation feedback into optimization signal

**29. The Annotator's New Role**
- Message to the audience: LLMs don't replace annotators -- they amplify them
- Annotators become calibrators, validators, domain experts
- The human-in-the-loop shifts from labeling everything to validating the judge
- Fewer labels, higher impact

**30. Thank You + References**
- Key references:
  - Shankar et al. (2024) "Who Validates the Validators?" -- CHI 2024
  - Hamel Husain -- "Creating an LLM-as-a-Judge Evaluation System"
  - Eugene Yan -- AlignEval
  - LangChain -- Agent Evaluation Readiness Checklist
  - Arize -- Prompt Learning with English Feedback

---

## Diagrams & Visuals to Include from References

| Slide | Visual | Source |
|-------|--------|--------|
| 6 | Decision tree: objective/subjective -> scoring method -> metrics | Eugene Yan |
| 7 | Diagnostic plots for classification tasks | Eugene Yan's AlignEval post |
| 5 | Timeline of annotation evolution | Custom (based on notes.md) |
| 16 | Critique shadowing iterative loop | Hamel Husain blog |
| 22 | CI/CD eval pipeline flow | LangChain readiness checklist |
| 25 | Prompt learning feedback loop architecture | Arize blog |
| 26 | Results table (instruction learning + BBH) | Arize blog |

---

## Running Example Thread

**Story summarization task** (fitting for Text2Story):
- Source: a news narrative (3-4 paragraphs)
- Candidate summaries: Good, Mediocre (too long, misses key point), Bad (hallucinated facts)
- Thread through: manual eval -> annotation guidelines -> LLM-as-a-judge prompt -> alignment measurement -> prompt optimization

This single example grounds every concept and lets the audience build intuition incrementally.

---

## Delivery Notes

- **Estimated slides**: ~30 (adjust for time slot)
- **Pacing**: Acts 1-2 should take ~40% of time (foundation matters for this audience), Acts 3-4 ~45%, Act 5 ~15%
- **Audience engagement**: the Mechanical Turk analogy is your bridge -- PhDs who've done annotation will immediately connect
- **Academic credibility**: Shankar et al. (CHI 2024) as the theoretical anchor; practical tools (AlignEval, Arize) as applied demonstrations
