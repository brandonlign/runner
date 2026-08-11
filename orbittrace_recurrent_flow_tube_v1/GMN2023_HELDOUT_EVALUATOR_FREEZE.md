# RFT v1 GMN 2023 held-out evaluator freeze

This file freezes the exact held-out evaluation code path for the already-frozen Recurrent Flow-Tube v1 methodology **before any GMN 2023 access by this branch**.

Scientific parent: `orbittrace_recurrent_flow_tube_v1/PROTOCOL.md`, blob `515362e69bec642a891e44dfd87dce9693942574`.

Exact RFT implementation parent: `orbittrace_recurrent_flow_tube_v1/run_development.py`, blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`.

The held-out evaluator changes no RFT scientific constant or algorithm. At execution time it must first verify an immutable GMN 2022 development artifact whose verdict is exactly `PASS_RFT_V1_GMN2022_DEVELOPMENT_VIABILITY`, whose role is `TARGET_EXCLUDED_GMN_2022_DEVELOPMENT_ONLY`, and whose `gmn_2023_access` flag is false. If the 2022 gate does not pass, the evaluator must terminate before catalogue parsing and GMN 2023 remains inaccessible.

Only after that authorizer passes, the evaluator sets the exact frozen runtime year to `2023`, the source list to the twelve fixed `2023-01` through `2023-12` months, and runs the unchanged RFT v1 event-level detector on target-excluded GMN 2023.

The held-out metrics and verdict are exactly those already preregistered in the parent protocol:

- full-catalogue qualified known showers;
- recovered@25, @50, @100, @500;
- top-100 dominant precision;
- MRR;
- fragmentation median among recovered known showers within top 500.

`PASS` requires all five numerical gates:

1. qualified known showers >= 120;
2. recovered@100 >= 58;
3. recovered@50 >= 35;
4. top-100 dominant precision >= 0.65;
5. fragmentation median <= 3.0;

and every provenance/firewall assertion.

`USEFUL_BUT_INSUFFICIENT` requires every provenance/firewall assertion, at least four of those five numerical gates, and recovered@100 >= 52. Otherwise the verdict is `FAIL`.

The only preregistered post-result mechanism flags are descriptive and do not alter candidate order:

- `coverage_failure = qualified_matches < 120`;
- `ranking_failure = qualified_matches >= 120 and recovered_at_100 < 58`;
- `fragmentation_failure = fragmentation_median_top500 > 3.0`;
- `purity_failure = top100_dominant_precision < 0.65`.

No 2023 ablation, threshold search, score change, reranking, candidate modification, source quota, feature/model fit, or alternate metric is allowed. No GMN 2023 result may change RFT v1.

SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY, DMS, and the protected solar-longitude interval `[20°,55°]` remain inaccessible.