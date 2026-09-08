# Proposed decision-support-quality prompt update

Status: proposed from 30 confirmed development labels; not applied locally or hosted.

This update sharpens the three existing human-aligned boundary rules without changing the
criterion, verdict labels, jury models, evidence mapping, or reference-free scope. It resolves the
fact-versus-proof ambiguity exposed by the human-rules-v1 jury and makes the accepted materiality
threshold operational.

## Current alignment evidence

The human-rules-v1 jury aggregates to `pass` on all 30 development cases. Against the confirmed
27-pass / three-fail human labels, that is 90% raw accuracy but zero recall on human failures,
balanced accuracy 0.50, and Cohen's kappa 0. The prompt therefore needs to improve discrimination,
not preserve headline accuracy.

## Proposed replacement

Replace the current **Human-aligned boundary rules** block and its following evaluator-scope
paragraph with:

```text
Human-aligned boundary rules:

1. Evidence validity. Check claims against the supplied conversation and tool evidence. Fail when
   that evidence materially contradicts a claim or demonstrates that it is false. Lack of
   exhaustive proof is not itself a failure: do not reject an otherwise plausible data-definition
   claim merely because the trace does not independently establish its provenance. Do not
   reconstruct hidden ground truth or import undocumented schema semantics.
2. Conversational completion. Grade the analytical step the user actually requested. The response
   may leave the broader decision open and continue the conversation by asking for a missing
   benchmark or context. Additional analysis or interpretation is required only when omitting it
   would make the requested result materially misleading. Do not require an invented materiality
   threshold, escalation rule, or unsolicited next step.
3. Conversation-level context. Evaluate the full conversation, not the latest response in
   isolation. A definition, scope, assumption, or caveat established earlier remains active and
   need not be repeated in every later response unless the response contradicts or silently
   abandons it.
4. Materiality. A visible factual issue forces a fail only when it could reasonably change the
   stakeholder's interpretation, action, or confidence in the core result. Keep minor inaccuracies
   visible in the verdict explanation, but do not turn them into a binary failure when the requested
   result and its decision meaning remain intact.

You may compare the response's claims, definitions, and direct arithmetic with visible tool
results to identify contradictions. Do not derive a separate ideal answer, grade SQL style, require
undocumented data-model knowledge, or independently recompute the analysis from hidden ground
truth.
```

## Expected effect on confirmed development cases

- `best-month-net` fails because visible aggregate evidence materially contradicts its stated
  refunded-revenue definition.
- `save-staged-emea` fails because the audit summary miscopies and falsely reconciles visible
  figures, undermining confidence in the evidence for the core result.
- `segment-then-2024-check` fails because visible refunded-row values demonstrate the material
  double deduction.
- `product-drill` passes with a critique: the requested primary rate is correct, while the small
  secondary simple-average scope discrepancy is not decision-material.
- The other 26 development cases pass.

The next validation step is an offline comparison of this proposal against the 30 confirmed human
labels. A new repeated jury run, hosted evaluator update, or promotion remains a separate action.
