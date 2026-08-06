# SonotaCo 2025 Valsecchi D_N episode comparison

The checksum-pinned D_N episode workflow completed successfully in run `31073086886` and produced artifact `8956382792` (`sha256:8410c0805c659a4e7755908578e9ba3a5d9b7c9c6f0d97fca5e28fc90f35803b`). The result file SHA-256 is `22de6690ebfaeabb2aec7de825ecf1c8ccd691ee00f98bcd2efa6aa4a29f4aa8`. All 11 protocol, parser, episode-count, fixed4-reproduction, equation, target, self-test, and finite-score gates passed.

## Exact benchmark results

| Method | Classification | Weak AUROC | FPR .05 | FPR .01 |
|---|---|---:|---:|---:|
| fixed-4° | frozen candidate | 0.813250 | 0.047852 | 0.006836 |
| D_N, M=6 | published distance and single-neighbour linkage evaluated at six members | 0.731316 | 0.046875 | 0.005371 |
| D_N, M=4 | predeclared sparse benchmark transfer | 0.759251 | 0.045898 | 0.007324 |

Recall at alpha 0.05 for k=4/6/8/12:

- fixed-4°: 0.154412 / 0.522059 / 0.691176 / 0.933824;
- D_N, M=6: 0.066176 / 0.316176 / 0.602941 / 0.955882;
- D_N, M=4: 0.154412 / 0.404412 / 0.470588 / 0.823529.

Recall at alpha 0.01 for k=4/6/8/12:

- fixed-4°: 0.058824 / 0.183824 / 0.294118 / 0.654412;
- D_N, M=6: 0.007353 / 0.095588 / 0.286765 / 0.647059;
- D_N, M=4: 0.051471 / 0.183824 / 0.205882 / 0.529412.

## Interpretation

The four-member D_N transfer is the strongest classical sparse comparator implemented so far, substantially improving on the prior four-member D_SH adaptation. Nevertheless, fixed4 retains a 0.054 AUROC advantage and materially stronger k=6 and k=8 recall. D_N, M=6 slightly exceeds fixed4 for k=12 recall at alpha 0.05, so the evidence does not support a claim that fixed4 is uniformly best at every stream strength or operating point.

The original D_N application estimated sample- and membership-dependent chance thresholds. This benchmark does not claim to reproduce those simulations. It applies the published geocentric distance and single-neighbour linkage as continuous birth-threshold scores under the exact same empirical negative calibration used by every episode comparator.
