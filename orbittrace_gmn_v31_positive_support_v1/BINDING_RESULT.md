# GMN v31 positive-support local geometry v1 — binding result

Status: **FAIL — permanently closed**.

First technically valid run: GitHub Actions `31663926607`, job `94334384429`, commit `925a82210e06776121a6d539003992b700605142`, artifact `9167213431`, artifact digest `sha256:a0de544a90e21c65d828f5a32115abc743c75f96091dc9079f02ef4c6d783c86`.

The run used only the authoritative offline target-excluded GMN v31 package (artifact `9167087908`, digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`) and the exact pinned diversity/evaluator source. No raw GMN event rows, raw event IDs, or raw hidden-label event mapping were accessed.

Before successor scoring, the offline evaluator reproduced the exact immutable hard-order control:

- recovered@25 = 21
- recovered@50 = 38
- recovered@100 = 59
- top-100 dominant precision = 0.6884631112636006
- MRR = 0.046734076055452344
- qualified matches = 95

Exact v31 GMN parent control:

- recovered@25 = 23
- recovered@50 = 41
- recovered@100 = 66
- top-100 dominant precision = 0.7229521515453452
- MRR = 0.050244164168646674
- qualified matches = 95

Frozen positive-support successor after exact parent diversity and equal hard-order fusion:

- recovered@25 = **17**
- recovered@50 = **29**
- recovered@100 = **47**
- recovered@500 = 95
- top-100 dominant precision = **0.5414709009524469**
- MRR = **0.043369172891473476**
- qualified matches = 95

Positive-support local-only order:

- recovered@25 = 11
- recovered@50 = 18
- recovered@100 = 37
- recovered@500 = 95
- top-100 dominant precision = 0.3806029082674664
- MRR = 0.02101913885512405
- qualified matches = 95

Positive-support score SHA-256: `575044169160c5ee532ef48f325243d74ca94bfc9c8924205864ba6879cc9993`.

Binding gates:

- recovered@100 strictly better than parent: **FAIL** (47 < 66)
- recovered@50 nonregression: **FAIL** (29 < 41)
- recovered@25 nonregression: **FAIL** (17 < 23)
- top-100 precision nonregression: **FAIL** (0.5414709009524469 < 0.7229521515453452)
- MRR nonregression: **FAIL** (0.043369172891473476 < 0.050244164168646674)
- qualified count identical: **PASS** (95)

Therefore `GMN_V31_POSITIVE_SUPPORT_V1` is not promotable and does not authorize SonotaCo access.

Per the preregistered protocol, this exact one-class positive-support lane is closed. No `k>1`, normalized positive distance, nearest-neighbor-of-nearest-neighbor normalization, target-density ratio, thresholded support, positive-reference pruning/weighting, hard/local blend weight, feature/metric/scaling/diversity/fusion change, or result-informed rescue is authorized.

Interpretation: proximity to qualified positive references alone is far weaker than v31's positive-versus-nonpositive nearest-reference contrast. The nonpositive reference geometry therefore carries essential discriminative information in the successful v31 mechanism, even though the separate Tomek experiment showed that some boundary-linked nonpositive references can be harmful. Those two facts jointly motivate studying the **structure of the two-class boundary/contrast**, not abandoning the negative class or rescuing the failed Tomek edit.

Scientific firewall remained intact: target-excluded GMN 2022+2023 development only; protected solar longitude 20°–55°, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS were not accessed.
