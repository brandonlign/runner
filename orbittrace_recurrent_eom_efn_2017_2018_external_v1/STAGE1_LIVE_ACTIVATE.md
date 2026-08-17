# Activate frozen EFN Stage-1 blind receipt

This marker activates exactly one live Stage-1 blind-index execution after both prerequisite zero-data audits passed.

Frozen authorizers:

- scientific protocol blob: `3b9c325205cdf4647c06674476858ae8fecbb145`
- promoted recurrent-EOM method blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`
- TAP schema freeze blob: `2a64e246534f5a41abfed8b8e725c723e2972b9e`
- successful TAP schema audit: run `31834003387`, artifact `9231769088`, digest `sha256:0da2f7d9c9f551b12f9fd38995c891573e00b50228b4ce01228930a52c885873`
- Stage-1 preaccess freeze blob: `163ccfad7128e120fb7c0d18a154b3b6bf52b8f5`
- successful Stage-1 synthetic audit: run `31833492435`, artifact `9231583848`, digest `sha256:72fb9198d5ea74f0d4df380bb2de063c1ea2b81ad6b3c97aba1ed227f4d4e74d`
- Stage-1 source blob: `61c6589ace0c5d36d83b7eb506c76200e0aa57ce`
- registered live workflow blob: `972834baf522f61abb4f3b0b12fd4c90aa8c61dc`

The only event-level query authorized by this marker is:

```sql
SELECT Code, "Obs.date", Lsun
FROM "J/A+A/667/A157/catalog"
```

No geometry, velocity, shower label, orbit, or other EFN scientific field is authorized at Stage 1. The raw 824-row response must not be persisted or uploaded. Only retained-ID allowlists/hashes and aggregate blind-receipt counts may survive the run.

A Stage-1 technical failure authorizes only an engineering transport/parser repair that cannot expose additional EFN columns. It does not authorize Stage 2.
