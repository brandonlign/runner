# EFN Stage-1 exact-360 solar-longitude wrap repair

**Classification: engineering/provenance repair inherited from the already-promoted recurrent-EOM input normalization; no new scientific rule.**

## Triggering technical no-result and diagnostic

Live Stage-1 retry 2 (`31835001724`, job `94879228888`, head `1c6da459f169a7762c8bbb4a04b1bd5cab10dca2`) stopped before a valid retained-ID freeze because one blind-index row failed the temporary transport-domain assertion `0 <= Lsun < 360`:

`invalid EFN Lsun for EN200318_231813`

Technical artifact: `9232135869`, digest `sha256:794f5887dedec28c887ad7b0f313aba4bfcd0a4931c886ab77c5a83a936fe666`.

A separately frozen blind-field-only transport diagnostic then repeated the unchanged Stage-1 query and inspected no geometry, velocity, shower, orbit, or other scientific field:

- diagnostic run: `31835275974`
- job: `94880091916`
- head: `3378e500430b06d28042e8471d706fab84779979`
- artifact: `9232234728`
- digest: `sha256:92a020a308be4b5b320ef13c271e4ca4db1af8b82fd91ea9b7b427dd7186f8c8`
- verdict: `PASS_RECURRENT_EOM_EFN_STAGE1_LSUN_TRANSPORT_DIAGNOSTIC`
- rows inspected: 824 blind-index rows
- invalid/out-of-domain `Lsun` count under the temporary `[0,360)` transport assertion: exactly `1`
- sole row: `Code=EN200318_231813`, raw `Lsun=360.0`, reason `GE_360`
- no non-numeric, non-finite, negative, or `>360` value was observed.

The diagnostic produced no retained IDs and no scientific endpoint.

## Authoritative promoted normalization

The promoted recurrent-EOM development runner, frozen before EFN existed, normalizes incoming solar longitude as:

```python
sol = event_field(row, ("sol", "solar_longitude", "solar_lon", "sol_lon")) % 360.0
```

and only then enforces the protected interval. The authoritative promoted runner Git blob is:

`fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`

The authoritative recurrent-EOM method Git blob remains:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Therefore raw `360.0°` and canonical `0.0°` are already exactly the same solar-longitude input under the promoted method. Treating EFN's single `360.0` boundary value as canonical `0.0` restores the existing method normalization; it does not create an EFN-specific scientific transform.

## Sole authorized Stage-1 repair

Keep the live ADQL query byte-for-byte unchanged:

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

For every returned blind-index row:

1. parse raw `Lsun` as float;
2. require it finite;
3. require `0.0 <= raw_Lsun <= 360.0`;
4. reject every value `<0.0` or `>360.0`;
5. canonicalize exactly as the promoted method: `sol = raw_Lsun % 360.0`;
6. apply the inclusive protected interval to **canonical** `sol`: `20.0 <= sol <= 55.0`;
7. record only an aggregate count of rows where raw `Lsun == 360.0`; do not persist raw or canonical solar-longitude values.

No tolerance around 360 is allowed. `360.000001` remains invalid. The only representational boundary accepted beyond the original half-open domain is exact finite `360.0`, which canonicalizes exactly to `0.0`.

The known diagnostic row `EN200318_231813` therefore remains eligible for the retained-ID allowlist if all other Stage-1 checks pass, because its promoted canonical solar longitude is `0.0°`, outside the protected interval.

## Stage-2 consistency requirement

Any future EFN Stage-2 geometry adapter must apply the same promoted `% 360.0` solar-longitude normalization before constructing GEO6 and before the protected-region assertion. The raw server-side filter `Lsun < 20.0 OR Lsun > 55.0` may return raw `360.0`; that value must enter recurrent-EOM only as canonical `0.0`.

No other coordinate or velocity transform is authorized.

## No scientific change

This repair does not alter:

- the fixed 824-row EFN cohort;
- years 2017/2018;
- selected Stage-1 columns;
- the protected interval `[20.0,55.0]`;
- recurrent-EOM/HDBSCAN parameters;
- GEO6 or its speed scale;
- annual normalization or recurrent-stability rule;
- candidate ranking;
- Stage-3 truth mapping;
- evaluator or validation gate.

Firewall at repair freeze:

- `valid_stage1_endpoint=false`
- `retained_ids_frozen=false`
- `raw_stage1_response_persisted=false`
- `efn_geometry_accessed=false`
- `efn_shower_labels_accessed=false`
- `target_information_access=false`
- `target_region_physical_values_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `orbittrace_target_access=false`
