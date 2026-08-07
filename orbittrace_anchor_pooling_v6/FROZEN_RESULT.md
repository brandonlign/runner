# OrbitTrace top-four anchor pooling v6 — frozen result

Workflow: `31147973719`

Selection artifact: `8982249452`

Selection artifact digest: `sha256:13cbfbb4b44e8b67937d88019aad69cad8aabbf9cd3f392470cda433d7693a07`

Scientific candidate source commit: `6b572b0bf9a1919d649c782da8b3d2d24562d97e`

Verdict: **`FAIL_ANCHOR_POOLING_V6_DEVELOPMENT`**

Feasible candidates: **0/6**.

| Candidate | min annual AUROC margin over Brown | mean margin | minimum k4 margin vs fixed4 | 2025 AUROC | 2023 AUROC |
|---|---:|---:|---:|---:|---:|
| L1 | +0.004380 | +0.006627 | -0.058824 | 0.837381 | 0.836351 |
| L1.5 | +0.004341 | +0.006490 | -0.066176 | 0.837145 | 0.836313 |
| frozen v3 L2 | +0.004291 | +0.006323 | -0.073529 | 0.836860 | 0.836263 |
| L4 | +0.003973 | +0.005648 | -0.073529 | 0.835829 | 0.835944 |
| geometric mean | +0.004437 | +0.006830 | -0.051471 | 0.837729 | 0.836409 |
| fourth-largest anchor | +0.001766 | +0.004336 | -0.036585 | 0.835411 | 0.833738 |

All six aggregation rules preserved a positive two-year AUROC advantage over Brown, strengthening the underlying multi-anchor observation. None matched fixed4's four-member sensitivity under the full gates. Therefore further pooling of the same Brown coefficient vector is not an adequate route to the complete detector goal.

This negative result is frozen. The next successor may incorporate the independently informative fixed4 channel, but may not silently retune or add pooling candidates to v6.
