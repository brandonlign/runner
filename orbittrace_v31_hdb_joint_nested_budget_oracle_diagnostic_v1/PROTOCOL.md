# OrbitTrace v31 HDB joint nested-budget oracle diagnostic v1

## Scientific role

Post-result exposed-SonotaCo truth-aware oracle diagnostic only. This formalizes a joint-feasibility question after #1050/#1053 showed that the fixed 229-family HDB universe can beat HDBSCAN separately in 2013 (budget 11) and 2014 (budget 9). A deployed method, however, produces one total order, so its top-9 set must be a subset of its top-11 set.

An exploratory calculation already indicated that a jointly passing nested set exists. Therefore this diagnostic is **provenance formalization of an already-observed result, not independent confirmation or a preregistered discovery**. It may sharpen feasibility but cannot select a deployable rule.

## Immutable inputs

- Exact fixed HDB family memberships from immutable #950 pretruth payload.
- Exact exposed SonotaCo 2013/2014 truth and evaluator definitions already frozen in the development benchmark.
- Exact v31 top-11/top-9 lists and literature controls from authoritative #1053 artifact/run. The #1053 artifact identity must be verified before use.

No candidate generation, membership, evaluator, budget, truth definition, or v31 order changes are allowed.

## Joint nested feasibility problem

Let `x9_j` indicate membership of family `j` in the common-order top 9 and `x11_j` membership in top 11.

Require:

- exactly 9 top-9 families;
- exactly 11 top-11 families;
- `x9_j <= x11_j` for every family;
- separate one-to-one annual shower↔candidate assignments using the unchanged annual F1 matrices;
- 2014 assignment uses only top-9 families and must have macro-F1 strictly greater than the frozen HDBSCAN 2014 comparator and at least its recovered `F1>0.5` count;
- 2013 assignment uses only top-11 families and must have macro-F1 strictly greater than the frozen HDBSCAN 2013 comparator and at least its recovered `F1>0.5` count.

The MILP assignment is only a feasibility device. Any selected nested set must then pass the **unchanged exact evaluator** in both years; otherwise the diagnostic fails closed.

## Minimum-correction oracle

Use two deterministic stages:

1. Among all jointly feasible nested sets, maximize overlap with exact v31's top 9 plus overlap with exact v31's top 11. Because cardinalities are fixed, this minimizes total slot substitutions relative to the two relevant v31 prefixes.
2. Hold that maximum overlap exactly fixed and maximize the sum of assigned annual F1 across both years. Stable family-order coefficients may be used only at machine-epsilon scale for deterministic tie resolution and must not alter the primary overlap/F1 objectives.

Report:

- whether any joint nested set can clear both HDB gates;
- exact evaluator metrics for the selected top 9 and top 11;
- overlap with v31 at each budget;
- number of replacements at each budget;
- incoming/outgoing family IDs and strict truth groups for diagnostic reporting only;
- number of distinct incoming strict groups across the nested correction.

## Interpretation boundary

A PASS proves only that one common fixed-universe ordering can in principle beat both HDB literature panels simultaneously. If the minimum correction remains small, the residual problem is genuinely a small common-order shower-group selection error rather than incompatible annual objectives.

All oracle identities, truth groups, annual F1 values, and replacement sets are non-promotable. They may not be hard-coded, used as target-region rules, or used directly to choose a successor. Any truth-free successor still requires a separate scientific freeze before its first valid result.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- No feature/model/rank/threshold/fusion/source-quota/parameter search is performed.
- No deployable selector or successor is evaluated.
