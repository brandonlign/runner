# Single-link persistence scale diagnostic v1 — binding result

## 🟢 POSITIVE — scale-normalized branch coordinate supported

The first complete frozen zero-label diagnostic succeeded in GitHub Actions run `31930410578` at execution head `893be2aec08165ebbb6ec9897d6238dea7f50616`.

- artifact: `9259119329`
- artifact digest: `sha256:812c0b11f78b5fae536405baa08c3d629e939ebba5209b70cbb7416d09fa89e2`
- result SHA-256: `b4c32ea78447fda7f490f5bd3fb49d7fbf07ab873346035963aa69ea5599520b`
- exact predeclared interpretation: `SUPPORTS_SINGLELINK_PERSISTENCE_SCALE_NORMALIZATION`
- supported frozen size bins: `4/4`
- strict scale-normalization wins: `4/4`

This is a **zero-label structural feasibility result**, not a successor-method promotion.

## Frozen cross-scale comparison

The diagnostic compared the same target-excluded GMN geometry at denominator 128 (~5.8k events per bucket) and denominator 1024 (~0.7k events per bucket). The negative-control coordinate was raw branch formation distance; the tested coordinate was dimensionless single-link branch lifetime

`log_persistence = log(d_parent / d_form)`.

Every predeclared branch-size bin had at least 30 branches at both scales and won all three frozen relative comparisons.

| branch size | KS formation | KS persistence | median-shift formation | median-shift persistence | p90-shift formation | p90-shift persistence |
|---|---:|---:|---:|---:|---:|---:|
| 4–7 | 0.490125 | 0.101558 | 0.608747 | 0.023982 | 0.615981 | 0.057853 |
| 8–15 | 0.497100 | 0.095962 | 0.629338 | 0.007910 | 0.553618 | 0.053870 |
| 16–31 | 0.326649 | 0.161249 | 0.195641 | 0.014095 | 0.439050 | 0.045729 |
| 32–63 | 0.558589 | 0.274604 | 0.530893 | 0.021720 | 0.491220 | 0.130649 |

Thus the multiplicative branch-lifetime coordinate is materially less sensitive to the ~8x sample-count change than raw linkage scale across all tested branch sizes.

## Scientific interpretation

PR #1272 showed that fixed HDBSCAN `10/10` becomes structurally inert as accessible sample size falls. PR #1273 showed that at ~700 events both core-distance smoothing and minimum-cluster condensation jointly suppress alternative branches. A simple lower-support HDBSCAN rebuild is not acceptable because #1271 reconstructed/flooded the catalogue and failed early-budget quality.

This result supplies one missing architectural component: a **support-free, dimensionless tree coordinate** whose distribution moves much less with sample size than raw geometric linkage distance. It therefore provides a plausible basis for a statistical pruning layer that can judge whether a fine branch is unusually persistent relative to background without defining significance in survey-specific absolute distance units.

The result does **not** establish that raw single linkage is a good meteor detector. Single linkage is noise/chaining-sensitive, and this diagnostic contains no truth, recovery, precision, F1, MRR, recurrence, or false-positive evaluation. The next scientific problem is therefore not to rank branches directly by this persistence value; it is to determine whether branch persistence can be **calibrated against a source-preserving background null** so that fine branches survive only when their scale-free lifetime is statistically unusual.

This direction is consistent with general cluster-tree inference literature, where rich empirical trees are pruned to remove statistically unsupported branches rather than fixing one density resolution globally. Any OrbitTrace implementation remains a distinct future successor and requires its own pre-outcome protocol.

## Closure

Per the frozen protocol:

- no persistence threshold may be selected from this result;
- no branch-size bin, subset, or comparison criterion may be changed;
- no real-shower truth may be opened on this tree from this diagnostic;
- raw unpruned single linkage is not promoted;
- any statistical-pruning successor must be motivated and frozen separately before its first technically valid outcome.

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
