# GMN v31 Tomek negative-reference editing v1 — binding result

Binding run: `31654096810` on commit `7620be5c9a6f2bb6c1d56e39af020f2820c9649d`.
Artifact: `9163772016`, digest `sha256:d3cb08bc779ae85299313d59dcbbb92ccdb39ca43e0ab14f57b6015e36f98e7e`.

Verdict: `FAIL_GMN_V31_TOMEK_NEGATIVE_EDIT_V1`.

Exact parent reproduced:
- recovered@25: 23
- recovered@50: 41
- recovered@100: 66
- recovered@500: 95
- top-100 dominant precision: 0.7229521515453452
- MRR: 0.050244164168646674
- qualified matches: 95

Frozen single-pass Tomek-negative edit:
- recovered@25: 23
- recovered@50: 41
- recovered@100: 67
- recovered@500: 95
- top-100 dominant precision: 0.7332227143159079
- MRR: 0.05003580034901832
- qualified matches: 95

Fold-level removed nonpositive references / original nonpositive references:
- fold 0: 20 / 87
- fold 1: 16 / 87
- fold 2: 12 / 98
- fold 3: 14 / 91
- fold 4: 13 / 97

Binding gates:
- recovered@100 strictly better: PASS (67 > 66)
- recovered@50 nonregression: PASS (41 = 41)
- recovered@25 nonregression: PASS (23 = 23)
- top-100 precision nonregression: PASS (0.7332227143159079 > 0.7229521515453452)
- qualified count identical: PASS (95)
- MRR nonregression: FAIL (0.05003580034901832 < 0.050244164168646674)

Therefore the method is not promotable and does not authorize SonotaCo access.

This exact lane is closed as preregistered: no positive-endpoint deletion, both-endpoint deletion, repeated/iterative Tomek editing, cross-class-only nearest-neighbor variant, k-neighbor generalization, distance threshold, alternate tie break, edited-nearest-neighbor rule, class weighting, fusion change, or result-informed rescue may be selected from this outcome.

SonotaCo 2013/2014 was not accessed. Protected 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remained inaccessible.