# Multiscale phase-marginal support: July development result

Runner workflow `30876505608` completed the frozen retired-July benchmark and preserved artifact `8879728749` with digest `sha256:5599bd84372f7eceb87c21885a38aa41a25d1596ea61e4c651a99804bc4e5bc4`.

## Result

- candidate weak AUROC: **0.790237**;
- density / DBSCAN AUROC: **0.753064 / 0.744659**;
- negative FPR: **0.065430** at alpha 0.05 and **0.000000** at alpha 0.01;
- worst-block FPR at alpha 0.05: **0.082031**.

Recall:

| members | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | 0.161184 | 0.000000 |
| 6 | 0.407895 | 0.000000 |
| 8 | 0.608553 | 0.000000 |
| 12 | 0.822368 | 0.000000 |

Fold AUROCs were **0.832520, 0.860118, 0.777524, 0.777003, and 0.707718**.

Verdict: **`KILL_PHASE_ADAPTIVE_JULY_POWER`**.

## Interpretation

Selecting the minimum locally normalized tail among 4-, 8-, and 16-star components improved neither raw discrimination nor strict-tail power. The independent outer conformal layer correctly absorbed the scale-selection multiplicity, but the selected statistic became too conservative in the extreme tail. All alpha-0.01 recall endpoints were zero, and the 5% negative rate exceeded the prior ceiling.

This closes minimum-tail multiscale selection. No component set, aggregation rule, bank size, KNN count, or threshold will be changed within this formulation. It is not eligible for untouched confirmation or GhostStream application.
