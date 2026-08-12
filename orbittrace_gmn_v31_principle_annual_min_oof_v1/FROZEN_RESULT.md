# Frozen result — GMN v31-principle annual-min OOF diagnostic v1

Binding run: `31564075286`
Binding job: `94012217032`
Execution head: `0e5cbffbf7bf4e970ba938901bb3945da6c54891`

Verdict: `FAIL_GMN_V31_PRINCIPLE_ANNUAL_MIN_OOF`

The parent control reproduced exactly before the successor was interpreted:
- parent margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- recovered@100: `66`
- recovered@50: `41`
- top-100 dominant precision: `0.7229521515453452`
- MRR: `0.050244164168646674`
- qualified families: `95`

Binding annual-min candidate:
- recovered@100: **61**
- recovered@50: **35**
- top-100 dominant precision: **0.6587262649474493**
- MRR: **0.04775968142019496**
- qualified families: **95**
- combined annual-min margin SHA256: `f461689f7e8c2eb90e3fe9e4728a077fe036bdbda17c74bf0152ada45187e659`

Artifact:
- ID: `9128846397`
- digest: `sha256:9e1e68e7d51b0993c61d5c15317454fe04456b4ebb21dce9efdb6093e2cde4a5`

Scientific conclusion: making the successful GMN local-geometry signal explicitly year-specific and conservatively taking the minimum degrades every ranking metric versus the binding 66-family parent. The annual-min mechanism is permanently rejected for this GMN representation.

No alternate annual threshold, annual label rule, mean/max/product combiner, k, metric, feature, scaling, diversity, fusion, or post-result rescue is authorized.

Firewall remained clean: SonotaCo 2013/2014, protected 20°–55° target information/events, MAARSY, and DMS were not accessed.
