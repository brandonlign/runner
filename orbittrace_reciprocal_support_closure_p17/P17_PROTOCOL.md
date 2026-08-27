# P17 reciprocal-support closure for support-safe halo characterization

## Status

Frozen after P15 pretruth workflow `31330227055` exposed a pretruth control-flow incompatibility, and **before any HDBSCAN/Sugar cluster value, known-shower truth value, matched F1/superiority outcome, external result, or OrbitTrace target access**.

P17 is a conservative edge-case completion of the already-frozen P15 secondary-halo availability rule. It changes no detector family, primary event set, primary rank, score, feature, covariance, threshold, finite-sample floor, density rule, or proposal geometry.

## Pretruth bottleneck that motivates P17

P15 correctly made an exact `<128`-negative direction unavailable and contributed zero proposals from it. On the HDBSCAN matched universe, the frozen drift artifact contained 75 eligible directions for 38 recurrent core families, demonstrating that exactly one reciprocal direction was unavailable as preregistered.

The inherited P12/P9 downstream code still contained two assumptions from the original all-directions-eligible development universe:

1. every family must have exactly two `direction_records`;
2. every eligible direction must be able to retrieve a reciprocal P3 reliability value.

Those are incompatible with a deliberately unavailable direction. P15 therefore remains a technical/pretruth no-result until this edge case is represented explicitly. No comparator value or truth was opened.

## Exact P17 scientific rule

P17 preserves the P15 direction-level support rule exactly:

- `MIN_DIRECTION_NEGATIVES = 128` remains immutable;
- an exact direction with fewer than 128 target-window negatives is `CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES` and contributes zero nonseed proposals;
- an independently support-eligible opposite direction is still fit/scored with exact inherited P12 science.

P17 additionally defines the only fail-closed interpretation compatible with frozen P9 bidirectional reliability:

- bookkeeping accepts that, for a family, each reciprocal direction is represented **either** by one eligible direction record **or** by one pretruth P15-unavailable ledger entry; the two representations together must still account for exactly two reciprocal directions;
- for an eligible direction, if its reciprocal P3 reliability exists, exact P9 is unchanged;
- if reciprocal P3 reliability does not exist **only because the exact reciprocal direction is present in the P15 unavailable ledger**, reciprocal reliability is treated as unavailable/false, so `p9_reliable = False` for that eligible direction;
- therefore the supported direction is evaluated but contributes zero proposals whenever its reciprocal direction is unavailable;
- a missing reciprocal reliability without the exact P15 unavailable-ledger proof remains fatal;
- no synthetic reciprocal model/reliability is created, no padding/resampling/borrowing is permitted, and no threshold is relaxed.

This preserves P9's requirement that nonseed membership growth needs reciprocal reliability. Absence of evidence cannot become positive reliability.

## Development non-regression

On canonical target-excluded 2022/2023 development, P15's fallback is vacuous: all 452 reciprocal directions have at least 128 negatives (minimum 2,197). Therefore P17's new missing-reciprocal branch must also be vacuous there.

P17 may be promoted only if an immutable development adjudication proves:

- zero P15 unavailable directions;
- zero P17 missing-reciprocal closures;
- exact canonical P12/P13 family/member decisions and established metrics remain unchanged;
- no new truth, matched comparator, external, or target access.

The canonical artifact-only P15 development PASS remains the scientific source of the zero-unavailable proof; P17 cannot use the rejected post-result floating-tolerance rescue.

## Matched benchmark and downstream architecture

P17 inherits the exact frozen P14/P15 SonotaCo 2023/2025 HDBSCAN/Sugar universes and all sparse-superiority gates unchanged. Both comparator checkpoints must freeze before any comparator cluster value or known-shower truth is opened.

P16's core-rank/halo-membership idea remains scientifically valid but its P15 dependency is superseded by P17 for matched portability. Any promoted reported-halo catalogue successor must consume the exact P17 pretruth halo, not silently reinterpret the failed P15 checkpoint path.

## External and target boundary

No external or target access is authorized by this protocol. A successor may proceed externally only after the fixed matched sparse-superiority requirement passes and only under a separately preregistered no-retuning external protocol. Final OrbitTrace access remains forbidden until matched literature superiority and defensible no-retuning generalization are satisfied.
