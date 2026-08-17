# Recurrent-EOM residual TopoModal GMN diagnostic v1 — binding closure

**Verdict: `FAIL_PRETRUTH_RESIDUAL_CONSTRUCTION`.**

Binding workflow: GitHub Actions run `32066070645`, pretruth job `95498382620`, execution commit `bdc7db33ddfba69ac45963cc5fccbfc143b0cfe5`.

Pretruth SHA-256: `b7de8a004fe811ca3f7e41d5fe1e0940bff0aadefb55edf9497f7f227c67f859`.

Pretruth artifact: `9300010295`; artifact ZIP digest `sha256:138b1d51c1add8c08124bdfb43d9f196ffd9e3a49730e3cd318b993933d913a5`.

## Structural result

| Scale | Bucket | Panel events | Recurrent-EOM candidates | Accepted events | Residual events | Residual TopoModal candidates | Activation |
|---|---:|---:|---:|---:|---:|---:|---|
| 1/128 | 0 | 5,567 | 29 | 2,100 | 3,467 | 9 | PASS |
| 1/128 | 1 | 5,840 | 35 | 2,041 | 3,799 | 19 | PASS |
| 1/128 | 2 | 5,857 | 38 | 2,120 | 3,737 | 18 | PASS |
| 1/128 | 3 | 5,816 | 33 | 2,133 | 3,683 | 13 | PASS |
| 1/1024 | 0 | 677 | 8 | 234 | 443 | 1 | PASS |
| 1/1024 | 1 | 739 | 5 | 205 | 534 | 0 | FAIL |
| 1/1024 | 2 | 736 | 6 | 266 | 470 | 0 | FAIL |
| 1/1024 | 3 | 766 | 9 | 258 | 508 | 0 | FAIL |

The exact frozen residual construction therefore transfers structurally at the coarser sparse scale but collapses at the finer scale: three of four 1/1024 panels contain hundreds of residual events yet no eligible frozen TopoModal hierarchy node reaches the preregistered support floor of four.

## Firewall / truth audit

The pretruth structural gate failed, so the downstream truth-evaluation job was not authorized and did not run.

- shower truth opened: **false**
- protected `[20°,55°]` target information/events accessed: **false**
- SonotaCo 2013/2014 accessed: **false**
- AMOS accessed: **false**
- MAARSY accessed: **false**
- DMS accessed: **false**
- post-result parameter search: **false**

## Binding closure

This exact `Recurrent-EOM -> remove all Recurrent-EOM members -> frozen radius-1/support-4 TopoModal on residual` mechanism is permanently closed under its frozen protocol. Do not lower support, enlarge the radius, change the sparse scales/hash panels, alter the residual definition, or otherwise rescue this v1 from its result.

The result localizes the next scientific problem to **low-support candidate existence under extreme sparsity**, not ranking: the coarser residual panels retain candidate structure, while the fine residual panels usually do not. Any successor must therefore use a genuinely different pre-frozen sparse-support candidate-generation mechanism rather than retuning TopoModal.
