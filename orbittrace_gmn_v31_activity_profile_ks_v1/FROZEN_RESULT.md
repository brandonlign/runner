# Frozen result — GMN v31 activity-profile KS v1

Binding run: `31704233453`  
Binding job: `94460627181`  
Execution head: `a77b714262778e468b88d287c87af9c569279946`  
Artifact: `9182610619`  
Artifact digest: `sha256:b0f4667f29e0296c092e276aa3d2c29bb3eb46bf96ebe838b13a67d7cf2cc5ea`

Frozen protocol commit: `9e88764e251387daabbb65616093a891ce6abf1c`  
Frozen implementation commit: `0ff54ba16cb185d848693443123b341985d3825e`

Verdict: **FAIL_GMN_V31_ACTIVITY_PROFILE_KS_V1**

All preregistered source, raw-GMN runtime, P19, offline-package, exact 23D reconstruction, centroid, fold, parent-margin, evaluator, and firewall checks passed. The reconstructed 226x23 parent matrix was array-identical to the authoritative offline package and reproduced SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`. The exact parent raw OOF margin reproduced SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

Exact v31 parent:

- @25 = **23**
- @50 = **41**
- @100 = **66**
- top-100 precision = **0.7229521515453452**
- MRR = **0.050244164168646674**
- qualified = **95**

Frozen 24D activity-profile-KS fusion:

- @25 = **23**
- @50 = **41**
- @100 = **68**
- top-100 precision = **0.7358676330643921**
- MRR = **0.050193677058155625**
- qualified = **95**

Frozen local-only activity-KS order:

- @25 = **22**
- @50 = **38**
- @100 = **64**
- top-100 precision = **0.6453280994832926**
- MRR = **0.03713604427218427**
- qualified = **95**

Gate result:

- @100 >66: **PASS** (68)
- @25 >=23: **PASS**
- @50 >=41: **PASS**
- precision >= parent: **PASS**
- qualified =95: **PASS**
- MRR >= `0.050244164168646674`: **FAIL** (`0.050193677058155625`)

This is therefore a binding scientific failure despite the genuine +2 top-100 recovery and precision improvement. It does **not** authorize SonotaCo access.

Frozen hashes:

- activity KS vector: `393457fe5d051e6976b6c58fdc5bf21ca541c0a07cb9709a9f0f0351970fbe40`
- candidate raw margin: `b3899e9ac71bff0b4e4ef3680849997ec5815caa92ad6cf6af0fb98562901dcf`
- candidate fused order: `903719ddabbae801b2e64165732947f85ba734101fb819bfbf5645723fa7c78c`

Scientific interpretation: the one new physical observable supplied information absent from the frozen 23D geometry and broadened top-100 recovery, but the exact candidate failed the preregistered MRR preservation criterion. This supports representation augmentation with genuinely new physical observables as a general research direction; it does not justify tuning or substituting another activity-profile statistic.

Permanent closure: no alternate KS axis/centering, p-value, histogram/KDE, Wasserstein/energy/MMD/CvM/AD/Kuiper/JS statistic, width/FWHM/IQR/MAD, skewness/kurtosis/multimodality, activity-peak count, transform, threshold, weight, blend, metric, k, reference, diversity, or fusion rescue derived from this result.

Protected solar longitude 20–55 degrees remained inaccessible. No OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, or DMS was accessed.