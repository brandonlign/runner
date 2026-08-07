# OrbitTrace multiscale consensus v2 — frozen development result

Authoritative workflow: `31146272334`

Artifact: `8981610407`

Artifact digest: `sha256:5fe93e5585f635087e387aadf1b93e1b4adc6d0e66855fb37839d8728289b87f`

Scientific source commit: `3e52fde86da81bdfd4e8b9ae46bb52812dd7d3b3`

Verdict: **`FAIL_MULTISCALE_CONSENSUS_V2_DEVELOPMENT`**

## Frozen metrics

| Method | Weak AUROC | FPR .05 | Worst-sector FPR .05 |
|---|---:|---:|---:|
| multiscale consensus v2 | 0.693422 | 0.040039 | 0.049479 |
| Brown-family wavelet | 0.828506 | 0.059570 | 0.080729 |
| fixed4 | 0.813250 | 0.047852 | 0.065104 |

Alpha=.05 recall at k=4/6/8/12:

- v2: `0.102941 / 0.279412 / 0.360294 / 0.713235`
- Brown-family wavelet: `0.080882 / 0.595588 / 0.830882 / 0.948529`
- fixed4: `0.154412 / 0.522059 / 0.691176 / 0.933824`

All source, parser, comparator-reproduction, calibration, pooled-FPR, and sector-FPR gates passed. The performance gates failed.

## Interpretation

v2 materially improved on the failed v1 and increased four-member recall above the Brown-family wavelet, so requiring multi-anchor/multiscale support does contain useful sparse-stream information. However, robust within-episode normalization plus top-four averaging discarded too much absolute matched-filter amplitude: moderate and strong injected streams lost large amounts of recall and weak-stream AUROC remained far below Brown.

The next successor should therefore preserve the exact Brown-family raw coefficient amplitude as the primary evidence and add multi-anchor support without replacing or robust-normalizing that amplitude.

This v2 result is frozen. Same-result retuning is prohibited; any material successor is separately named.
