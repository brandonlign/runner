# Activate frozen EFN Stage-1 Lsun transport diagnostic

This marker authorizes one engineering-only diagnostic execution after Stage-1 retry 2 stopped on `Lsun` validation for `EN200318_231813`.

Frozen diagnostic:

- diagnostic protocol blob `590ff886a53655ff00424d2eae16951ec4a1b769`
- diagnostic source blob `c5065b5d18a46df5fe642be2ef2c66ee3d4e0a0b`
- diagnostic workflow blob `4f17372ddceb10544aee1e4f9f09cade7197998f`
- scientific protocol blob `3b9c325205cdf4647c06674476858ae8fecbb145`
- TAP schema freeze blob `2a64e246534f5a41abfed8b8e725c723e2972b9e`
- date-encoding repair freeze blob `5c5c373cc055ceb03498aa37fac46803e6f38f0c`

The diagnostic repeats only the unchanged Stage-1 blind query:

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

It may persist only invalid `Lsun` rows as `Code`, raw `Lsun`, and mechanical reason. It must not produce retained IDs, inspect geometry or labels, persist valid solar-longitude values, or create a scientific endpoint.
