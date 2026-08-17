# EFN Stage-1 solar-longitude transport correction

**Classification: engineering/provenance correction restoring the already-promoted recurrent-EOM normalization. No new scientific rule.**

## Why this correction is required

The frozen blind-field diagnostic run `31835275974` (job `94880091916`, artifact `9232234728`, digest `sha256:92a020a308be4b5b320ef13c271e4ca4db1af8b82fd91ea9b7b427dd7186f8c8`) directly printed four Stage-1 `Lsun` values outside the temporary `[0,360)` transport assertion:

- `EN200318_231813`: `360.0466`
- `EN200318_225527`: `360.0309`
- `EN220318_005247`: `361.1052`
- `EN220318_023230`: `361.1739`

A later record, `STAGE1_SOLAR_WRAP_REPAIR_FREEZE.json`, incorrectly summarized the diagnostic as a single exact `360.0` row. That summary is therefore superseded for transport interpretation. The original file is preserved unchanged as part of the audit history.

Live retry 4 (`31840806463`, job `94897028152`, head `05a47cacd261827f6ea8eab96a5dfb311c056bc1`) confirmed the mismatch operationally: all provenance gates passed, the frozen blind-only query executed, and Stage 1 stopped on `EN200318_231813` because `360.0466` is greater than the temporary exact-360 ceiling. No retained-ID endpoint was produced.

## Authoritative inherited rule

The recurrent-EOM method was promoted before EFN and normalizes solar longitude in `run_development.py` as:

```python
sol = event_field(row, ("sol", "solar_longitude", "solar_lon", "sol_lon")) % 360.0
```

Pinned promoted runner Git blob:

`fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`

Pinned recurrent-EOM method Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Therefore the correct EFN transport behavior is not an exact-360 special case. It is the already-promoted generic normalization:

1. parse raw `Lsun` as float;
2. require finite;
3. set `canonical = raw_Lsun % 360.0` with no survey-specific range clamp;
4. require `0 <= canonical < 360`;
5. apply the protected interval only to canonical longitude: `20 <= canonical <= 55`;
6. persist only aggregate counts of rows that required modulo wrapping (`raw < 0` or `raw >= 360`), never the raw/canonical values.

This also means a hypothetical finite negative or multi-turn value is handled exactly as the promoted method would handle it; nonfinite values still fail closed.

## No scientific change

Unchanged:

- catalogue cohort: fixed 824 EFN rows;
- years: 2017/2018;
- Stage-1 query: `SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"`;
- protected interval: inclusive `[20,55]` after canonicalization;
- recurrent-EOM/HDBSCAN parameters;
- GEO6;
- annual normalization and recurrent-stability definition;
- candidate extraction/ranking;
- Stage-2/Stage-3 separation;
- evaluator and external-validation gate.

Firewall at correction freeze:

- valid Stage-1 endpoint: false
- retained IDs frozen: false
- EFN geometry accessed: false
- EFN shower labels accessed: false
- target information accessed: false
- target-region physical values accessed: false
- MAARSY scientific access: false
- DMS scientific access: false
- OrbitTrace target access: false
