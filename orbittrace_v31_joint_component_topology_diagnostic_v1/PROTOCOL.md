# OrbitTrace v31 joint component-topology diagnostic v1

## Scientific role

Post-v49 exposed-development mechanism diagnostic only. It does not define, evaluate, select, or authorize a successor ranking.

The completed evidence is specific:

- #1098 fixes an exact 60-family HDB joint-positive population using independent quality suppression and cross-route component opportunity;
- #1113 shows lower frozen component-best v31 percentile is strongly associated with annual recoverability inside those 60 families at both family and strict-group levels in both years;
- #1136 shows component evidence can be dangerously inherited by a weak family when the connected component is large and heterogeneous;
- #1139 independently confirms that larger own-v31 minus component-best inheritance gap is associated with nonrecoverability across the fixed 60-family population;
- v44/v45/v46 fail when raw component evidence is converted into placement, v48 fails when absolute quality promotion is used, and v49 is conservative enough to leave the HDB literature endpoints exactly at v31.

A truth-blind topology audit of the already-frozen #1098/#1072 inputs reveals one natural categorical distinction without selecting a numerical size cutoff:

- `ONE_TO_ONE`: the frozen connected component contains exactly one HDB family and exactly one Sugar family;
- `AMBIGUOUS`: every other frozen connected-component topology.

Among the exact 60 joint-positive HDB families this split is deterministically 41 `ONE_TO_ONE` and 19 `AMBIGUOUS` before any current outcome truth is loaded.

The diagnostic asks only:

> Within the exact fixed 60-family joint-positive HDB population, are families in unambiguous 1-HDB + 1-Sugar components more recoverable than families in multi-family/ambiguous components in both exposed years?

No component-size threshold, score, rank, selector, replacement, order, or literature panel is evaluated.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation.

## Immutable inputs

Use only:

1. authoritative #1098 run `31457923695`, artifact `9088724826`, ZIP SHA-256 `11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978`;
2. exact #1098 signal file `V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL.json`, SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
3. exact frozen component closure file `CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY.json`, SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
4. immutable #950 HDB family memberships from artifact `9074742322`, ZIP SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
5. the same immutable exposed HDB truth already used by the established development evaluator, restored only after the topology vector is frozen.

Require:

- 229 total HDB signal families;
- exactly 60 `joint_signal == true` families;
- exact graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- exact component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
- exactly 196 frozen connected components;
- every selected HDB family maps to exactly one frozen component;
- exactly 41 joint families have `hdbscan_member_count == 1 AND sugar_member_count == 1`;
- exactly 19 joint families are `AMBIGUOUS`.

Before truth, serialize the complete exact 60-family vector containing only family identity, exact v31 rank, component identity, HDB member count, Sugar member count, total component member count, and the binary topology class.

No #1136 boundary identity, annual recoverability label, literature budget, panel outcome, target information, MAARSY, or DMS information enters the vector.

## Truth-aware diagnostic

Only after the topology vector is frozen, restore the same immutable #950 memberships and exposed HDB truth.

For every fixed vector family, reproduce the established family truth semantics exactly:

1. derive the fixed best label with the existing `family_truth` implementation over the two exposed years;
2. if positive, compute annual F1 for that fixed label with the existing `annual_f1_for_fixed_label` implementation;
3. otherwise annual F1 is zero;
4. annual recoverability remains the already-established `annual_f1 > 0.5` criterion.

### Family-level gate

For each year separately, compare:

- recoverable fraction among all 41 fixed `ONE_TO_ONE` joint families;
- recoverable fraction among all 19 fixed `AMBIGUOUS` joint families.

Both strata must be nonempty. Family-level direction passes iff

`recoverable_fraction(ONE_TO_ONE) > recoverable_fraction(AMBIGUOUS)`.

### Diagnostic-group-level gate

Form the same strict diagnostic labels used in the established lineage: `SHOWER/<fixed best label>` for positive families and `NEG/<family_id>` otherwise.

Within each diagnostic group, choose exactly one representative by smallest exact-v31 rank, tie-broken by family ID. The group's topology class is the frozen topology class of that representative. The group is annual-recoverable iff any fixed joint family in that group has annual F1 > 0.5 in that year.

For each year separately, compare recoverable fractions among representative-`ONE_TO_ONE` groups and representative-`AMBIGUOUS` groups. Both strata must be nonempty. Group-level direction passes iff

`recoverable_fraction(rep ONE_TO_ONE) > recoverable_fraction(rep AMBIGUOUS)`.

Mixed-topology membership inside a diagnostic group is reported descriptively but does not alter the representative rule or create an exclusion.

## Binding interpretation gate

PASS requires the strict `ONE_TO_ONE > AMBIGUOUS` recoverability direction at both family and representative-group levels in **both 2013 and 2014**.

If any required stratum is empty or any one of the four strict inequalities fails, the diagnostic FAILS and this exact topology distinction is closed as the next selector mechanism. No alternate component-size bin, `<=2`/`<=3` threshold, log size, route-count ratio, entropy, component density, topology subclass, or post-result second test is allowed as rescue.

PASS supports only the mechanism statement that unambiguous 1↔1 cross-route components are a more reliable context for the already-supported joint/component evidence. PASS does not authorize a ranking, placement key, frontier filter, component-best transfer, quality transfer, replacement list, or successor order; any successor requires a separate freeze.

## Explicit prohibitions

No candidate total order, literature panel, selector, replacement rule, successor, component-size threshold, size transform, topology search, route-count ratio, component density, entropy, graph/radius/metric change, alternative component definition, quality/component score fusion, coefficient, top-k, rank window, budget/year rule, oracle identity, boundary rescue list, feature/model/k/scaling/diversity/fusion/source-quota search, or post-result second search.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
