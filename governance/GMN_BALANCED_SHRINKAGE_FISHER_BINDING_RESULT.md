# Binding result — GMN balanced shrinkage Fisher OOF v1

Run: `31565972049`
Job: `94017720509`
Artifact: `9129508430`
Artifact digest: `sha256:d5338751651c4122dab4f91bc4e2b652b307c0f36d83d1f293fe68f5da8d15df`

Verdict: `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF`

Exact successful-parent controls reproduced before interpretation:
- recovered@100: 66
- recovered@50: 41
- top-100 dominant precision: 0.7229521515453452
- MRR: 0.050244164168646674
- qualified families: 95
- parent OOF margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`

Binding Fisher successor:
- recovered@100: **69**
- recovered@50: **41**
- top-100 dominant precision: **0.7677499561973543**
- MRR: **0.05055989766869564**
- qualified families: **95**
- parent median absolute margin: 0.4460321881586118
- raw Fisher median absolute score: 1.1959148553269499
- unit factor: 0.3729631638672734
- scaled Fisher score SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`

All preregistered gates passed. This is the strongest demonstrated target-excluded GMN ranking mechanism in the current family universe.

The mechanism is frozen exactly as evaluated: strict whole-shower OOF; exact 23D intrinsic representation; separate positive/nonpositive Ledoit-Wolf covariances; equal 0.5/0.5 covariance pooling; equal-prior midpoint; Fisher direction; positive scalar unit preservation; unchanged diversity and equal hard-order rank fusion. No post-result tuning is authorized.

A cross-dataset use requires a separately frozen transfer protocol before any new SonotaCo outcome. Any SonotaCo 2013/2014 use remains EXPOSED DEVELOPMENT ONLY and must never be described as external validation.

Firewall remained intact: blind exclusion `[20.0,55.0]`; SonotaCo 2013/2014 access false in this GMN run; target information access false; target-region events accessed false; MAARSY scientific access false; DMS scientific access false.
