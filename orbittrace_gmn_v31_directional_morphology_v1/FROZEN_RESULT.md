# Frozen result — GMN v31 directional morphology recurrence v1

Binding run: `31762234568`  
Binding job: `94650840712`  
Execution head: `0f67c4dbdb7ad4f36b107bd6782448f931d5706e`  
Artifact: `9205070872`  
Artifact digest: `sha256:d051cd5375c3e858180553ae74e138b8b5853b4cc68157433e29322e5d307ccd`

Frozen protocol commit: `9e3560fd6556a38c9c22ad3123eea0193b08024a`  
Frozen protocol blob: `46e880d874bc9aa8fcd6156e3dc9737725ac0ad3`  
Frozen implementation commit: `29dc2e0cf417574de00e608a7bac0d99f6d7d572`  
Frozen implementation blob: `c92802d90ed4c19f678660f65d52c585229969b6`

Verdict: **FAIL_GMN_V31_DIRECTIONAL_MORPHOLOGY_V1**

All preregistered source, runtime, immutable-artifact, exact 23D reconstruction, centroid, fold, parent-margin, evaluator, and firewall checks passed. The first technically valid outcome is therefore binding.

Exact v31 parent:

- @25 = **23**
- @50 = **41**
- @100 = **66**
- top-100 precision = **0.7229521515453452**
- MRR = **0.050244164168646674**
- qualified = **95**

Frozen 24D directional-morphology fusion:

- @25 = **24**
- @50 = **38**
- @100 = **67**
- top-100 precision = **0.7251741598709189**
- MRR = **0.05029427953243564**
- qualified = **95**

Frozen local-only directional-morphology order:

- @25 = **21**
- @50 = **37**
- @100 = **62**
- top-100 precision = **0.623257180206491**
- MRR = **0.03667138346898046**
- qualified = **95**

Gate result:

- @100 >66: **PASS** (67)
- @50 >=41: **FAIL** (38)
- @25 >=23: **PASS** (24)
- precision >= parent: **PASS**
- MRR >= parent: **PASS**
- qualified =95: **PASS**

This is a binding scientific failure because every preregistered gate was required. It does **not** authorize SonotaCo access.

Frozen hashes:

- directional morphology vector: `c58e7900e8d26984779cc8a43537a6f10fd638165bff60b13733a99a4ffba264`
- candidate raw margin: `7aea02f461d50cc40d79bae18773b1ea60281ed52d63c47bd5d75afad6aa31c4`
- candidate fused order: `7597bc0a44d72bf663c027b035e63a01c4badd6085069f8d439f6f6de7e4b22d`

Feature distribution (for provenance, not rescue selection):

- all families: min `0.03628677019020229`, median `0.41844828511138177`, max `0.8192095152921408`
- positive families: min `0.0823842553169247`, median `0.4129576141244552`, max `0.8192095152921408`
- nonpositive families: min `0.03628677019020229`, median `0.43146418619585686`, max `0.7573086206687112`

Scientific interpretation: the fixed directional-shape recurrence coordinate perturbed the exact v31 ranking in a partly favorable way, improving @25, @100, top-100 precision, and MRR, but it materially harmed the preregistered @50 recovery gate. The lane is therefore rejected rather than tuned.

Permanent closure under the frozen protocol: no outcome-informed rescue using eigenvalue-only variants, principal-axis angles, determinants, anisotropy/eccentricity summaries, covariance/correlation alternatives, shrinkage/ridge, signed or squared Frobenius changes, alternate normalization, added radial/width terms, multiple tensor coordinates, thresholds, transforms, weights, feature subsets, metric/k/scaling changes, reference changes, or fusion/diversity changes.

Protected solar longitude 20°–55° remained inaccessible. No OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, or DMS was accessed.