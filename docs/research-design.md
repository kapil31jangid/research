# Research Design

The canonical prediction metric is the selected candidate probability, accompanied by
a compact candidate summary. The legacy interaction-level prediction is retained only
for compatibility and is not populated by current candidate-level scoring. A candidate
prediction failure aborts ML scoring for the entire recommendation and records a BKT
fallback; partially predicted rankings are never reported.

RAPID-Learn investigates whether adaptive learning can retain useful personalisation under constrained computational resources.

## Research questions and hypotheses

The central question is whether the resource-aware hybrid policy preserves learning utility relative to full-resource operation more effectively than static, rule-only, BKT-only, or ML-only baselines. Planned hypotheses concern retention under low resources, reduced unnecessary computational cost, and higher knowledge-gap detection from uncertainty and prerequisite signals.

## Baselines and ablations

The experiment runner supports a state-independent static curriculum baseline,
BKT-only and BKT-plus-uncertainty conditions, pedagogical adaptation, the full system
with and without ML, and explicit ablations for uncertainty, misconceptions,
forgetting, resource awareness, offline adaptation, and ML. Switches reach the real
interaction runtime rather than post-processing pathway labels.

The simulator maintains two intentionally separate state systems. System mastery is
RAPID-Learn's estimated state; synthetic mastery is simulator ground truth used to
generate responses and apply independent learning effects. Cross-concept
recommendations update only the selected concept's synthetic state. Synthetic
misconception intensity is tracked separately and may decrease after matching
remediation, allowing a clearly labelled simulation proxy for resolution.

## Measures and validity

Educational measures include accuracy, learning gain, normalised gain, retention, and time to mastery. System measures include latency, memory, CPU, bandwidth, and resource-normalised utility. Threats include synthetic-learner assumptions, rule validity, curriculum scope, device heterogeneity, and the absence of real learner evidence. Current outputs are synthetic simulations only; no statistical or educational claim is made.

Controller records retain requested and actual adaptation paths, triggered/rejected rules, resource and offline state, optional model version/probability, fallback state, and estimated versus measured latency. These fields support auditability, not claims of classroom effectiveness.
