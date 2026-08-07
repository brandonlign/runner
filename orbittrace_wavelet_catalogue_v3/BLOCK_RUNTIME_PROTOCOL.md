# OrbitTrace catalogue v3 block-runtime protocol

This work is implementation-only. It may change how exact rescoring is computed in memory, but it may not change any catalogue event, candidate, window, metric, calibration value, p-value, threshold, component rule, family-link rule, ranking rule, label boundary, development year, or blindness rule.

Before any catalogue access, the block implementation must prove deterministic equivalence to the frozen scalar/grouped implementation on synthetic windows, including:

- wavelet scores within the existing floating-point equivalence tolerance;
- identical positive-lobe member IDs;
- identical fixed4 nearest-three event selection under stable ties;
- fixed4 scores within the existing floating-point equivalence tolerance;
- identical accept/reject decisions after frozen empirical calibration when supplied the same scores.

The implementation may precompute immutable window arrays, use bounded anchor blocks, matrix multiplication/broadcasting, and stable partial selection. It must remain bounded-memory and deterministic.

The equivalence audit uses the exact frozen catalogue dependency set. Environment/import failures that occur before the scalar-versus-block comparison are technical failures and do not constitute an equivalence verdict.

No 2024–2026 catalogue and no OrbitTrace target information may enter runtime development. A runtime equivalence pass authorizes rerunning the already-frozen target-excluded 2022–2023 catalogue v3 development only; it does not alter the scientific method.
