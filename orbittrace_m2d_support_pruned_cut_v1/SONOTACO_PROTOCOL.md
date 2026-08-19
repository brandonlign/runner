# M2D support-pruned cut v1 — SonotaCo transfer protocol

## Question

Does the already-frozen support-pruned TopoModal cut preserve the existing M2D advantage over symmetrically tuned HDBSCAN on the exact 29,246-event SonotaCo 2013+2014 common universe, while reducing oversized candidate memberships?

This is a no-tuning transfer test. The support-pruned rule was frozen and passed target-excluded GMN development before this SonotaCo transfer stage.

## Fixed method

No method parameter changes are authorized.

- physical embedding: frozen TopoModal implementation;
- graph radius: 1.0;
- minimum support: 4;
- cut rule: recurse into the reportable child and discard an immediate sibling with support <4; recurse both when both are reportable; retain the parent only when both immediate children are sub-support but the parent itself has support >=4;
- M2D formula and exact C++ scorer: unchanged from the binding SonotaCo M2D result;
- ranking: M2D descending, modal contrast descending, family hash ascending;
- evaluation budgets: K = 10, 20, 30, 40;
- common universe: exact symmetric benchmark intersection, 15,988 events in 2013 and 13,258 in 2014, pooled 29,246.

## Baselines frozen before execution

Tuned HDBSCAN from symmetric benchmark v2:

- mean K10/20/30/40 macro-F1: 0.345475559012312;
- K40 macro-F1: 0.46086713246967964;
- recovered@40: 52;
- native macro-F1: 0.4762894120871253.

Existing support-resolved M2D on the same common universe:

- mean K10/20/30/40 macro-F1: 0.35364538749003405;
- K40 macro-F1: 0.5012446318461822;
- recovered@40: 58;
- native macro-F1: 0.7266723655790133.

Existing baseline support catalogue:

- candidates: 888;
- mean member count: 23.594594594594593;
- p90 member count: 27;
- maximum member count: 4,070.

## Firewall and execution order

1. Build the complete support-pruned candidate catalogue using only the label-free common-row artifact.
2. Record memberships, candidate count, coverage, discarded sub-support events, and size diagnostics.
3. Freeze and hash that candidate pretruth artifact before any SonotaCo shower-truth artifact is downloaded.
4. Only then compute exact M2D scores and evaluate against the already-frozen truth/evaluator.

Candidate generation and M2D ranking must not use shower labels. No candidate filtering, size cap, threshold sweep, reranking, or parameter change is allowed after truth is opened.

## Promotion gates

Support-pruned v1 replaces baseline M2D for the fair SonotaCo benchmark only if all gates pass:

1. mean K10/20/30/40 macro-F1 is >= baseline M2D 0.35364538749003405;
2. K40 macro-F1 is >= baseline M2D 0.5012446318461822;
3. recovered@40 is >= baseline M2D 58;
4. native macro-F1 is >= baseline M2D 0.7266723655790133;
5. it therefore also remains strictly above tuned HDBSCAN on mean curve F1 and K40 F1, with recovered@40 >=52;
6. mean candidate member count is strictly lower than baseline support-resolved M2D;
7. p90 candidate member count is no higher than baseline;
8. maximum candidate member count is strictly lower than baseline 4,070;
9. the support-pruning mechanism is active (at least one sub-support event is discarded);
10. candidate generation/ranking remains label-free and there is no post-result parameter search.

Failure freezes this exact SonotaCo transfer as a negative result. No rescue sweep is authorized from the same truth.

## OrbitTrace follow-up

Only if this exact frozen method passes the SonotaCo transfer gates may it be applied to the already-revealed GMN 2022+2023 OrbitTrace case to characterize whether the former rank-84 / 1,814-member family becomes cleaner. Because OrbitTrace has already been revealed, that follow-up is post-reveal characterization, not a new blind rediscovery.