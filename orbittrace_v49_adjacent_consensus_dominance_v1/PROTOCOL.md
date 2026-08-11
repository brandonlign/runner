# OrbitTrace v49 adjacent consensus-dominance correction v1

## Scientific role

Separately frozen exposed-development successor after binding v48 failure. Exact v31 remains the parent and strongest genuine method at 2/4.

The development history isolates two distinct failure mechanisms in the HDB tiny-budget ordering:

1. inherited component evidence cannot safely determine absolute placement by itself (#1136/#1139; v44/v45/v46 failures);
2. assigning a joint-positive family an absolute auxiliary promotion key creates broad order cascades even after selector refinement. The v48 order was frozen before its outcome with only 35 self-supported movers but **225/229 HDB positions changed**.

v49 therefore does not assign any family a new absolute auxiliary rank. It keeps exact v31 as the default total order and permits only a local adjacent correction when the two independently frozen auxiliary supports agree that the lower-ranked family dominates the family immediately above it.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable inputs

Use only the already-frozen truth-blind HDB signal vector from #1098:

- source run `31457923695`, artifact `9088724826`;
- artifact ZIP SHA-256 `11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978`;
- signal SHA-256 `a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07`;
- 229 HDB families;
- exact 60-family `joint_signal` population;
- immutable `quality_percentile` and `component_best_v31_percentile` for every HDB family;
- exact graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- exact component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

Also preserve as provenance only:

- #1091 binding joint-direction authorizer, run `31456963941`, artifact `9088402091`, result SHA-256 `2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842`;
- #1139 binding inheritance-gap diagnostic, run `31488131546`, artifact `9099927842`, result SHA-256 `c372b4aac0547198cb6ac4239d604fddc12fdd0f11a930ab39a1e46d01f5e461`;
- the truth-blind v48 order-freeze file from artifact `9100509632`, SHA-256 `295d2392838d841c441ce164351e426b3efbbe7be487877b4cf3f914a64c7351`, which records `225` moved HDB candidates before v48 outcome truth was loaded.

The v48 outcome itself does not define the v49 order. No v48 truth-aware candidate identities or panel labels are inputs.

## Sole v49 ordering rule

Sugar is exact v31 unchanged.

For HDB:

1. start from the complete exact-v31 HDB order, sorted by `(v31_rank, family_id)` and require ranks `1..229` exactly;
2. scan the current list from position 2 toward the end;
3. let `A` be the family at the current position and `B` the family immediately above it;
4. `A` may swap one position upward across `B` **iff** all of the following are true:
   - `A.joint_signal == true` under the exact #1098 gate;
   - `A.quality_percentile <= B.quality_percentile`;
   - `A.component_best_v31_percentile <= B.component_best_v31_percentile`;
   - at least one of those two inequalities is strict;
5. after an allowed swap, move the scan pointer back by one position (but never before position 2) so the same family may make another adjacent crossing only if it also dominates the next predecessor on both supports;
6. if no swap is allowed, advance the pointer by one;
7. stop when the pointer has passed the end of the list.

This is a deterministic adjacent Pareto-correction process. A non-joint family can never initiate an upward swap. Auxiliary evidence is used only to authorize a specific pairwise crossing; it never supplies an absolute insertion rank, coefficient, distance, threshold, or score.

The complete v49 order must be frozen before current SonotaCo outcome truth is loaded.

## Frozen truth-blind structural consequences

Using only the exact #1098 vector, the above rule has one deterministic consequence and is frozen now before outcome evaluation:

- exact-v31 HDB order SHA-256: `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d`;
- v49 HDB order SHA-256: `6344a7a4abd67698cd32d17d3183c482b7e8954f6923e0c255a04f7d231af819`;
- adjacent swaps: `35`;
- families whose final position changes: `50/229`;
- families moving upward: `20`;
- families moving downward: `30`;
- maximum upward displacement: `6` ranks;
- maximum downward displacement: `3` ranks.

These are descriptive consequences of the single frozen rule, not selected thresholds or gates. No alternate pairwise relation, scan direction, dominance dimensions, strictness convention, mover population, or swap cap was evaluated for outcome performance.

## Evaluation

Before truth, the workflow must reproduce:

- exact source/ranker pins;
- immutable #950 pretruth payload;
- exact graph/components;
- #1091 and #1098 provenance;
- #1139 mechanism provenance;
- the v48 truth-blind cascade-freeze identity;
- the exact complete v49 order and every structural count/hash above.

Only after all of those checks pass may the workflow restore the same immutable exposed SonotaCo truth used by the established development evaluator.

The evaluator must first reproduce all four exact v31 controls, then evaluate exactly one v49 order. The runtime HDB order must equal the pretruth-frozen v49 order SHA exactly. Sugar must remain byte-identical to exact v31.

PASS requires all four existing SonotaCo literature pair gates. The first technically valid outcome is binding.

## Explicit prohibitions

No absolute quality-rank placement, component-best placement, inheritance-gap placement, fixed joint-slot permutation, component representative ordering, threshold, quantile, epsilon, coefficient, interpolation, weighted score, bonus, cap, top-k, rank window, budget/year/route exception, swap-distance cap, alternate scan order, alternate dominance dimensions, OR rule, one-signal swap, alternate strictness rule, pair-specific weight, oracle identity, boundary rescue list, graph/radius/metric/component change, candidate change, feature/model/k/scaling/diversity/fusion/source-quota search, or post-result rescue is authorized.

If v49 fails, this exact adjacent two-support dominance rule is permanently closed.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
