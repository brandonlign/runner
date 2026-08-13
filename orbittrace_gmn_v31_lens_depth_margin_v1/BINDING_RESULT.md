# GMN v31 lens-depth margin v1 — binding result

Status: **FAIL — permanently closed**.

First technically valid run: GitHub Actions `31665094820`, job `94337839317`, commit `87cc4dfdbe4c9f380deb2d281978899c766a3873`, artifact `9167618039`, artifact digest `sha256:f34c5580423a453a8248ab8c732970946e5d98871379e148a3f4261bd5e4aa46`.

The run used only the authoritative target-excluded GMN v31 offline package and exact pinned evaluator/diversity source. It reproduced the exact immutable hard-order development control before candidate scoring.

Exact v31 GMN parent control:

- recovered@25 = 23
- recovered@50 = 41
- recovered@100 = 66
- top-100 dominant precision = 0.7229521515453452
- MRR = 0.050244164168646674
- qualified matches = 95

Frozen maximum-lens-depth successor after exact inherited diversity and equal hard-order fusion:

- recovered@25 = **23**
- recovered@50 = **44**
- recovered@100 = **65**
- recovered@500 = 95
- top-100 dominant precision = **0.7148286576501794**
- MRR = **0.05065513910833264**
- qualified matches = 95

Lens-depth local-only order:

- recovered@25 = 22
- recovered@50 = 39
- recovered@100 = 64
- recovered@500 = 95
- top-100 dominant precision = 0.6341853515952921
- MRR = 0.045982783695164745
- qualified matches = 95

Lens-margin SHA-256: `6816e4f8afe64c38226248770986762a817057ed8884127c307a3cb7c42c19a3`.

Binding gates:

- recovered@100 strictly better than parent: **FAIL** (65 < 66)
- recovered@50 nonregression: **PASS** (44 > 41)
- recovered@25 nonregression: **PASS** (23 = 23)
- top-100 precision nonregression: **FAIL** (0.7148286576501794 < 0.7229521515453452)
- MRR nonregression: **PASS** (0.05065513910833264 > 0.050244164168646674)
- qualified count identical: **PASS** (95)

The failure was not caused by high-dimensional zero-depth collapse. Across all folds, positive class depths had only three zero cases and nonpositive class depths had three zero cases in total; fold median depths were broadly in the 0.24–0.36 range. The parameter-free pairwise depth geometry therefore produced a meaningful nondegenerate ranking, but that ranking did not beat v31 at the primary @100 gate and reduced top-100 precision.

Therefore `GMN_V31_LENS_DEPTH_MARGIN_V1` is not promotable and does not authorize SonotaCo access.

Per the frozen protocol, no weighted lens depth, local/trimmed lens depth, DD-plot classifier, downstream linear/nonlinear classifier, alternate boundary convention, pair subsampling/weighting, class-prior weighting, depth transform, v31-margin blend, k-RNG classifier, feature/metric/scaling/diversity/fusion change, or result-informed rescue is authorized.

Interpretation: full pairwise class-centrality contains some useful early-ranking signal (@50 and MRR improve), but replacing v31's nearest-prototype contrast with the canonical maximum lens-depth contrast weakens primary top-100 recovery and purity. This does not justify iterating through nearby lens-depth variants.

Scientific firewall remained intact: only the target-excluded GMN 2022+2023 offline development package was accessed; no raw event rows/IDs, SonotaCo 2013/2014, protected 20°–55° target-region data, OrbitTrace target information/events, MAARSY, or DMS were accessed.
