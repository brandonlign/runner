# Frozen result — v62 intrinsic-representation strict-OOF local-geometry margin v1

Binding run: `31563692176`
Binding job: `94011063633`
Execution head: `e357e9e789d460610e85cf2b58bf766301c0105b`

Verdict: `FAIL_V62_INTRINSIC_LOCAL_GEOMETRY_ALL_FOUR_LITERATURE_SUPERIORITY_PAIRS`
Panel wins: **2/4**

Frozen pretruth representation:
- overall pretruth SHA256: `1988fcb89781a3ba94d19bd7b2e0c058c13b39c73ed020f7931c772952069e64`
- Sugar 23D feature SHA256: `423c9aef746cd873270cf8950ce79d93620282d12161449ebc99863f748834c7`
- HDBSCAN 23D feature SHA256: `e0a8162e2b4d73df68552d56f0f81305e28cda1fc539d9e88943e42fb3394663`
- exact columns: `(1,2,3,4,5,6,7,8,9,10,14,15,16,17,18,19,20,28,29,30,31,32,33)`

Binding panels:

- Sugar 2013: v62 `0.255139876469369 / 14`; literature `0.20372657466522806 / 13`; v31 parent `0.2719801488280529 / 16` — literature pair PASS, worse than v31.
- Sugar 2014: v62 `0.2929300045717354 / 16`; literature `0.25901527732153334 / 15`; v31 parent `0.31529041952487225 / 17` — literature pair PASS, worse than v31.
- HDBSCAN 2013: v62 `0.1447372411290561 / 8`; literature `0.16813025050497152 / 10`; v31 parent `0.14888037368183737 / 9` — FAIL, worse than v31.
- HDBSCAN 2014: v62 `0.14263780337958157 / 8`; literature `0.15689595582646423 / 9`; v31 parent `0.15198123772301594 / 9` — FAIL, worse than v31.

Artifact:
- ID: `9128654239`
- digest: `sha256:4bf784a601583526a62736f7f79809ba4cfd1f786ec065c34b630c2b639d792d`

Scientific conclusion: the exact GMN-validated 23D intrinsic representation does not improve the v31 SonotaCo parent when substituted as the sole representation change. It retains the two Sugar literature wins but degrades all four panels relative to v31 and fails both HDBSCAN literature panels. v62 is permanently rejected.

No column, feature, scaling, k, metric, annual reference, annual combiner, diversity, fusion, threshold, source quota, or membership rescue is authorized.

SonotaCo role remains exposed development only. Protected 20°–55° target information/events, MAARSY, and DMS remained inaccessible.
