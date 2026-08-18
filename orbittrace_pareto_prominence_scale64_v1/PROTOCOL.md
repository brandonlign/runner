# OrbitTrace Pareto-prominence scale-64 v1 — frozen translation protocol

## Status

**FROZEN BEFORE IMPLEMENTATION, BEFORE ANY D=64 ZERO-LABEL OUTCOME, AND BEFORE ANY D=64 SHOWER-TRUTH OUTCOME.**

This is the single authorized scale-translation stage following the binding 10/10 PASS of recurrent–TopoModal Pareto-prominence v1. It does not change that ranking mechanism. It asks whether the same architecture survives at a substantially denser, previously untested target-excluded GMN scale.

## Immutable positive source mechanism

Parent scientific method: recurrent–TopoModal Pareto-prominence v1.

- scientific branch: `agent/orbittrace-recurrent-topomodal-pareto-prominence-v1`
- protocol blob: `b3979c133c9e3b5e4611795f5a638a85c5695eb1`
- Pareto builder blob: `8add0107ca4376fa9e62b35713971456a5d6cfe1`
- truth evaluator blob: `eddb7bef439152e63fcc025ca81b35189b88a33b`
- binding run: `32077197154`
- truth artifact: `9303967256`, digest `sha256:f6cb980e5a701e1968aba3c0424f07f645153adbf10c44109981a14857a47fb6`
- verdict: `PASS_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1` (10/10 gates)

Candidate representation remains the frozen pairwise-disjoint support-resolved TopoModal cut. Recurrent corroboration remains exact event overlap with exactly one Recurrent-EOM parent. Pareto ordering remains exactly the two-objective rule from the positive source.

## Firewall

Use only target-excluded GMN 2022+2023 development data. Inclusive solar longitude `[20.0,55.0]` is excluded before geometry, sampling, candidate construction, ranking, prelabel serialization, or truth evaluation.

Forbidden:
- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 access;
- ASFN/EFN event-level access;
- AMOS, MAARSY, or DMS scientific access;
- orbital elements, station metadata, uncertainty metadata, or shower labels during candidate construction/ranking;
- any result-informed change to scale, buckets, radius, support floor, candidate extraction, corroboration, Pareto objectives, tie order, budget, metric, or gates.

## Previously untested scale

Use the already-frozen scale-stress hash and no new salt:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Test exactly denominator `d=64`, buckets `0,1,2,3`.

This yields four deterministic nested-scale panels of approximately 11.5k pooled events each, denser than the previously tested d=128 panels. No other denominator, bucket, replicate, bootstrap, or alternate salt is authorized.

## Candidate construction — unchanged mechanism

For each d=64 panel:

1. Reconstruct the exact target-excluded normalized GMN rows.
2. Apply the frozen support-resolved TopoModal cut implementation from `orbittrace_topomodal_support_resolved_cut_v1/generate_prelabel.py` without changing its physical embedding, radius `r=1.0`, GUDHI ToMATo 3.12.0 hierarchy, support floor 4, or cut recursion.
3. Construct the exact selected Recurrent-EOM comparator on the same event panel using the inherited Recurrent-EOM HDBSCAN method.
4. For every support-cut TopoModal candidate, count exact event-overlap hits against Recurrent parents:
   - retain iff it overlaps exactly one parent;
   - discard iff it overlaps zero parents;
   - abort as technical no-result iff it overlaps more than one parent.
5. Preserve the full TopoModal membership of every retained child.
6. Set `corroborating_parent_rank` to the unique parent rank and `native_support_rank` to the frozen support-cut rank.

No union, intersection, membership trimming, parent insertion, orphan completion, quota, or alternate candidate generator is permitted.

## Pareto-prominence order — byte-for-byte scientific rule

For each retained child `s`:

- `R(s) = corroborating_parent_rank(s)`, minimized.
- `M(s)` is its ordinal rank under descending `modal_contrast`, then ascending `native_support_rank`, then ascending `family_hash`, minimized.

Use ordinary non-dominated layers on `(R,M)`. Final total order is exactly:

1. Pareto layer ascending;
2. `M` ascending;
3. `R` ascending;
4. native support rank ascending;
5. family hash ascending.

All retained candidates remain exactly once. No fitted coefficients, transforms, thresholds, crowding distance, hypervolume, quotas, or learning are allowed.

## Pretruth authorization

Before truth is opened, serialize and SHA-256 seal a d=64 prelabel containing all four event universes, annual IDs, Recurrent parents, support-cut candidates, overlap audit, retained Pareto candidates, objectives/layers/ranks, and firewall fields.

All four panels must satisfy:
- exact d=64 hash selection and firewall;
- support-cut candidates pairwise disjoint;
- Recurrent candidates pairwise disjoint and continuously ranked;
- every retained child overlaps exactly one parent and every discarded child zero parents;
- retained membership unchanged from support-cut source;
- Pareto modal ranks form a permutation;
- Pareto layers/dominance valid;
- final order deterministic and continuous;
- retained candidate capacity is at least equal-budget `K = number of Recurrent candidates` in every panel;
- Pareto ordering is active in at least one panel (top-K order differs from inherited parent-rank/native-support order).

Only `PASS_PARETO_PROMINENCE_SCALE64_V1_PRETRUTH` authorizes truth evaluation. A structural fail closes this d=64 translation without truth.

## Truth metric

For each bucket and separately for 2022 and 2023, use the exact established Recurrent-EOM match semantics:
- eligible shower: at least 4 truth events in that annual panel;
- positive match: dominant precision >=0.5 and overlap >=4;
- equal budget K from the Recurrent comparator;
- evaluate exactly first K Pareto candidates against all K Recurrent candidates.

Report recovery/qualified matches, recovered@25/@50/@100/@500, mean top-100 dominant precision, median top-500 fragmentation, historical conditional MRR, reciprocal-rank mass, and zero-filled eligible-query MRR. Historical conditional MRR is diagnostic only.

## Binding d=64 promotion contract

Aggregate unweighted across the 8 annual bucket-year panels. Inherit the five coarse-scale preservation gates from the positive source:

1. Pareto qualified total is not lower than Recurrent-EOM.
2. Pareto qualified recovery is nonlower in at least 6/8 annual panels.
3. Mean zero-filled eligible-query MRR is not lower than Recurrent-EOM.
4. Mean top-100 dominant precision is not lower than Recurrent-EOM.
5. Mean median top-500 fragmentation is not higher than Recurrent-EOM.

All five are mandatory. First technically valid truth result is binding.

Return exactly:
- `PASS_PARETO_PROMINENCE_SCALE64_V1`, or
- `FAIL_PARETO_PROMINENCE_SCALE64_V1`.

A PASS establishes scale portability from d=128 to d=64 and authorizes a separately frozen denser/full-GMN scalability stage. It does not authorize protected-target access or an external superiority claim.

A valid FAIL closes this exact d=64 translation. No rescue by changing denominator/buckets, support cut, overlap rule, Pareto order, K, metric, or gates.