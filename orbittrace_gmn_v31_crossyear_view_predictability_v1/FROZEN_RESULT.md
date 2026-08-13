# Binding result — FAIL

Frozen protocol commit `a0dfaa4eb14abd6f920ed37e9e608e85f74c0eff`.

Exact P19 prelabel SHA-256 reproduced: `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`.
Exact v31 parent feature/centroid/margin hashes and metrics reproduced before candidate scoring.

Paired-view error SHA-256: `3bd1710722b42b9f326d3d88c922d1a11432f47cd7cb4177ac4dcecaaa8b5d02`.
Candidate margin SHA-256: `94d12cc1e15a1b7e0eafad187c4e9fa5e3da8a61da17a40709f866a5e665dc95`.
Candidate fused-order SHA-256: `e472fdea644b47e7618e643beab4d5ebd5d9b3d1f66ddc2644f2a0cf1350e0e7`.

Parent -> candidate:
- @25: `23 -> 22`
- @50: `41 -> 42`
- @100: `66 -> 65`
- top-100 dominant precision: `0.7229521515453452 -> 0.7244872392646434`
- MRR: `0.050244164168646674 -> 0.04976712750680706`
- qualified: `95 -> 95`

Verdict: `FAIL_GMN_V31_CROSSYEAR_VIEW_PREDICTABILITY_V1`.

The exact self-supervised annual-view prediction mechanism is closed. No annual-view subset/addition, alternate regression/loss/direction, nonlinear map, weighting, or v31 ranking rescue is authorized. No SonotaCo benchmark was run; protected 20-55, OrbitTrace target information/events, MAARSY and DMS were not accessed.