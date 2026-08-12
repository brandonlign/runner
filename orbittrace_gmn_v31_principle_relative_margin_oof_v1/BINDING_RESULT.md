# Binding result — GMN v31-principle local-scale-relative margin OOF v1

Run: `31564498650`
Job: `94013456705`
Artifact: `9128989753`
Artifact digest: `sha256:24cb205f8703ab3e4a80c5ca48692331848731f2f2d74676b7a8fb95a85df6c0`

Verdict: `FAIL_GMN_V31_PRINCIPLE_RELATIVE_MARGIN_OOF`

Exact parent controls reproduced before interpretation:
- recovered@100: 66
- recovered@50: 41
- top-100 dominant precision: 0.7229521515453452
- MRR: 0.050244164168646674
- qualified families: 95
- raw parent margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`

Binding successor result:
- recovered@100: 64
- recovered@50: 42
- top-100 dominant precision: 0.7117112551868016
- MRR: 0.050270310156544755
- qualified families: 95
- global scale: 1.8350215921911561
- relative margin SHA256: `d8f308a9d084a0d57dba34f8152976afd84c257dd0db8afbc1fce8616d0973c7`

Although top-50 recovery and MRR increased slightly, the preregistered top-100 and precision gates failed. This exact normalization is permanently closed. No alternate denominator, rescaling, clipping, epsilon, weighting, diversity, or fusion rescue is authorized.

Firewall remained intact: blind exclusion `[20.0,55.0]`; SonotaCo 2013/2014 access false; target information access false; target-region events accessed false; MAARSY scientific access false; DMS scientific access false.
