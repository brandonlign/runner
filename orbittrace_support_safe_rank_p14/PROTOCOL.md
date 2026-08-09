# OrbitTrace P14 — support-safe multiplicity rank completion

## Status and motivation

P14 is frozen **before any Sugar/HDBSCAN cluster value, known-shower truth value, matched F1, or sparse-superiority outcome has been opened**. It is the sole architecture-level response to a deterministic transport-domain failure observed in pretruth P13 exact-row construction: immutable multiplicity scoring is undefined when either year has fewer than the frozen 128 events in a family's local window.

P13 remains scientifically successful on its target-excluded development universe. P14 must therefore be a backward-compatible semantic extension, not a new tuned detector.

## Immutable inherited architecture

P14 inherits P13 exactly:
- immutable recurrent core family construction and event IDs;
- exact P12 halo as secondary characterization only;
- fixed target exclusion 20°–55° during development/comparator/external work;
- exact v8 multiplicity statistic wherever it is defined;
- exact `EPISODE_SIZE = 128`;
- exact core discovery/halo characterization claim split;
- no recursive growth, no new threshold, no new feature, no retuning.

## Sole P14 change: fail-closed total-order completion

For any target-free panel after recurrent core families/centroids are frozen:

1. A family is **multiplicity-scorable** iff immutable v8 `build_local_episode` succeeds with exactly 128 events for each required year.
2. Every scorable family is passed through the exact immutable v8 `score_families` code and receives the exact unchanged multiplicity values.
3. Exact immutable v8 `rank_scored(..., "multiplicity")` orders all scorable families.
4. If immutable scoring raises exactly `family <ID> year <YEAR> has only <N> events in local window`, with `N < 128`, that family is retained as an immutable recurrent core but receives **no fabricated multiplicity score**.
5. Unscorable recurrent cores are appended after **all** scorable cores, ordered lexicographically by stable `family_id` solely to complete the total catalogue order.
6. No unscorable core may outrank any scorable core.
7. No padding, resampling, duplicate events, smaller episode, adaptive episode size, score extrapolation, replacement score, structural proxy score, family deletion, or family-specific rescue is permitted.
8. Any other exception remains fatal. P14 catches only the exact immutable insufficient-local-window exception.

This is conservative missing-evidence semantics: a recurrent structure remains reportable, but absent the 128-event evidence required by the promoted ranking statistic it cannot receive ranking credit over a family with a defined multiplicity score.

## Development promotion gate

P14 may replace P13 only if authoritative target-excluded development proves:
- v8 requested families = 226;
- v8 scored families = 226;
- all 452 development episodes have exact size 128;
- therefore the P14 fallback is vacuous on development;
- P13 core family count/order/hash are unchanged;
- P13 core discovery endpoints remain exactly 95 qualified, 58 recovery@100, 95 recovery@500, MRR `0.045531138942766655`, top-100 precision `0.6884631112636006`;
- exact P12 halo hash and membership-quality endpoints remain unchanged;
- no detector/catalogue/truth recomputation occurs in the P14 development adjudicator.

If any development family is unscorable, or any existing P13 output/hash/endpoint changes, P14 fails and is not eligible for matched literature.

## Matched benchmark consequence

Only after P14 development PASS may the Sugar/HDBSCAN benchmark be re-frozen/continued under P14. Exact comparator row universes, assignment bytes, evaluator, truth eligibility, size strata, sparse/broad gates, core/halo fairness boundary, and pretruth barrier remain unchanged from P13.

The only matched difference is that a recurrent core whose exact multiplicity statistic is undefined because its exact-row local window has <128 events remains in the core catalogue but ranks after every scorable core. The fallback identity/status must freeze before truth.

## External and target boundary

No matched PASS, no external access. No external PASS, no target access. P14 does not authorize OrbitTrace coordinates, members, identity, target-region event values, or the 20°–55° final search.
