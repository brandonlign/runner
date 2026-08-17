# Activate EFN Stage-1 live retry 3 after promoted modulo-360 repair

This marker authorizes one retry of the exact blind-index query after the frozen Lsun transport diagnostic established that the only temporary-domain exception in the fixed 824-row release is exact raw `Lsun=360.0`, and the promoted recurrent-EOM runner was independently verified to canonicalize solar longitude with `% 360.0` before protected-region exclusion.

Authorizers:

- scientific protocol blob `3b9c325205cdf4647c06674476858ae8fecbb145`
- promoted recurrent-EOM method blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`
- promoted runner blob `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`
- TAP schema freeze blob `2a64e246534f5a41abfed8b8e725c723e2972b9e`
- Stage-1 returned-header repair freeze blob `2419ea2821c77e148436dc4e15d3c17da785f678`
- Stage-1 date-encoding repair freeze blob `5c5c373cc055ceb03498aa37fac46803e6f38f0c`
- Stage-1 solar-wrap repair freeze blob `c6ed3fc90c45764c8101f62a993edb189502bb99`
- modulo-360 Stage-1 source blob `eb4f3e44ccb92a96d9ac7bb77622fbab805c46ea`
- live retry-3 workflow blob `95340be232d48ac6844ce85061a4104e2c4eb62e`

The ADQL query remains byte-for-byte unchanged:

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

Raw finite `Lsun` is accepted only on `[0,360]`, canonicalized as `raw_Lsun % 360.0`, and the protected interval is applied to that canonical value. Exact `360.0` therefore becomes exact `0.0`; values below 0 or above 360 remain forbidden.

No geometry, velocity, shower, orbit, or other EFN field is authorized. The raw Stage-1 response must not be persisted.
