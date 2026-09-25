# OrbitTrace adaptive local-likelihood v1 — frozen development result

Authoritative workflow: `31145869525`

Artifact: `8981472925`

Artifact digest: `sha256:0a4ecbfdca23ac30a2e19c0e87627db656acb7fb72ff09f5defe5ff1a90a58d9`

Scientific source commit: `22ef069b17626bb640a9252e8ea4d879a473e7ec`

Verdict: **`FAIL_ADAPTIVE_LOCAL_LIKELIHOOD_V1_DEVELOPMENT`**

## Frozen metrics

| Method | Weak AUROC | FPR .05 | Worst-sector FPR .05 |
|---|---:|---:|---:|
| adaptive local-likelihood v1 | 0.551704 | 0.043945 | 0.057292 |
| Brown-family wavelet | 0.828506 | 0.059570 | 0.080729 |
| fixed4 | 0.813250 | 0.047852 | 0.065104 |

Alpha=.05 recall at k=4/6/8/12:

- adaptive v1: `0.029412 / 0.029412 / 0.080882 / 0.058824`
- wavelet: `0.080882 / 0.595588 / 0.830882 / 0.948529`
- fixed4: `0.154412 / 0.522059 / 0.691176 / 0.933824`

The calibration and upstream integrity gates passed, but every performance gate failed.

## Interpretation

The v1 local-shell Poisson formulation is rejected. Its score does not increase reliably with injected stream membership and is therefore not a viable primary detector. The likely structural failure is that, in a sparse 128-event episode, the fixed radius-4 outer shell often contains few or zero unrelated events. The local expected background then becomes extremely small, while maximizing over every anchor and four scales rewards accidental compact triplets in background episodes. The result is calibrated but poorly discriminative.

This failed formulation is frozen and may not be silently retuned or relabelled as successful. Any successor must be separately named and preserve this record.
