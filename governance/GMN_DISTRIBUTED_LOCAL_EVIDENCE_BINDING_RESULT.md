# Binding result — GMN distributed local-evidence OOF v1

Run: `31565610623`
Job: `94016679479`
Artifact: `9129379413`
Artifact digest: `sha256:9020397ff62bc0ba6e45be31ae8e245a40108a6c843d04f64700b0cdf40491be`

Verdict: `FAIL_GMN_DISTRIBUTED_LOCAL_EVIDENCE_OOF`

Exact parent controls reproduced before interpretation:
- recovered@100: 66
- recovered@50: 41
- top-100 dominant precision: 0.7229521515453452
- MRR: 0.050244164168646674
- qualified families: 95
- parent margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`

Binding distributed-evidence result:
- recovered@100: 65
- recovered@50: 42
- top-100 dominant precision: 0.7462934770862113
- MRR: 0.05056520426642316
- qualified families: 95
- parent median absolute margin: 0.4460321881586118
- evidence median absolute score: 0.5364027947970167
- unit factor: 0.8315247282173417
- scaled evidence SHA256: `bc672035fcdb6ce6221900eacc09b6e770f446535d266fa031a90a54f77e85ca`
- label-free fold bandwidths: `[1.634735874782552, 1.5170548922742626, 1.6023478234049935, 1.6188783754039153, 1.5496568322653461]`

The method improved top-50 recovery, top-100 dominant precision, and MRR, but the binding top-100 strict-improvement gate failed because 65 < 66. Therefore the exact Gaussian distributed-evidence mechanism is permanently closed. No kernel, bandwidth, bandwidth multiplier, prior, neighbor truncation, class weighting, score scaling, diversity, fusion, or post-result rescue is authorized.

Firewall remained intact: blind exclusion `[20.0,55.0]`; SonotaCo 2013/2014 access false; target information access false; target-region events accessed false; MAARSY scientific access false; DMS scientific access false.
