# GMN v31 class-conditional nearest-distance calibration v1 — binding result

Status: **FAIL — permanently closed**.

The first workflow attempt (`31662273582`) failed before candidate execution because `globalmeteornetwork.org` transiently refused a historical monthly-file connection. That run produced no candidate score/order/result and is engineering-only.

The first technically valid candidate outcome is GitHub Actions run `31662570915`, job `94330275590`, commit `4a0a0cfd5db6d64f724af3b20d287435a6444fba`, artifact `9166811151`, digest `sha256:a0ce4a0f5ac5b1dfc40c970e7dd632878f019237f343ec670ab4d720bb08a2b2`.

Before candidate science, the retry workflow reproduced the exact GMN v31 parent and required its frozen provenance:

- prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- 23D feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- raw v31 OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

Frozen class-conditional successor after exact parent diversity and equal hard-order fusion:

- recovered@25 = **21**;
- recovered@50 = **39**;
- recovered@100 = **63**;
- recovered@500 = 95;
- top-100 dominant precision = **0.6740578853111707**;
- MRR = **0.04852448219397636**;
- qualified matches = 95.

Its class-calibrated local-only order was also worse:

- recovered@25 = 17;
- recovered@50 = 30;
- recovered@100 = 55;
- top-100 dominant precision = 0.5609300885346831;
- MRR = 0.044227349113514544;
- qualified matches = 95.

Binding gate results:

- recovered@100 strictly better than parent: **FAIL** (63 < 66);
- recovered@50 nonregression: **FAIL** (39 < 41);
- recovered@25 nonregression: **FAIL** (21 < 23);
- top-100 precision nonregression: **FAIL** (0.6740578853111707 < 0.7229521515453452);
- MRR nonregression: **FAIL** (0.04852448219397636 < 0.050244164168646674);
- qualified count identical: **PASS** (95).

Therefore `GMN_V31_CLASS_CONDITIONAL_DISTANCE_V1` is not promotable and does not authorize SonotaCo access.

Per the preregistered protocol, this exact class-conditional calibration lane is permanently closed. No alternative p-value transform, log/ratio/odds contrast, pseudocount, threshold, calibration pooling, leave-one-family calibration, class-prior correction, weighted contrast, k, metric, feature, scaling, diversity, fusion, or result-informed rescue is authorized.

Interpretation is limited to the tested mechanism: separately calibrating positive/nonpositive nearest distances against training-only same-class leave-group-out geometry materially worsened the v31 ranking on target-excluded GMN. This does not support changing v31's raw nearest-class margin into a class-relative conformity contrast.

Scientific firewall remained intact: GMN 2022+2023 target-excluded development only; protected solar longitude 20°–55°, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS were not accessed for this successor.
