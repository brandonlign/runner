# Fresh 2026 H1 partition-invariant clique result

## Authoritative execution

Runner workflow `30873405862` completed the full frozen January–June 2026 benchmark from power-source SHA-256 `22b9ddeab4b628a8991d255c740ba709ffe7977c209fd21a2ad9083c2c726e2f`.

Artifact `8878660162` was preserved with digest `sha256:cf992e8637ebb877c9e37f0cc856b7bd878aaf1db62ae0df697a31ad41421c0e`.

All source, data, audit, baseline-payload, and baseline-source hashes passed before scoring. GhostStream remained blinded by removing solar longitude 20.0°–55.0° before all pools, windows, scores, folds, and endpoints.

## Fresh confirmation panel

- 99 eligible established showers after the blind interval;
- 100 complete MDC complex/parent reporting units across five folds;
- 1,188 weak positive windows;
- 1,024 independent empirical-background negative windows;
- four supported 60-degree sectors: 0, 1, 4, and 5.

## Performance

- partition-invariant clique weak AUROC: **0.82674**;
- killed reference/query split comparator AUROC: **0.81240**;
- fixed local-density AUROC: **0.80294**;
- fixed DBSCAN AUROC: **0.78595**.

Every complex fold passed:

- fold 0: **0.80308**;
- fold 1: **0.86601**;
- fold 2: **0.82809**;
- fold 3: **0.78798**;
- fold 4: **0.84463**.

Candidate recall:

| Members | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | **0.23485** | **0.10354** |
| 6 | 0.52525 | 0.31818 |
| 8 | 0.77525 | 0.48990 |
| 12 | 0.95707 | 0.73485 |

The clique improved exactly-four-member recall over the split comparator by **0.02273** at alpha 0.05 and **0.02778** at alpha 0.01.

## Frozen gate outcome

Seventeen of eighteen gates passed. The only failure was pooled candidate false-positive rate at alpha 0.05:

- observed: **0.06836**;
- frozen maximum: **0.06000**.

The alpha-0.01 FPR passed at **0.01465**, and the worst-sector alpha-0.05 FPR passed at **0.10547**. Sector 4 contributed the excess, with candidate FPR **0.10547**; the killed split comparator was also elevated there at **0.09375**, indicating a shared local-calibration problem rather than a clique-specific power defect.

Verdict: `KILL_PARTITION_INVARIANT_CLIQUE_2026H1`.

## Interpretation and rule

The partition-invariant four-clique statistic solved the split-allocation sensitivity problem and generalized strongly in AUROC, fold consistency, and four-member recall. The exact 60-degree-sector calibration formulation nevertheless failed its prospectively frozen pooled false-alarm gate on fresh data.

Do not lower the FPR gate, replace seeds, remove sector 4, narrow the evaluated shower set, or rerun this exact source. A new method may investigate continuous or finer conditional background calibration, but it must be frozen and validated as a separate formulation.
