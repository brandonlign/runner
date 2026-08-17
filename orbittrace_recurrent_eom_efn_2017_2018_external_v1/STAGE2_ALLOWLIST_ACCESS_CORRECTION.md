# EFN Stage-2 retained-ID access correction — frozen before geometry access

**Classification: firewall-strengthening access-plumbing correction. No scientific method or cohort change.**

The original frozen protocol requires that no protected-row physical geometry ever be returned, but its Stage-2 transport text proposed a server filter on raw catalogue longitude: `Lsun < 20 OR Lsun > 55`.

Stage-1 transport adjudication established that EFN `Lsun` is not strictly wrapped to `[0,360)`: the binding blind-only diagnostic observed values `360.0466`, `360.0309`, `361.1052`, and `361.1739`. The already-promoted recurrent-EOM method canonicalizes all finite solar longitudes with `% 360.0` before applying the protected interval.

Therefore a raw-longitude server filter is not sufficient to guarantee the protocol's stronger firewall requirement. A hypothetical raw `400 deg` row would pass `Lsun > 55` while canonicalizing to protected `40 deg`, causing geometry to be returned before the local protected check.

## Authorized Stage-2 access repair

Stage 1 has now successfully frozen the retained IDs before any EFN geometry access:

- run: `31841115599`
- job: `94897990578`
- head: `f23b7f414b99145e02df43e1e64f91f9f9600f94`
- artifact: `9234262113`
- artifact digest: `sha256:e27a98b0a9881134d0b60691ffa223c850e6a459f3511eac8d66965fd0065d2a`
- 2017 retained: `338`, SHA-256 `1f4bc6d32c7b65f70b567d8b618f2a4b672214e692405a568db5cf2b00b77745`
- 2018 retained: `444`, SHA-256 `7358ea62ad18559da8006b174e37c82e0a3d22eb44dfee1bd138433615a9b7dd`

The Stage-2 server query must now restrict by these **already-frozen retained IDs**, not by raw `Lsun` alone. It may return only:

`Code, Obs.date, Lsun, Lgeo-Lsun, Bgeo, Vgeo`

for `Code IN (<frozen retained allowlist>)`.

The Stage-2 program must still:

1. prove the allowlist files match the binding Stage-1 hashes;
2. require the returned ID set equals the retained union exactly;
3. canonicalize `Lsun` with the already-promoted `% 360.0` rule;
4. assert every returned canonical `sol` is outside inclusive `[20,55]`;
5. require finite native `Lgeo-Lsun`, `Bgeo`, and positive finite `Vgeo`;
6. use no quality filter, survey calibration, coordinate conversion, or velocity conversion;
7. return/query no `Shower`, `Object`, orbit, brightness, uncertainty, or other field.

A deterministic query batch size may be used only for TAP transport limits; batching cannot change the requested ID union or scientific output.

This correction strengthens the original protocol's firewall requirement and does not change which rows are scientifically eligible: the eligible set remains exactly the Stage-1 canonical-longitude retained set frozen before geometry access.

Firewall at correction freeze:

- Stage-1 retained IDs frozen: true
- EFN geometry accessed: false
- EFN shower labels accessed: false
- target information accessed: false
- target-region physical values accessed: false
- MAARSY scientific access: false
- DMS scientific access: false
- OrbitTrace target access: false
