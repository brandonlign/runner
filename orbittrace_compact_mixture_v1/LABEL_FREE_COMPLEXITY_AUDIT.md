# Compact Mixture v1 — label-free complexity audit

This audit used only the exact pooled, protected-region-excluded, HDBSCAN-compatible SonotaCo 2013/2014 rows. No shower label, `iau` field, target information, orbit, uncertainty, or external truth entered the calculation.

The physical embedding and diagonal-Gaussian fitting form are exactly those frozen in `PROTOCOL.md`. The purpose was limited to determining whether low component truncations visibly underfit catalogue structure before any v1 truth access.

| K | BIC |
|---:|---:|
| 8 | 772262.0748264743 |
| 16 | 712707.0445686092 |
| 32 | 654758.2769592667 |
| 64 | 606049.3166007128 |
| 96 | 585316.5503882103 |
| 128 | 572084.8424549603 |
| 160 | 564053.8872243192 |

BIC decreased at every audited truncation and was still decreasing at `K=160`. Compact Mixture v1 therefore freezes `K=160` as a high-resolution truncation. This is **not** a claim that 160 is the BIC optimum.

No `K>160` was inspected for v1 before truth. The first technically valid v1 truth outcome permanently closes result-informed K selection for v1.
