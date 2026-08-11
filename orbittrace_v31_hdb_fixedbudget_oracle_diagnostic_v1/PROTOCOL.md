# OrbitTrace current-HDB fixed-budget oracle diagnostic v1

## Role
Truth-aware post-result diagnostic only. It defines no deployable ranking rule. After #1040/#1043 ruled out representative choice as sufficient, #1046 showed many recoverable HDB shower labels are stranded below v31's tiny budgets, and #1049 showed frozen radius-1 graph surfacing does not recover most of them. This diagnostic asks whether the **current immutable #950 HDB candidate universe itself has enough joint budget-level headroom to beat HDBSCAN** if label-set selection were perfect.

## Immutable universe and evaluator
Use the exact #950 HDB route family IDs and memberships. For each year, retain the unchanged eligible truth showers (>=4 truth events) and compute the exact annual F1 matrix between every eligible truth label and every fixed candidate family that overlaps that year's truth universe. Candidate memberships are not changed.

Use the frozen HDBSCAN candidate budget and literature summary from the immutable truth/evaluation package:
- 2013 budget 11, literature macro-F1 0.16813025050497152, recovered F1>0.5 count 10;
- 2014 budget 9, literature macro-F1 0.15689595582646423, recovered count 9.

## Oracle optimization
For each year solve two binary cardinality-constrained one-to-one matching problems over label-candidate edges:

1. `max_recovery_oracle`: maximize the number of selected edges with F1>0.5, with each label used at most once, each candidate used at most once, and at most the frozen budget selected.
2. `literature_recovery_constrained_macro_oracle`: require at least the literature recovered count, then maximize total F1 subject to the same one-to-one and budget constraints.

The second oracle's macro-F1 is total selected F1 divided by the full number of eligible truth showers, exactly matching the existing macro denominator. Unused budget slots are equivalent to zero-F1 output and therefore do not affect the metric.

Optimization uses `scipy.optimize.milp` with binary variables and the exact fixed F1 matrix. No candidate, label, threshold, budget, objective weight, or solver parameter is searched from the result.

## Outputs
Report feasibility, maximum recovery count, recovery-constrained maximum macro-F1, whether the fixed universe can in principle satisfy the exact HDBSCAN pairwise superiority gate, and the oracle-selected label/family/F1 pairs. Also report how many oracle-selected families lie inside exact v31's frozen top-budget, top-2x-budget, and top-5x-budget fused order; these are descriptive diagnostics only.

## Prohibitions
No oracle selection may be promoted or used as a ranking rule. No new score, cutoff, candidate, membership, feature, graph transform, model, metric, k, diversity/fusion rule, source quota, or parameter search is authorized. Any successor inspired by this ceiling must be separately frozen. SonotaCo remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar longitude 20-55 degrees remain inaccessible.
