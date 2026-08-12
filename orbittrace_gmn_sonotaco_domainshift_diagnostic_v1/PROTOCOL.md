# OrbitTrace GMN–SonotaCo generic-feature domain-shift diagnostic v1

## Purpose

Diagnose, without SonotaCo shower truth or literature-comparator results, whether the 21 generic source-blind family features used by the frozen GMN ranking line have materially different distributions in target-excluded GMN 2022/2023 and the canonical label-free SonotaCo 2013/2014 seed catalogue.

This is a diagnostic only. It does not define, train, select, or promote a successor scientific ranker.

## Frozen inputs

The diagnostic uses exactly:

- the target-excluded GMN 2022/2023 hard + P19 + P20 family universe: 226 + 1,075 + 3,203 = 4,504 families;
- the canonical label-free SonotaCo 2013/2014 hard + P19 + P20 seed-family universe produced by the already-frozen portable generators: 25 + 84 + 225 = 334 families;
- the same 21 generic source-blind features used by PR #977, in their existing order and formulas;
- the existing canonical SonotaCo base rows only, with truth-bearing fields forbidden.

No SonotaCo shower truth, matched literature rows, or comparator evaluation artifact may be downloaded or used.

## Frozen measurements

For each of the 21 features, report:

- GMN q25, median, q75, and IQR;
- SonotaCo q25, median, q75, and IQR;
- two-sample Kolmogorov–Smirnov statistic overall;
- the same KS statistic separately within hard, P19, and P20 when both samples contain at least five families.

Also measure how distinguishable the two survey domains are from the complete 21-feature vector using exactly the source implementation already frozen in `run_diagnostic.py`:

- `HistGradientBoostingClassifier`;
- learning rate 0.05;
- 250 iterations;
- 31 max leaves;
- L2 regularization 1.0;
- random state 20260809;
- five deterministic folds balanced within survey-domain × generator-source strata;
- inverse-domain-size training weights within each fold;
- report out-of-fold ROC AUC and balanced accuracy overall and separately within hard/P19/P20.

These statistics are descriptive diagnostics of survey shift. They are not optimization objectives for this run.

## Interpretation boundary

The diagnostic may establish whether strong survey-domain shift exists and which already-defined feature coordinates exhibit the largest descriptive shift. It must not, in this run:

- choose a feature subset;
- choose a weighting or adaptation rule;
- choose a probability cutoff;
- choose a source quota;
- train a scientific shower-quality ranker;
- use SonotaCo truth to define a successor;
- perform a second search after seeing results.

Any successor hypothesis, if scientifically justified later, must be separately named and frozen before its own result-bearing execution.

## Firewall

- GMN protected solar-longitude exclusion remains `[20.0, 55.0]` at source construction.
- SonotaCo shower truth access: false.
- Literature-comparator evaluation: false.
- Matched comparator rows used: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- OrbitTrace target-information access: false.
- Protected target-region events accessed: false.

The already-frozen `run_diagnostic.py` is unchanged by this protocol addition; this file records the execution and interpretation boundary before any successful diagnostic result exists.
