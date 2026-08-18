# OrbitTrace Pareto-prominence scale-64 v1 — binding result

## Verdict

**STRUCTURAL FAIL BEFORE TRUTH.** The exact d=64 scale translation is closed.

No shower truth was opened and no scientific result was produced. The first execution reached the truth-blind candidate-construction stage and failed the frozen unique-Recurrent-parent corroboration requirement on bucket 0.

## Provenance

- scientific branch: `agent/orbittrace-pareto-prominence-scale64-v1`
- frozen protocol commit: `1d16ec6289f8f2a0fc51da6410f9d89f25411c29`
- protocol blob: `f1976a5776cb7b89744f25074d9f96a4429d172e`
- scientific implementation execution commit: `f13631d868b24c95983e1cfd6f8886ff5c8a5a5d`
- prelabel builder blob: `f36e77bc5210f28b41b1c2fab25ffefb2b14f516`
- truth evaluator blob: `0b8cbc3497ec747eb1f4c05664b3d5d89105a32b`
- workflow run: `32102488542`
- workflow job: `95605586627`
- provenance-only artifact: `9312081426`
- artifact digest: `sha256:fb6324ffa49631f075661da1dc39516b1c710a93d2afc55df768f7adba2d35e6`

## Binding pretruth observation

The exact target-excluded GMN runtime reproduced successfully. Protected solar longitude `[20,55]` remained excluded. The first d=64 panel was deterministic bucket 0 with `11,375` pooled 2022+2023 events.

Candidate construction then raised:

`RuntimeError: support child overlaps multiple recurrent parents`

This occurred before a d=64 prelabel could be sealed. The artifact therefore contains provenance/environment only; it is not a scientific truth artifact.

## Why this is a scientific structural failure rather than repairable plumbing

The positive sparse source architecture itself requires a retained TopoModal support child to overlap **exactly one** Recurrent parent. Its frozen overlap-consensus source (`orbittrace_recurrent_topomodal_overlap_consensus_v1/build_prelabel.py`, blob `eb2e324ad60b3a6e4249de587b83d77a4d156417`) explicitly asserts `len(parent_hits) <= 1` and serializes the configuration `abort: more_than_one_recurrent_parent_overlap`.

Therefore the d=64 failure is not caused by an accidental translation implementation choice. At the denser scale, at least one support-resolved TopoModal child violates a structural assumption of the exact Pareto-prominence architecture: unique Recurrent-parent corroboration.

Discarding multi-parent children, choosing one parent, splitting the child, using maximum overlap/Jaccard, or otherwise resolving ambiguity would change the scientific mechanism after observing the structural result and is not authorized.

## Interpretation

Pareto-prominence v1 remains a clean 10/10 PASS on the previously frozen d=1024/d=128 sparse GMN benchmark. However, its exact architecture does **not** demonstrate straightforward scale portability to d=64. The failure occurs before ranking-quality truth metrics can even be evaluated, because candidate-to-parent correspondence becomes non-unique as panel density increases.

This materially weakens any claim that the sparse Pareto-prominence mechanism is already a full-GMN/general method. A future method must address many-to-many Recurrent/TopoModal correspondence by a genuinely new, separately frozen scientific mechanism rather than rescuing this lane.

## Closure

The exact d=64 translation is closed. Do not rescue it by:
- discarding multi-parent children only because this failure was observed;
- assigning a multi-parent child to one parent by overlap/Jaccard/size/rank;
- splitting or trimming multi-parent children;
- changing denominator, bucket, salt, radius, support floor, support cut, Pareto objectives/order, budget, metric, or gates;
- opening d=64 truth for the failed unsealed construction.
