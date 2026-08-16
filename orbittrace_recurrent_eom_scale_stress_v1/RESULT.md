# Recurrent-EOM fixed-scale stress diagnostic v1 — binding result

## 🟢 POSITIVE DIAGNOSTIC — fixed-scale inertia hypothesis supported

The first complete frozen zero-label diagnostic succeeded end-to-end in GitHub Actions run `31929171717` at execution head `3cf4f27d9df73da022b539d9f33e58a374ace074`.

- artifact: `9258799549`
- artifact digest: `sha256:706feba8f8cf6865e395deafe52ad1764876579b803fa9495d85193d2cc422e3`
- result SHA-256: `0c6926aa84d9b88f19f5bb2817b2846b53d09579dbef6b5c4d9c9bb9fd252288`
- exact predeclared interpretation: `SUPPORTS_FIXED_SCALE_INERTIA_HYPOTHESIS`

This is a **structural diagnostic result, not a successor-method promotion**.

## Frozen band result

The predeclared ASFN-size band comprised the four deterministic buckets at each of denominators 64 and 128:

- fits: `8`
- mechanism-inactive fits: `6`
- inactive rate: **`0.75`**

The predeclared EFN-size band comprised the four deterministic buckets at denominator 1024:

- fits: `4`
- mechanism-inactive fits: `4`
- inactive rate: **`1.00`**

Because both frozen bands met the preregistered `inactive_rate >= 0.75` criterion, the categorical interpretation is binding.

## Nested bucket-0 scale sequence

Exact target-excluded GMN geometry, exact GEO6, exact HDBSCAN `10/10`, and exact recurrent-EOM were held fixed. Only deterministic sample size changed.

| denominator | pooled n | median nonself 10-NN distance | ordinary nodes | recurrent nodes | node symdiff | recurrent mechanism |
|---:|---:|---:|---:|---:|---:|:---|
| 8 | 92,024 | 0.0883296340 | 349 | 341 | 22 | active |
| 16 | 45,880 | 0.1093164807 | 188 | 185 | 7 | active |
| 32 | 22,803 | 0.1356267025 | 111 | 106 | 11 | active |
| 64 | 11,375 | 0.1697610875 | 60 | 59 | 3 | active |
| 128 | 5,567 | 0.2126402672 | 29 | 29 | 0 | inactive |
| 256 | 2,792 | 0.2680141589 | 18 | 18 | 0 | inactive |
| 512 | 1,382 | 0.3354839480 | 11 | 11 | 0 | inactive |
| 1024 | 677 | 0.4207595503 | 8 | 8 | 0 | inactive |

The median physical GEO6 radius required to reach the tenth neighbor grew from `0.0883296340` at `n=92,024` to `0.4207595503` at `n=677`, a factor of about **4.76**. At the same time the selected hierarchy contracted sharply and ordinary/recurrent EOM became exactly identical in the smaller nested samples.

## Frozen replicate details

### denominator 64 (~11.4k events)

- bucket 0: active, node symdiff `3`
- bucket 1: inactive, symdiff `0`
- bucket 2: inactive, symdiff `0`
- bucket 3: active, symdiff `11`

Thus recurrence activity is already sample-sensitive at this scale (`2/4` inactive).

### denominator 128 (~5.8k events)

All four buckets were mechanism-inactive with identical ordinary/recurrent selected-node sets (`4/4` inactive).

### denominator 512 (~1.4k events)

All four buckets were mechanism-inactive (`4/4`).

### denominator 1024 (~0.7k events)

All four buckets were mechanism-inactive (`4/4`).

## Scientific interpretation

This isolates a real structural limitation of fixed-count recurrent-EOM HDBSCAN. Recurrent-EOM changes only FOSC/EOM extraction on a pooled HDBSCAN hierarchy. As accessible sample size falls while `min_samples=10` and `min_cluster_size=10` remain fixed, the tenth-neighbor radius spans a much larger region of GEO6 and the hierarchy contains fewer alternative density branches. Once those alternatives disappear, an extraction-only recurrence objective cannot select a different cut, regardless of its recurrence score.

The diagnostic therefore provides a direct sample-size-only reproduction of the same **mechanism inactivity** previously recorded on small external surveys, without reopening ASFN/EFN event rows or using any shower truth.

This does **not** prove that sample size is the sole cause of the external validation failures, nor does it establish that changing `k` would improve scientific recovery. It establishes the narrower causal point that fixed 10/10 support is itself sufficient to make recurrent-EOM increasingly inert as sample size decreases.

PR #1271 provides the complementary warning: simply lowering support to 8/4 reconstructs almost the entire selected catalogue and increases broad recoverability, but its uncalibrated local-BIC extraction loses early precision/MRR and fails the frozen gate. Therefore the unresolved method problem is not "choose a smaller k." It is to expose statistically supportable structure across sample sizes **without allowing a low-support hierarchy to flood the catalogue with poorly controlled branches**.

A genuinely distinct future architecture, if pursued, should therefore be motivated around statistically calibrated/adaptive multi-scale density structure or split significance rather than another fixed-count support choice or recurrence-score rerank.

## Closure

Per the frozen protocol:

- no denominator, bucket or sampling salt may be changed after this outcome;
- no observed scale may be converted into a new `min_samples` or `min_cluster_size` setting;
- no `k` tuning is authorized;
- this diagnostic does not alter the selected recurrent-EOM paper method;
- any future successor requires an independent pre-outcome protocol and must respect all closed-mechanism rules.

## Firewall

The binding workflow enforced:

- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `shower_truth_used=false`;
- `sonotaco_2013_2014_access=false`;
- `asfn_event_level_access=false`;
- `efn_event_level_access=false`;
- `amos_scientific_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `method_parameter_selection_from_result=false`.
