# Main-based pinned execution of affine stream-tube v4

Status: frozen before the exact candidate source is decoded or any scientific score is computed in this branch.

## Purpose

Execute the clean, interface-complete affine stream-tube preflight without depending on a closed experimental branch that continued receiving bookkeeping commits.

## Pinned implementation

The workflow fetches exact repository commit `e06867d8c60aaeb8cb1a73d2c5bfdbb63de936ea` and extracts from that commit only:

- the affine v4 protocol and two source payload parts;
- the exact PR #14 baseline/episode payload and requirements;
- the exact passed PR #38 Mondrian scorer payload parts.

The decoded affine candidate must match SHA-256 `7ec195a34fa286129f01d181b7a8365623a0266d76c153a155d98d220cc833f3`. The inherited baseline and scorer must match SHA-256 `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50` and `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

## Scientific boundary

This is the same frozen preflight as PR #78:

- retired GMN 2019 and 2025 development data only;
- GhostStream solar longitude 20°–55° removed before every pool, window, score, fold, and endpoint;
- exact four-event anchored affine stream-tube statistic;
- exact inherited physical geometry and 10° Mondrian calibration;
- 64 calibration and 32 audit windows per supported bin;
- one deterministic positive replicate per eligible shower/member count;
- unchanged fixed comparators, complex-disjoint folds, seeds, thresholds, and continuation gates.

No source byte, statistic, input, seed, calibration count, comparator, fold, threshold, endpoint, or blind interval may change. Any failed source hash, data gate, calibration gate, or scientific gate kills this exact formulation. A pass authorizes only a separately frozen full four-year development benchmark and never GhostStream application.