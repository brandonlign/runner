# P2 canonical runtime identity

Frozen before any P2 scientific execution and before any P1 scientific result.

There is exactly one authorized P2 scientific runtime:

1. base source `run_development.py` SHA-256 `7637b6fb310ee3f24f1de8479a34d10c594dc55471eee55b8854e1c28787e8dd`;
2. apply exactly `apply_protocol_compliance_patch.py`, yielding SHA-256 `169ed0a276cdcae628cd830130cfb03d6511a972df50d4dc10ffddfc1c8e05da`;
3. apply exactly `apply_protocol_precision_patch_v2.py`, yielding final SHA-256 `f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb`.

The second patch is implementation-only and exactly reversible. It resolves two protocol-literal issues before any science:

- covariance singularity is decided by NumPy's machine-precision `matrix_rank` rule; only rank-deficient covariance uses the Moore–Penrose pseudoinverse;
- the frozen local-window condition is exactly `|wrapped Δsol| <= 5.0°`, with no epsilon enlargement.

Source-only audit run `31283328434` passed and artifact `9029093070` recorded final runtime SHA-256 `f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb`.

No alternate P2 source package, unpatched base source, v1-only source, earlier development workflow, threshold, covariance fallback, or candidate-boundary implementation is authorized for scientific execution. The only future activation marker is `RUN_V2.md` under the v2 guarded workflow, and it requires an exact frozen P1 scientific no-go artifact.
