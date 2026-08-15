# Final #1263 AMOS — pre-data infrastructure reuse freeze

## Role

Zero-scientific-data implementation provenance only.

The final AMOS endpoint is scientifically defined by `PROTOCOL.md` on this branch. Older AMOS branches are not executable alternative endpoints. This record identifies which already-audited components may be reused unchanged and which scientific components must be replaced because the final method is now #1263.

## Reuse unchanged by exact source identity

### Blind receipt from PR #1244

Exact source:

- `orbittrace_recurrent_eom_amos_2023_2024_external_v1/blind_receipt.py`
- Git blob `9fed803aa09f03f779610eaff5304251bbf21020`
- source head `1fb8f68b84bc200545a23cb5a216baa7e0fa0f09`

Its role is method-agnostic and remains exact:

- accept only `event_id,utc_time,solar_longitude_deg`;
- exact calendar years 2023/2024;
- inclusive protected removal `[20.0,55.0]`;
- output only retained-ID allowlist/hash;
- no geometry or truth access.

The binding synthetic blind-receipt audit from #1244 remains historical engineering evidence. A new final-pipeline source audit must re-verify the exact blob before any provider transfer is opened.

### Canonical coordinate adapter from PR #1244

Exact source identities:

- transform blob `612ad23af6e11ac2155282258e3d1429fbe00d67`;
- adapt blob `9a0fb05f94d6a28cd95f97d864e76400056273b0`.

No AMOS-specific empirical fit, offset, alignment, velocity correction, quality cut, or parameter change is allowed.

### Comparator-only structural contract from PR #1248

The optional supplementary header remains exactly:

`event_id,ra_sd_deg,dec_sd_deg,vg_sd_km_s,convergence_angle_deg,q_au,e`

Unknown/protected/duplicate IDs fail closed. Missing optional values affect only the relevant comparator-specific supplementary universe; they never remove a row from the primary final-method sample.

The frozen comparator implementation identities remain:

- literature adapter blob `00578445ed0957fb3708bb84fda1df6ef7b5b004`;
- Sugar core SHA-256 `5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`;
- catalogue-HDBSCAN source SHA-256 `a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`.

## Reference-only; not reusable as final scientific endpoint bytes

The old recurrent-EOM scientific generator/evaluator from #1244 are historical reference only:

- old pretruth generator blob `07fd6649080f8355a62acbaf71abb739a47319bd`;
- old evaluator blob `b84422e9f037d6784b18943302a4c734777d8479`.

They cannot serve as the final scientific endpoint unchanged because the selected final method is density-synchronous recurrent-EOM and the new protocol requires three locked hierarchy outputs: ordinary HDBSCAN, recurrent-EOM, and #1263 density-synchronous.

A new pretruth generator and postfreeze evaluator must therefore be implemented and independently zero-data audited. Their truth semantics may be copied only insofar as they reproduce the frozen evaluator exactly.

## Exact final-method scientific source pins

- recurrent-EOM kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- density-synchronous kernel blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- #1263 binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.

No source derived from the abandoned post-closure FOSC-margin branch is eligible.

## Required zero-data audit sequence before any AMOS receipt

1. exact blind-receipt blob identity + synthetic boundary audit;
2. exact adapter identity + synthetic canonical-coordinate audit;
3. final pretruth generator audit proving one pooled hierarchy and three deterministic outputs before truth;
4. annual-EOM reconstruction identity for recurrent-EOM;
5. density-synchronous annual-integral reconstruction and `S_sync <= R` identity;
6. ordinary HDBSCAN partition identity;
7. postfreeze evaluator audit proving it accepts only the frozen pretruth payload + separate retained-ID labels and cannot recompute candidates;
8. optional comparator-supplement isolation audit;
9. machine-readable execution freeze pinning every source and audit artifact.

Only after all nine are complete may a compliant transfer be considered for scientific execution. Even then, sending the provider request remains a separate owner-authorized action.

## Firewall

No AMOS event row or label, SonotaCo row, ASFN/EFN row, MAARSY/DMS value, OrbitTrace target information, or protected `[20°,55°]` event is accessed by this reuse freeze.
