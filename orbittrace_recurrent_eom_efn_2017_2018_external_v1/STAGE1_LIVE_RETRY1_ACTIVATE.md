# Activate repaired EFN Stage-1 live retry 1

This marker authorizes one retry of the exact Stage-1 blind-index query after the first live run produced a technical no-result solely because VizieR returned the CSV alias `Obs_date` for semantic TAP column `Obs.date`.

Authorizers:

- unchanged scientific protocol blob `3b9c325205cdf4647c06674476858ae8fecbb145`
- TAP schema freeze blob `2a64e246534f5a41abfed8b8e725c723e2972b9e`
- original Stage-1 preaccess freeze blob `163ccfad7128e120fb7c0d18a154b3b6bf52b8f5`
- header-repair freeze blob `2419ea2821c77e148436dc4e15d3c17da785f678`
- repaired Stage-1 source blob `2b2d81a36cdf254746f19afbdc43525e9c5a2acf`
- repaired live workflow blob `fd169081682e515e854de8dc5d7e98c3444ba566`

The ADQL query is unchanged:

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

No geometry, velocity, shower, orbit, or other EFN field is authorized. The raw Stage-1 response must not be persisted.
