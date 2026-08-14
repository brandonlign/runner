# Activate EFN Stage-1 live retry 4

This activation is authorized solely by `STAGE1_RETRY3_PIN_MISMATCH.md`.

Science and access boundary are unchanged. The only repair since retry 3 is the workflow assertion for the already-frozen `STAGE1_SOLAR_WRAP_REPAIR_FREEZE.json` Git blob (`3a4b0ccbd098944e2279d2f3bf9404a523b7ac68`).

The sole live query remains:

```sql
SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"
```

No geometry, shower label, orbit field, target information, MAARSY, or DMS access is authorized by this activation.
