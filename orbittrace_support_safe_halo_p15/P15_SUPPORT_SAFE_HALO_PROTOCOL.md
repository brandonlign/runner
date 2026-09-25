# OrbitTrace P15 support-safe secondary halo availability

Status: conceptual/scientific rule frozen after P14 matched pretruth stopped on an exact P12 input-eligibility condition and **before any comparator cluster value, known-shower truth value, matched F1, superiority result, external value, or target-region value was opened**.

## Motivation

Promoted P14 makes the recurrent core/rank total and fail-closed when exact 128-event multiplicity is undefined on a restricted matched universe. In pretruth workflow `31327020945`, that primary core/rank froze successfully. The secondary exact-P12 characterization halo then encountered a separate existing P12 precondition: one family-direction had fewer than `MIN_DIRECTION_NEGATIVES = 128` target-window nonseed negatives. Exact P12 is undefined for that direction.

The secondary halo is characterization-only and is forbidden from affecting primary discovery, ranking, or matched superiority. Therefore insufficient negative support must not alter the recurrent core, relax 128, synthesize negatives, or block an otherwise valid primary catalogue.

## Frozen P15 rule

P15 changes **only secondary characterization availability**:

1. Primary discovery remains exactly promoted P14: identical recurrent core family IDs/event sets and support-safe multiplicity total order.
2. Exact P12 science, thresholds, features, OLS drift fit, OAS covariance, D_SH view, crossfit, density veto, proposal logic, conflict resolution, and membership decisions remain unchanged for every eligible family-direction.
3. `MIN_DIRECTION_NEGATIVES = 128` remains immutable.
4. A family-direction is secondary-halo eligible iff its existing exact P12 target-window nonseed set contains at least 128 negatives.
5. If and only if that exact precondition fails, the direction is recorded as `CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES`, contributes **zero nonseed proposals**, and execution continues to the next direction.
6. No padding, resampling, replacement, smaller negative set, threshold extrapolation, score fabrication, or borrowing from another panel/year is permitted.
7. The opposite direction of the same recurrent family remains independently eligible and, if eligible, runs exact P12 unchanged. Thus available exact characterization is retained without inventing evidence for the unavailable direction.
8. Every other exception remains fatal. P15 does not create a general exception-catching mechanism.
9. Halo construction still begins from immutable core membership; an unavailable direction cannot remove a core member. The secondary halo is the core plus exact-P12 accepted nonseed assignments arising only from eligible directions.
10. Pretruth checkpoints must record every unavailable direction, source/target year, observed negative count, required count 128, and a deterministic hash of this availability ledger.
11. Halo remains strictly secondary and may not enter primary matched F1, ranking, sparse superiority, or advancement gates.
12. Solar longitude 20°–55° remains inaccessible.

## Development promotion gate

Before P15 may replace P14/P12 characterization semantics, the rule must be tested only on the original target-excluded development state. Promotion requires:

- all 452 original P12 family-directions are eligible (`negative_count >= 128`);
- zero P15 unavailable-direction fallbacks fire;
- exact P14/P13 core identity/order remain unchanged;
- exact P12 halo membership identity/hash remains unchanged;
- all previously frozen P13/P14 development endpoints and P12 halo metrics remain unchanged;
- no new truth query and no target access.

If any fallback fires on development or any established output changes, P15 fails and cannot be used for matched evaluation.

## Matched benchmark consequence

If development compatibility passes, the already-frozen comparator row universes, strict manifests, P14 core/rank rules, evaluator, sparse superiority gates, truth timing, and target firewall remain unchanged. Only secondary-halo availability becomes support-safe as above. Both HDBSCAN and Sugar pretruth checkpoints still must freeze before truth opens.
