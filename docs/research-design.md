# Research Design

RAPID-Learn investigates whether adaptive learning can retain useful personalisation under constrained computational resources.

## Research questions and hypotheses

The central question is whether the resource-aware hybrid policy preserves learning utility relative to full-resource operation more effectively than static, rule-only, BKT-only, or ML-only baselines. Planned hypotheses concern retention under low resources, reduced unnecessary computational cost, and higher knowledge-gap detection from uncertainty and prerequisite signals.

## Baselines and ablations

The experiment runner supports static curriculum, rule-based, BKT-only, ML-only, hybrid without resource awareness, resource-aware hybrid, and ablations removing uncertainty, misconception detection, forgetting, or prerequisite gating.

## Measures and validity

Educational measures include accuracy, learning gain, normalised gain, retention, and time to mastery. System measures include latency, memory, CPU, bandwidth, and resource-normalised utility. Threats include synthetic-learner assumptions, rule validity, curriculum scope, device heterogeneity, and the absence of real learner evidence. Current outputs are synthetic simulations only; no statistical or educational claim is made.
