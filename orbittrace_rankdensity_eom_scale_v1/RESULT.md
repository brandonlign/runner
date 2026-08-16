# OrbitTrace rank-density EOM cross-scale structural diagnostic v1 — result

## 🔴 NEGATIVE

First technically valid run: `31934343254`

Artifact: `9260230784`

Artifact digest: `sha256:c10d89dd14eb24b33d0fc450b392682656bfd450e34e94a6009896dbc1b91e33`

Result SHA-256: `684dd1d315cbc64976fea118e88264ca29a42db3bc47b2191865f7dadece46a0`

Exact frozen interpretation:

`REFUTES_RANKDENSITY_EOM_CROSS_SCALE_COHERENCE`

### Frozen cross-scale results

Versus exact recurrent-EOM HDBSCAN `10/10` on the same four nested target-excluded GMN ~5.8k -> ~0.7k pairs:

- rank-density EOM pooled event-weighted mean best Jaccard: `0.5139478872575847`
- recurrent-EOM pooled event-weighted mean best Jaccard: `0.6775544963616581`
- rank-density EOM median bucket event-weighted mean best Jaccard: `0.5406968778511756`
- recurrent-EOM median bucket event-weighted mean best Jaccard: `0.6919491970848559`
- rank-density strict bucket wins: `0/4`

Bucket-level weighted best Jaccard:

- bucket 0: `0.5401100939` vs `0.6646757563`
- bucket 1: `0.4246629239` vs `0.7200783818`
- bucket 2: `0.5607646608` vs `0.6156967826`
- bucket 3: `0.5412836618` vs `0.7192226378`

Rank-density EOM produced nonempty output in all eight subsets, so only the nonempty-output clause passed; all comparative gates failed.

### Structural pattern

The rank-density tree was much less degenerate than the closed ordinary-single-link log-mass FOSC architecture, but its selected branch boundaries still changed substantially under thinning.

Selected rank-density candidate counts:

- denominator 128: `173, 196, 192, 185`
- denominator 1024: `24, 29, 29, 31`

Selected coverage fractions stayed broadly similar (~0.45–0.52), so the failure is not simply empty output or a giant-root collapse. Instead, the MST/upper-level-set connectivity partitions reorganize enough when points are removed that sparse selected memberships do not map to dense selected memberships as coherently as recurrent-EOM.

### Interpretation

PR #1277 established a useful zero-label fact: the same event's ordering by raw local density is highly stable under the 8× thinning stress even though absolute radii move strongly. This experiment shows that **stable density ordering is not sufficient when cluster membership is still defined by a point-connectivity tree**. The density percentile coordinate survives, but MST topology/branch boundaries remain sample-sensitive.

The exact third-neighbor empirical-rank + Euclidean-MST + percentile-EOM architecture is therefore closed. Do not rescue it by changing density k/support, graph, rank transform, branch lifetime, mass weighting, EOM tie rule, output support, subset, salt, or gate.

The next justified direction should avoid relying on fragile point-tree topology: fit or estimate a smooth survey-specific background/density field and identify statistically supported residual overdensity regions/components relative to that field, with all calibration label-free and frozen before truth.

### Engineering provenance

Initial run `31934184610` is preserved as an engineering no-result only. It failed on the first subset with Python `RecursionError` before any candidate summary, Jaccard metric, or result JSON. The valid run used the exact frozen implementation through `run_diagnostic_v2.py`, which changed only `sys.setrecursionlimit(100000)`.

No shower truth, protected target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed.
