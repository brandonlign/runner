# DAG-atom Pareto-prominence v1 — binding result

## Status

**FAIL_DAG_ATOM_PARETO_PROMINENCE_V1 — CLOSED**

The first technically valid complete truth execution is binding. The exact raw common-refinement-atom candidate set plus frozen two-objective Pareto-prominence ordering fails the preregistered 17-gate promotion contract and is permanently closed.

## Frozen science

- protocol blob: `7e586325118e28536581f6b4ceaff40324635b10`
- pretruth builder blob: `441bec6a51b7629c12b5323e3e2e7305b2f7575b`
- truth evaluator blob: `b2a07da83c9fc5ba7410992ee760b9f551c92023`
- exact recurrent parent blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`
- zero-label DAG source run: `32185851992`
- DAG prelabel SHA-256: `65ead5f26026dbed74a098cc1df17d000c28705cd8fcd3af5134fd98151a0573`
- successful sparse Pareto source run: `32077260440`
- old Pareto truth SHA-256: `697118cf053154d009fad5a323c92e40bdea6d187c054a58d81b9d6abb8f4b6f`

The scientific rule was frozen before implementation and before truth. Candidate memberships were the complete exact nonempty intersections `A_ij = T_i ∩ R_j`; no atom-size filter, component contraction, union, overlap threshold, degree penalty, or learned score was permitted. Ranking reused the already-successful parameter-free Pareto-prominence logic with recurrent-parent rank and contributing-TopoModal-parent modal-prominence rank.

## Zero-label pretruth

Original staged run `32188889835` completed pretruth successfully and sealed:

- artifact `9343467987` (`orbittrace-dag-atom-pareto-prominence-v1-pretruth`);
- artifact digest `sha256:07323d69ad40e102cbdf3189d272c323de0893e32fbec361f01eec7e437281f6`;
- prelabel SHA-256 `8621c48ec179cc808b64bcd1b4a19f2af12dd38ef01ab9ae32cdc4c38dc67d7f`;
- pretruth SHA-256 `e17ace61a139598dec69243f2489fc9f8c48831c90bb2c86c1c224628fb6c169`;
- verdict `PASS_DAG_ATOM_PARETO_PROMINENCE_V1_PRETRUTH`;
- all 12 preregistered structural gates passed.

Thus the candidate catalogue, atom identities/memberships, ranking, equal budgets, comparators, and firewall were immutable before the binding truth result.

## Technical no-result and Repair 01

The truth job in run `32188889835` is preserved as a technical no-result. It failed on the first successor metric call with:

`KeyError: 'family_id'`

The legacy parent `metrics()` wrapper requires a `family_id` field when constructing a temporary annual row, but the downstream truth function uses only `event_ids`. No successor metric, scale aggregate, promotion gate, verdict, or result file existed. Truth labels had been loaded, and one d=64 comparator metric was computed in memory immediately before the exception, but no value was printed, persisted, or used for method construction.

`TECHNICAL_REPAIR_01.md` and `TECHNICAL_REPAIR_01_FREEZE.json` preserve the repair chronology. The sole compatibility repair injects deterministic `family_id = 'DAGATOM1:' + atom_hash` only when a frozen DAG atom lacks the legacy identifier. It does not change any event membership, rank, comparator, budget, metric, gate, or access policy.

## Binding execution

- clean retry run: `32189372993`
- execution commit: `1e153d65333a44fec10d35a61068ffe037c3e8c4`
- artifact: `9343696639` (`orbittrace-dag-atom-pareto-prominence-v1-binding-repair01`)
- artifact digest: `sha256:ada957a3e1550caeca16f83ccfea77c3a529cd7559e3cfa9bda97d66223b745b`
- result SHA-256: `d4e11a82ca54bb754b229f085744133859f7174d15a609d39036fd1af4300064`
- repair token: `TECHNICAL_REPAIR_01_FAMILY_ID_ONLY`
- historical d=128/d=1024 Pareto comparator reproduced exactly before accepting the result: **PASS**.

The workflow completed source audit, sealed-pretruth rebind, historical-comparator rebind, binding truth evaluation, result/firewall enforcement, and artifact upload successfully.

## Binding scale results

### d=64 — versus exact recurrent-EOM

Comparator:

- pooled qualified total: `153`
- mean zero-filled eligible-query MRR: `0.04064735821202093`
- mean top-100 dominant precision: `0.3254283129943979`
- mean fragmentation: `1.0`
- recovered@25 / @50 / @100 / @500 totals: `115 / 148 / 153 / 153`

DAG-atom successor:

- pooled qualified total: **`185`** (`+32`)
- mean zero-filled eligible-query MRR: **`0.03851358495146374`** (regression)
- mean top-100 dominant precision: **`0.4624144734944088`** (large improvement)
- mean fragmentation: `1.0`
- recovered@25 / @50 / @100 / @500 totals: `98 / 170 / 185 / 185`
- qualified matches nonlower in `7/8` annual panels.

Five of six dense gates passed. The sole dense failure was zero-filled MRR. The pattern is important: atomization substantially improves eventual equal-budget recovery and purity, but shifts some recoveries later in the prefix (`@25` falls while `@50/@100` rise), so the frozen early-ranking gate fails.

### d=128 — versus already-successful recurrent–TopoModal Pareto-prominence v1

Comparator:

- pooled qualified total: `127`
- mean zero-filled MRR: `0.06716051462349848`
- mean precision: `0.5084922365404909`
- mean fragmentation: `1.0`

DAG-atom successor:

- pooled qualified total: `125`
- mean zero-filled MRR: `0.06670142141174568`
- mean precision: `0.5170094010514626`
- mean fragmentation: `1.0`
- qualified matches nonlower in `7/8` annual panels.

The successor improves mean precision slightly but loses two pooled qualified recoveries and regresses zero-filled MRR. The frozen d=128 no-regression contract therefore fails.

### d=1024 — versus already-successful recurrent–TopoModal Pareto-prominence v1

Comparator:

- pooled qualified total: `30`
- mean zero-filled MRR: `0.4025038973922902`
- mean precision: `0.5892922679172679`
- mean fragmentation: `1.0`

DAG-atom successor:

- pooled qualified total: `28`
- mean zero-filled MRR: `0.39393246882086164`
- mean precision: `0.5865144901394901`
- mean fragmentation: `1.0`
- qualified matches nonlower in `6/8` annual panels.

Qualified total, zero-filled MRR, and precision all regress slightly. No sparse added-value condition is met.

## Exact gate outcome

Passed:

- d64 qualified total nonlower;
- d64 qualified nonlower in at least 6/8 panels;
- d64 precision nonlower;
- d64 fragmentation nonhigher;
- d64 strict material effect;
- d128 qualified nonlower in at least 6/8 panels;
- d128 precision nonlower;
- d128 fragmentation nonhigher;
- d1024 qualified nonlower in at least 6/8 panels;
- d1024 fragmentation nonhigher.

Failed:

- d64 zero-filled MRR nonlower;
- d128 qualified total nonlower;
- d128 zero-filled MRR nonlower;
- d1024 qualified total nonlower;
- d1024 zero-filled MRR nonlower;
- d1024 precision nonlower;
- strict sparse added-value beyond the already-successful Pareto predecessor.

Because all 17 gates were mandatory, the binding verdict is `FAIL_DAG_ATOM_PARETO_PROMINENCE_V1`.

## Interpretation

The positive zero-label DAG result remains valid: the exact cross-hierarchy common refinement is genuinely more stable under thinning than either parent representation. This truth result shows that **using every common-refinement atom directly as a detector candidate is too fine-grained for the frozen ranking contract**.

At d=64, the representation is scientifically promising in one narrow sense: it recovers substantially more qualified showers and raises purity while maintaining fragmentation. Its weakness is ordering/partition granularity at the very front of the catalogue. At d=128/d=1024, where the earlier uniquely corroborated full-TopoModal-child Pareto detector was already strong, splitting those useful children into smaller intersection atoms loses a small amount of recovery and MRR.

Therefore structural stability of a refinement does not imply that the refinement itself is the optimal reportable cluster granularity. The exact raw-atom detector is closed; this result must not be used to choose an atom-size cutoff, merge rule, degree penalty, component contraction, rank weight, or other rescue within this family.

## Closure

The exact DAG-atom + two-objective Pareto-prominence detector is permanently closed. No result-informed rescue is authorized through:

- atom-size thresholds, including `>=4` filtering;
- connected-component unions/contractions;
- restoring full TopoModal or recurrent memberships inside this method;
- overlap/Jaccard thresholds;
- degree penalties or parent-set penalties;
- weighted/Borda/geometric-mean/hypervolume/epsilon/crowding-distance rank fusion;
- per-parent quotas or round-robin scheduling;
- denominator-, bucket-, year-, or budget-specific exceptions;
- K, truth-metric, or gate changes;
- learned reranking;
- post-result parameter search.

Any future detector must be scientifically distinct and separately justified/frozen rather than a repair of this failed method.

## Firewall

The binding run used only the authorized target-excluded GMN development truth. Protected `[20°,55°]`, OrbitTrace target identity/events/orbital information, SonotaCo, ASFN/EFN event-level data, AMOS, MAARSY, and DMS remained inaccessible. No post-result parameter selection was performed.
