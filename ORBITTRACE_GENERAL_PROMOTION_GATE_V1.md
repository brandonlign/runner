# OrbitTrace general-method promotion gate v1

Status: **FROZEN BEFORE ANY NEW SCIENTIFIC RESULT AFTER 2026-08-20 20:00 ET**

This is a goal-level promotion rule. It does **not** alter, rescue, reinterpret, or retroactively strengthen/weaken any already-frozen ticket-level PASS/FAIL gate. A ticket may pass its own development criterion and still fail this general-method promotion gate.

## 1. Scientific claim being gated

Promotion means all of the following are supportable for one exact frozen method with no target- or survey-specific retuning after method freeze:

1. It materially outperforms the strongest relevant literature baseline under symmetric tuning and identical data/evaluation budgets.
2. It transfers to independent survey data without method retuning.
3. It does not obtain that gain by sacrificing recovered-shower count or producing pathological memberships/percolation.
4. A later target-inclusive application is a clean discovery test rather than a source of method selection.

## 2. Fair comparator rule

On every labeled benchmark panel, the comparator is the **strongest relevant method after symmetric tuning on the same development information**. Published/default parameters alone are not sufficient when the literature method explicitly requires or benefits from parameter selection.

At minimum, current meteor-stream benchmarks must include ordinary HDBSCAN/EOM with its method-native minimum-cluster-size/min-samples choices tuned symmetrically under the same folds, plus any stronger relevant literature comparator available at freeze time. Sugar/DBSCAN-style comparators remain required where the repository's matched implementation is valid, but beating a weaker comparator does not compensate for losing to the strongest one.

No candidate gets more label access, tuning folds, parameter trials, or candidate-budget information than its comparator. Candidate-count truncation or top-K evaluation must be symmetric and frozen before held-out truth is opened.

## 3. Material superiority rule

A numerically positive epsilon is not enough for promotion.

For the frozen primary macro-F1 summary over the repository's common K panel (currently K = 10, 20, 30, 40 where applicable), the candidate must satisfy **both**:

- point-estimate improvement over the strongest symmetrically tuned comparator of at least **+0.020 absolute macro-F1** on the aggregate held-out benchmark; and
- a paired shower-level bootstrap 95% confidence interval for candidate-minus-comparator aggregate macro-F1 whose lower bound is **strictly greater than 0**.

The bootstrap unit is the reference shower/family, preserving all predictions for that unit together. Use 20,000 deterministic bootstrap replicates with a preregistered seed. No alternative resampling unit or interval is substituted after outcome.

In addition:

- recovered showers at the frozen F1 > 0.5 criterion may not decrease in any held-out direction used for the primary superiority claim;
- no individual held-out direction may have negative macro-F1 delta versus the strongest comparator;
- membership pathologies invalidate promotion even if rank metrics pass: a reportable candidate family cannot obtain apparent discovery success through gross percolation. The exact quantitative target-discovery membership gate must be frozen separately before any new target-inclusive reveal.

The +0.020 margin is a goal-level definition of “materially beats,” chosen prospectively to exclude the already-observed class of tiny transfer wins (~0.001–0.004 absolute) from being mislabeled as substantive superiority. It is not a post-result threshold for any future method.

## 4. Generalization rule

Development superiority alone is insufficient. After a method is frozen, it must be transferred **without method retuning** to at least one independent survey/dataset not used to choose its architecture, features, weights, thresholds, or ranking rule.

For promotion to a genuinely general method, the preferred evidentiary standard is two independent survey/data domains when available. At minimum one must be scientifically fresh for the method lineage under a repository-history freshness audit; a previously project-exposed corpus may be reported as secondary transfer evidence but cannot by itself establish pristine generalization.

The external transfer comparator is tuned only by the same symmetric rule available to the candidate. If the candidate has no tunable parameters after freeze, it remains fixed; the comparator may use only its preregistered method-native tuning information.

A failed external transfer closes that exact method for the general-method claim. Do not tune on the failed survey and retry under the same method name.

## 5. OrbitTrace blind-boundary rule

The OrbitTrace-inclusive multiscale-HDBSCAN reveal already performed in PR #1435 is **spent evidence** for all methods defined after that reveal. Its target outcome, membership size, rank, precision/recall, or any inferred failure mode may be used only for postmortem reporting, not for selecting a successor's architecture, feature set, weights, thresholds, candidate universe, or membership rule.

Therefore, a future successor may not call a replay on that same revealed target panel a new blinded validation. To support a new “final blinded target-inclusive discovery” claim, the repository must first identify and freeze a genuinely untouched target-inclusive partition/dataset (or an independently sealed target-inclusive evaluation artifact) before the successor is allowed to see its target memberships/outcome. If no such panel exists, the scientific claim must be downgraded explicitly to post-selection target application rather than blind discovery validation.

No target coordinates, historical target assignments, revealed member IDs, known target precision/recall failure, or target-region diagnostics may enter successor development.

## 6. Sequence and stopping rules

For a candidate intended for general promotion:

1. Freeze method, candidate universe, tuning budget, baselines, metrics, and ticket-level success criteria on allowed development data.
2. Execute development once. Scientific failure closes the exact method; engineering failures before truth/result may receive source-identical repairs with preserved provenance.
3. Only after development passes, freeze and execute independent transfer with no method retuning.
4. Only after the required generalization gate passes, freeze a fair symmetric literature comparison if it was not already embedded in development/transfer.
5. Only after literature superiority and generalization both pass may a genuinely untouched target-inclusive panel be opened.
6. Final target failure closes the method for the clean-discovery goal. No rescue sweep after reveal.

All negative results remain durable. No failed lineage is silently revived by renaming parameters or combining rejected variants unless a new hypothesis is scientifically distinct and motivated without using protected outcomes.

## 7. Current interpretation boundary

This file does not promote v8, recurrent-EOM, density-synchronous recurrent-EOM, multiscale HDBSCAN, R1, or any other existing method. It only defines what future evidence must clear before the repository claims the persistent general-method goal is complete.
