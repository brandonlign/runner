# Final #1263 AMOS runtime-lock audit activation

Zero-scientific-data activation only.

This marker tests the explicit runtime lock against the already-binding exact-label current-evaluator audit outputs.

Pinned runtime:
- Python `3.11.15`;
- NumPy `2.1.3`;
- SciPy `1.14.1`;
- scikit-learn `1.7.1`;
- HDBSCAN `0.8.43`;
- joblib `1.5.3`;
- threadpoolctl `3.6.0`.

Pinned files:
- runtime requirements blob `153e96877e860e7c0d3ad0e961f44861f619cc66`;
- Python marker blob `d8292d992d92d92c184209f9bbc655c93693b3bf`;
- runtime requirement document blob `3786e0a9af6e5e99af12b9a061713d206fb73ddc`;
- authoritative freeze blob `beed71cac547973b198b6ed16e319ebe42051583`;
- current evaluator blob `c45e4739ea68639945b13de54f6e24dc9d870ba3`;
- runtime audit workflow blob `02b58c87dc6a76438c3c297bb2e67b134b25b13e`.

The audit must install only from the exact lock and reproduce the already-binding result SHA-256 values:
- source `63d53aff1a056e6be67347f6adc3ba453c9851833b3ebc2a56ec380318a2e439`;
- pipeline `d354d042a4dc057bae89aa46df2d684292fedb05badcdbcffe8e50bba7fe73c9`;
- hardening `0de496d2f3b42111f39759c51c96063128b23eb063571174d96c42400d5bbe25`;
- exact label transport `fff8d9777e83acbf1940a94429bee6ee2809721c5e946a3c3cfa2207ad060427`.

No provider request, AMOS scientific data, GMN, SonotaCo, ASFN, EFN, OrbitTrace target information/geometry, MAARSY, or DMS is authorized.