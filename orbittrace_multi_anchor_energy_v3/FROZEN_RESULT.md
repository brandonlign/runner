# OrbitTrace multi-anchor wavelet energy v3 — frozen development result

Authoritative workflow: `31146579074`

Artifact: `8981702758`

Artifact digest: `sha256:2ba81d1ba52eef89dc818c60169acd7804cc38281b380cdfed82664693509d89`

Scientific source commit: `34634faa13420af162298d5d0e17b77c93419ad8`

Verdict: **`FAIL_MULTI_ANCHOR_WAVELET_ENERGY_V3_DEVELOPMENT`** under the full preregistered primary gates.

## Frozen metrics

| Method | Weak AUROC | FPR .05 | Worst-sector FPR .05 |
|---|---:|---:|---:|
| multi-anchor energy v3 | **0.836860** | 0.056641 | 0.065104 |
| Brown-family wavelet | 0.828506 | 0.059570 | 0.080729 |
| fixed4 | 0.813250 | 0.047852 | 0.065104 |

Alpha=.05 recall at k=4/6/8/12:

- v3: `0.080882 / 0.610294 / 0.830882 / 0.948529`
- Brown-family wavelet: `0.080882 / 0.595588 / 0.830882 / 0.948529`
- fixed4: `0.154412 / 0.522059 / 0.691176 / 0.933824`

## Gate outcome

Passed:

- weak AUROC above Brown-family wavelet;
- k=6/8/12 recall preservation;
- worst-sector FPR <= 0.08;
- all upstream source, parser, comparator-reproduction, and integrity gates.

Failed:

- k=4 recall at least fixed4;
- pooled FPR .05 <= 0.055 (`0.056641`, 116/2048 held-out negatives).

## Interpretation

v3 is the first OrbitTrace-owned ranking in this development chain to exceed the Brown-family wavelet in weak-stream AUROC while preserving its moderate/strong-stream recall. The multi-anchor energy aggregation therefore survives as a promising primary ranking, but the full v3 detector does not pass because it does not solve the four-member tail and its nominal .05 pooled FPR is slightly above the preregistered cap.

The next authorized development step is not to replace or retune the v3 ranking. It is to develop a separately named decision architecture around the frozen v3 score, using the already validated fixed4 minimum-p sparse rescue and a conservatively calibrated primary decision threshold. Any such architecture must be frozen before prospective validation.
