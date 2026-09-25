# OrbitTrace post-v46 HDB boundary inherited-evidence diagnostic v1

## Scientific role

This is a **post-v46 mechanism diagnostic only**. It does not define, evaluate, select, or authorize a successor ranking.

The motivation is fixed by the completed exposed-development history. Component-level evidence is diagnostically associated with recoverability (#1098, #1113, #1126), but three distinct frozen attempts to convert that evidence into HDB placement all failed their binding SonotaCo literature gates: v44 broad component-best placement, v45 joint-slot permutation, and v46 Pareto-frontier placement. The diagnostic asks one narrower question: **at the two already-fixed HDB literature budget boundaries, did v46 substitute a family with strong inherited component evidence but worse own-family annual utility than the exact v31 family it displaced?**

A PASS supports only that boundary inherited-evidence substitution mechanism. It does not authorize removing the entrant, keeping the outgoing family, adding a threshold, or constructing any new order. A FAIL means that this simple mechanism is insufficient. Either result is binding for this diagnostic.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation.

## Immutable sources

Pre-outcome boundary identities must be reconstructed only from truth-blind frozen artifacts:

- #1098 full HDB signal vector, result SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`, source run `31457923695`, artifact `9088724826`;
- #1126 Pareto-frontier vector SHA-256 `5ca5cab6f6a47c05d013237190ad21b247a13e22fa06988ee36dc0832a37fc02`, canonical SHA-256 `8373f4946e7f84c7c3ee0ac51167881722d4f8b78c34383400f1967824df6798`, source run `31459760333`, artifact `9089357860`;
- frozen connected-component identity SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

The exact reconstructed HDB order hashes are required to be:

- v31: `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`;
- binding v46: `80965d6e32ae772a3ebe405bd147095e00f2c9c4688160e189d9ce69f3deaf89`.

The exact v46 order reconstruction is the already-frozen v46 rule only: frontier families use their frozen `component_best_v31_percentile`; all other HDB families use their own exact-v31 percentile; sort by `(placement_key, own_v31_percentile, family_id)`. No new score is created.

## Boundary freeze before truth

Use only the two pre-existing HDB literature panel budgets:

- 2013: `B = 11`;
- 2014: `B = 9`.

For each year/budget, freeze:

- `incoming = top_B(v46) - top_B(v31)`;
- `outgoing = top_B(v31) - top_B(v46)`;
- the shared intersection;
- the incoming family’s own exact-v31 rank/percentile, frozen component ID, component-best percentile, and inherited-evidence gap `own_v31_percentile - component_best_v31_percentile`.

Require exactly one incoming and one outgoing family at each budget. Require every incoming family to originate below its fixed budget in exact v31 and to have strictly better component-best percentile than its own percentile. These identities must be serialized to `V46_BOUNDARY_INHERITANCE_FREEZE.json` **before any SonotaCo truth is downloaded**.

No alternate budget, window, top-k, threshold, identity, frontier layer, dominance rule, or comparator is allowed.

## Truth-aware diagnostic

Only after the boundary freeze is fixed, restore the same immutable exposed SonotaCo HDB truth and #950 family memberships used by the established evaluator.

For each frozen incoming/outgoing pair and its corresponding year, compute own-family annual F1 exactly as #1098 did:

1. determine the family’s fixed best label with the existing `family_truth` semantics over the two exposed years;
2. if positive, compute the two annual F1 values for that fixed label with the existing `annual_f1_for_fixed_label` implementation;
3. otherwise annual F1 is zero;
4. use only the annual F1 corresponding to that frozen panel year.

The sole interpretation gate is:

`incoming_annual_f1 < outgoing_annual_f1`

for **both** fixed HDB panel years.

PASS therefore means both v46 boundary substitutions replaced the v31 boundary family with an inherited-evidence family having strictly worse own-family annual F1 in the corresponding year. The existing `F1 > 0.5` recoverability status is reported descriptively but is not an additional fitted or searched gate.

## Explicit prohibitions

This diagnostic does not evaluate any replacement order or rescue. It does not select a successor. It does not test keeping the outgoing identities, removing the incoming identity, thresholds, component-gap cutoffs, component sizes, own-v31 cutoffs, second Pareto layers, relaxed/epsilon dominance, rank windows, budget changes, coefficients, bonuses, caps, quality/component blends, alternate component statistics, route/year exceptions, top-k, oracle corrections, or any post-result second search.

If this diagnostic passes, any future successor still requires a separately justified rule frozen before its first outcome. The boundary identities or truth labels from this diagnostic may not be hard-coded as a rescue list.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. No OrbitTrace target information or target-region events may be accessed. No MAARSY or DMS scientific access is authorized. All outputs must assert these firewall conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
