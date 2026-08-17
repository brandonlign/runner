# PhysCore-Residual TopoModal v1 — binding result

**Verdict: `PASS_PHYSCORE_RESIDUAL_TOPOMODAL_V1` (6/6 panels).**

Binding workflow: GitHub Actions run `32064907724` at execution commit `c206a6c095e717531c28cb758a700c5d7cb12dcf`.

## Frozen pretruth / structural activation

Pretruth verdict: `PASS_PHYSCORE_RESIDUAL_TOPOMODAL_V1_PRETRUTH`.

Pretruth freeze SHA-256: `bfc31e2cfd6e946aed5817d6fd1d897081cd0e661dd13c99243daf22b47cce2a`.

The exact PhysCore prefix remained unchanged, and the frozen residual TopoModal stage filled every matched-literature budget before truth access:

| Panel | PhysCore families | Residual TopoModal families | Successor catalogue | Frozen literature budget |
|---|---:|---:|---:|---:|
| HDBSCAN 2013 | 11 | 704 | 715 | — |
| HDBSCAN 2014 | 9 | 487 | 496 | — |
| Sugar 2013 | 11 | 889 | 900 | 34 |
| Sugar 2014 | 10 | 598 | 608 | 46 |
| D_SH 2013 | 11 | 1202 | 1213 | 41 |
| D_SH 2014 | 12 | 850 | 862 | 47 |

Pretruth artifact: `9299507541`; artifact ZIP digest `sha256:cad8ce7cd2d8b76ddf74032e3fe86eb4b779fd862429232efe0ae1e1ae68439d`.

## Binding exposed SonotaCo development evaluation

The two previously binding PhysCore-vs-published-HDBSCAN wins were inherited only after exact prefix identity was proved; their truth was not reopened.

| Comparator | Year | Successor macro F1 | Comparator macro F1 | Successor recovered | Comparator recovered | Win |
|---|---:|---:|---:|---:|---:|---|
| Published HDBSCAN | 2013 | 0.1756351130 | 0.1681717489 | 10 | 10 | PASS |
| Published HDBSCAN | 2014 | 0.1688317479 | 0.1568959558 | 9 | 9 | PASS |
| Sugar | 2013 | 0.3604437013 | 0.2037265747 | 22 | 13 | PASS |
| Sugar | 2014 | 0.4030646595 | 0.2590152773 | 23 | 15 | PASS |
| Rudawska-Jenniskens D_SH single linkage | 2013 | 0.3585733318 | 0.2528566656 | 22 | 16 | PASS |
| Rudawska-Jenniskens D_SH single linkage | 2014 | 0.3277846576 | 0.2341280610 | 18 | 13 | PASS |

Binding result SHA-256: `c92b6c22f115fe59da5e4e7a1c7cb0f0405e9ff46b1647bd57332399e11d6fd7`.

Result artifact: `9299521629`; artifact ZIP digest `sha256:32f48963ac84260974fb5e8d6938a6e27be1dddf540cddecd16d78b167ead2f9`.

## Access / leakage audit

- Candidate construction and catalogue ordering were frozen before truth access.
- `truth_access_before_pretruth = false`.
- `target_information_access = false`.
- `target_region_events_accessed = false`.
- AMOS scientific access: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- Post-result parameter search: false.
- The protected solar-longitude interval remains excluded by the frozen protocol.

## Interpretation

This is a candidate-generation result, not a ranking rescue. Retaining the high-quality PhysCore prefix and generating new TopoModal families only from its residual event set removed the prior proposal-count bottleneck and then beat every frozen exposed comparator panel at its own natural budget. No post-result tuning is authorized by this record.
