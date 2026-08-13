# GMN v31 margin-confidence fusion v1 — binding result

Binding run: `31661580584` on commit `8f15e4cf5a6b82099744da99b21104e49ec57e8f`.
Artifact: `9166453893`, digest `sha256:799a0123ad5bafa9d9d9cec5820abd0fa6e117606b999846f0274002f306cfde`.

Verdict: `FAIL_GMN_V31_MARGIN_CONFIDENCE_FUSION_V1`.

Exact parent reproduced before candidate evaluation:

- recovered@25: 23
- recovered@50: 41
- recovered@100: 66
- top-100 dominant precision: 0.7229521515453452
- MRR: 0.050244164168646674
- qualified matches: 95

Frozen parameter-free margin-confidence successor:

- recovered@25: 23
- recovered@50: 41
- recovered@100: 61
- recovered@500: 95
- top-100 dominant precision: 0.7207046740486416
- MRR: 0.04925086792650762
- qualified matches: 95

The exact raw strict-OOF margin vector was reproduced and captured with SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`, identical to the frozen parent margin hash. The candidate therefore differs only in the preregistered confidence-weighted final fusion.

Binding gates:

- recovered@100 strictly better than parent: **FAIL** (61 < 66)
- recovered@50 nonregression: **PASS** (41 = 41)
- recovered@25 nonregression: **PASS** (23 = 23)
- top-100 precision nonregression: **FAIL** (0.7207046740486416 < 0.7229521515453452)
- MRR nonregression: **FAIL** (0.04925086792650762 < 0.050244164168646674)
- qualified count identical: **PASS** (95)

Therefore the method is not promotable and does not authorize SonotaCo access.

This exact lane is permanently closed as preregistered. No alternate confidence transform, absolute- or signed-margin cutoff, quantile binning, calibration fit, exponent/temperature, coefficient, interpolation endpoint, constituent weight, feature/metric/scaling/diversity change, or post-result rescue is authorized.

Scientific firewall remained intact: GMN 2022+2023 target-excluded development only; protected solar longitude 20°–55°, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS were not accessed for this successor.
