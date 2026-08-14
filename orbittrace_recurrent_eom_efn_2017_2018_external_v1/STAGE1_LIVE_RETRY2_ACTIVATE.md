# Activate EFN Stage-1 live retry 2 after sec/2000 repair

This marker authorizes one retry of the exact Stage-1 blind-index query after live retry 1 produced a technical no-result solely because VizieR returns `Obs_date` as an integer `sec/2000` time value.

Authorizers:

- scientific protocol blob `3b9c325205cdf4647c06674476858ae8fecbb145`
- promoted recurrent-EOM method blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`
- TAP schema freeze blob `2a64e246534f5a41abfed8b8e725c723e2972b9e`
- original Stage-1 preaccess freeze blob `163ccfad7128e120fb7c0d18a154b3b6bf52b8f5`
- returned-header repair freeze blob `2419ea2821c77e148436dc4e15d3c17da785f678`
- date-encoding repair freeze blob `5c5c373cc055ceb03498aa37fac46803e6f38f0c`
- date-repaired Stage-1 source blob `95c0b034cf1ab98237a019a01df79bc7c70d11fd`
- live retry-2 workflow blob `bd64e17506017374d0814d11102c5074291782a6`

The ADQL query remains byte-for-byte unchanged:

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

Returned `Obs_date` is parsed only to the frozen calendar year using VizieR `sec/2000` boundaries. No timestamp is persisted.

No geometry, velocity, shower, orbit, or other EFN field is authorized. The raw Stage-1 response must not be persisted.
