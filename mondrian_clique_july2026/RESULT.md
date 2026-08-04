# Mondrian four-clique: authoritative unused-July-2026 result

## Verdict

**`KILL_JULY_2026_MONDRIAN_CONFIRMATION`**

The exact coverage-normalized 10-degree Mondrian four-clique formulation passed all calibration, AUROC, comparator, fold-consistency, alpha-0.05 recall, and monotonicity gates on the untouched July 2026 snapshot. It failed the two frozen sparse-power gates at alpha 0.01 for k=4 and k=6. Under the predeclared all-gates rule, the formulation is killed and is not authorized for GhostStream or a catalogue scan.

## Frozen provenance

Source verification run `30875952724` passed before July data access and preserved artifact `8879532017`, digest `sha256:16168700b18bed3e7076522559a858604a5ec52e3da4b90380a22a3cf791335f`.

Frozen implementation hashes:

- July data source: `a9bd2f3ff033c7e4f524e214b28096c14e7a5cdddf56a043c20069a2b3d6d94e`;
- July power source: `8559424a4453ce4938654de37be7c164f3ca100ddd6c7d943c38df33cf3c2044`;
- baseline source: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`.

The first source-audit attempt failed before any July network request because an encoded payload was incomplete. The replacement payloads contained the already frozen implementations, were independently hash-verified and syntax-checked, and changed no scientific setting.

## Untouched data gate

Runner workflow `30876028073` executed the data-only gate and preserved artifact `8879562201`, digest `sha256:eeeb15d2f07fa6414fa3583f4ae41cff0edcbfa5bbe666ad48d6f74480eb3f07`.

The exact GMN snapshot was:

- URL: `https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_202607.txt`;
- bytes: `85,325,788`;
- SHA-256: `2eec48a52c186c9f2679e7b0eade710a3450b063c9300a67354e1fc82a08b575`;
- recorded last-modified value: `Mon, 03 Aug 2026 22:30:07 GMT`.

All eight data gates passed:

- 38 eligible showers;
- 23 strong showers;
- 36 eligible complex/parent units;
- 2 multi-shower complex units;
- 63,755 raw quality sporadics;
- 20,000 retained sporadics outside the blind interval;
- four supported globally anchored 10-degree bins: `[9, 10, 11, 12]`;
- feature completeness `1.000000`.

Preserved data hashes:

- selected events: `657bc671df2edfe2e4e9f1516f538988e3aa31eb039792ae4ee6c1f12bd50adb`;
- audit: `1feebfe723b6b3a683f3841255d80c4d5b2a05e1cdf054951085375e09c56edf`;
- data report: `7ea429b0140d76bdfc910dc33ebbf6186f55fb13edc72bb3b3042bde37521dee`.

## One-shot power result

Runner workflow `30876148147` downloaded the exact passed data artifact by run ID, verified every preserved hash, decoded and verified the frozen power and baseline sources, and then executed the one-shot score. Artifact `8879607361` was preserved with digest `sha256:bd00eb22cb911850ed67176e52a0f5b1b6ca6bcb3c51339774c8ca7d4000c1a8`.

Panel size:

- 38 eligible showers;
- 608 positive windows;
- 456 weak k=4/6/8 positive windows;
- 256 independent negative windows;
- five complete complex-disjoint folds.

Weak-window discrimination:

- Mondrian four-clique AUROC: **0.790390**;
- killed split statistic: **0.775571**;
- fixed local density: **0.778624**;
- fixed DBSCAN: **0.766494**.

Calibration:

- pooled FPR at alpha 0.05: **0.042969**;
- pooled FPR at alpha 0.01: **0.003906**;
- worst 60-degree reporting-sector FPR at alpha 0.05: **0.046875**.

Fold AUROCs:

- fold 0: **0.776879**;
- fold 1: **0.812826**;
- fold 2: **0.757568**;
- fold 3: **0.803711**;
- fold 4: **0.802083**.

Recall:

| injected members | alpha 0.05 | alpha 0.01 |
|---:|---:|---:|
| 4 | 0.151316 | 0.026316 |
| 6 | 0.407895 | 0.111842 |
| 8 | 0.605263 | 0.269737 |
| 12 | 0.861842 | 0.539474 |

Thirteen of fifteen scientific gates passed. The failed gates were:

- k=4 recall at alpha 0.01 required at least `0.05`; observed **0.026316**;
- k=6 recall at alpha 0.01 required at least `0.15`; observed **0.111842**.

Preserved result hashes:

- result JSON: `7fdbfca0a237ff53b2c28e9be0640a8efc5de397aa7691b243d44a636377df0f`;
- positive records: `2882fdc76437e5b3f53829cdd24b1857dd7d0791f8ed93a52301b00244f40f6e`;
- negative records: `ef70f7832d672c82871f3ec17a246715f6d0c440e48dc31f0977d46d7ad7208d`;
- report: `30cabbf15896f6366c159aaccf9334dccef2e59d85271626eabd17d4317cc4ef`.

## Interpretation and boundary

The independent July result confirms that the 10-degree Mondrian calibration repair solved the raw four-clique false-alarm instability: pooled and worst-sector error were comfortably controlled, discrimination beat every fixed comparator, every fold generalized, and all alpha-0.05 weak-stream gates passed.

The method did not meet the prospectively required sparse-stream sensitivity at the stricter alpha-0.01 operating point. That limitation is not a calibration failure and cannot be repaired by changing the p-value threshold, calibration count, gate, bin width, seed, or shower subset after seeing July.

No rerun, threshold relaxation, seed replacement, bin removal, endpoint change, or GhostStream application is authorized. Keep this branch closed, draft, and unmerged as the authoritative near-pass/no-go record.
