# Paper-to-repository consistency summary

The final manuscript was checked against the Step 8 certificate, Step 9 package, canonical aggregate CSV files, condition matrix, learner-profile configuration, and publication figures.

Verified and reflected in the paper:

- BKT, independent uncertainty, retention/forgetting, prerequisites, concept-scoped misconceptions, resource monitoring, offline resolution, candidate ranking, optional logistic regression, and complete BKT fallback.
- Simulator latent state is separated from the learner state visible to RAPID-Learn.
- Nine primary runtime conditions, five seeds, 45 isolated runs, and exactly 900,000 interactions.
- 500 learners per condition/seed, 40 interactions per learner, mastery threshold 0.80, initial system mastery 0.20, and NCERT Class 5 Mathematics pack 1.0.0.
- 10,000 percentile-bootstrap resamples at the seed-summary unit and matched within-seed comparison unit.
- Overall, ablation, resource, offline, ML, and weight-sensitivity results use certified values only.
- Figures 4 and 5 trace to the frozen canonical analysis outputs.

Important reconciliations:

- The paper no longer states or implies that Full RAPID-Learn outperformed Static overall.
- `no_ml` and `no_offline_adaptation` are described as auxiliary controls, not primary conditions.
- Resource awareness is described as implemented and behaviourally verified, but without an established outcome advantage.
- ML is described as optional, poorly calibrated in the synthetic study, and without established incremental benefit.
- Offline content availability is separated from application-shell caching, and rare cached-path use is disclosed.

No smoke-test or sensitivity-run observation is presented as a primary-suite estimate. Sensitivity outputs are used only for the explicitly labelled local robustness analysis.
