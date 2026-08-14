# Stratified-core HDBSCAN v1 zero-truth audit 1 — test assertion no-result

**Classification: engineering-only synthetic audit failure. No GMN catalogue/truth, SonotaCo, EFN, OrbitTrace target information/events, protected target-region data, MAARSY, or DMS access.**

Run `31844432139`, job `94907882159`, head `8c67db26eacbcff15ed188b52f8e5e5258eed5ef` passed all frozen source pins and entered the synthetic core-mechanics audit.

The implementation-computed stratified core vector had already matched the independent brute-force vector bit-for-bit. The audit then failed on an incorrect hand-written expected value for synthetic event 0:

`duplicate-coordinate self exclusion changed: 0.4`

For that synthetic same-year row, the other-event distances are `0.0` (distinct duplicate identity), `0.1`, `0.2`, `0.3`, `0.4`, ... . Therefore the fifth nearest **other** event is correctly at `0.4`; the assertion incorrectly expected `0.3` by counting only four other events after the duplicate.

Authorized repair: change only the synthetic expected scalar from `0.3` to `0.4`. The frozen 5+5 core definition, exact-self exclusion rule, duplicate-event inclusion rule, injected-core hierarchy code, HDBSCAN parameters, and all scientific gates remain unchanged.
