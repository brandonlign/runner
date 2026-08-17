# Activate corrected EFN Stage-1 live retry 5

Authorized by the successful synthetic generic-modulo audit frozen in `STAGE1_GENERIC_MODULO_REPAIR_FREEZE.json`.

This activation changes no science. It restores the already-promoted recurrent-EOM solar-longitude normalization (`raw_Lsun % 360.0`) for all finite blind-index values before applying the inclusive protected interval `[20,55]`.

The sole live query remains:

```sql
SELECT Code, "Obs.date", Lsun FROM "J/A+A/667/A157/catalog"
```

No EFN geometry, shower label, orbit field, target information, MAARSY, or DMS access is authorized here.
