# OrbitTrace theory-scaled robust single linkage structural diagnostic v1 — result

## 🔴 NEGATIVE

First technically valid run: `31933224197`

Artifact: `9259928864`

Artifact digest: `sha256:58d62fa5c43d5cc7f20913cf7861732cb24184a7cd480a54fab48cd8f1b86c28`

Result SHA-256: `c97ef9c52f6535ca85afad6de0b44ee39dc6aa7de2c1292ec9daec1a8ba90129`

Exact frozen interpretation:

`REFUTES_THEORY_RSL_CHAIN_AND_SCALE_HYPOTHESIS`

### What passed

The dimensionless robust-tree branch lifetime remained much less sample-size-sensitive than raw formation scale in **all four** frozen branch-size bands. Thus the earlier scale-normalization observation survives the density-core robust hierarchy.

- supported bins: `4/4`
- strict lifetime-vs-formation scale wins: `4/4`

### What failed

The exact theory-scaled RSL hierarchy did **not** reduce chaining under either predeclared topology statistic.

- root largest-child strict wins vs ordinary single link: `0/8`
- internal mass-weighted split-imbalance strict wins: `0/8`
- ordinary median root largest-child fraction: `0.999233595032393`
- robust median root largest-child fraction: `0.9992574435045009`
- ordinary median mass-weighted split imbalance: `0.9771082087089451`
- robust median mass-weighted split imbalance: `0.9963816654879885`

The robust hierarchy therefore remained at least as root-chain dominated and was substantially more imbalanced internally under the frozen metrics.

### Engineering provenance

Initial run `31933011464` was an engineering no-result: the public `hdbscan.robust_single_linkage(..., algorithm='boruvka_kdtree')` path returned a nonmonotone linkage representation and the run stopped on the first subset before emitting any metric or result JSON.

The scientifically unchanged rerun used the exact generic mutual-reachability hierarchy with the same frozen `k(n)=ceil(6 ln n)` and `alpha=sqrt(2)`. `ENGINEERING_CORRECTION_V1.md` and `ENGINEERING_CORRECTION_V2.md` preserve the correction rationale.

### Consequence

The exact `k(n)=ceil(6 ln n), alpha=sqrt(2)` RSL anchor is closed. Do not rescue it by changing the multiplicative constant, log base, alpha, k schedule, branch-size bins, topology metrics, or gates after this result.

The result strengthens a narrower conclusion: **dimensionless branch lifetime is a useful sample-scale normalization, but neither ordinary single-link topology, additive FOSC pruning, nor this theory-scaled RSL topology identifies which branches are scientifically real.** The remaining justified direction is statistical branch-confidence/significance pruning rather than another deterministic hierarchy knob.

No shower truth, protected target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed.
