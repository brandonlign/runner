# Binding result — GMN diagonal shrinkage Fisher OOF v1

Run: `31568293302`
Job: `94024627334`
Artifact: `9130305524`
Artifact digest: `sha256:f09405e4069549061d87323244563715052614e334872241f532bd3e58db8dd4`

Verdict: `FAIL_GMN_DIAGONAL_SHRINKAGE_FISHER_OOF`

Exact Fisher parent controls reproduced before candidate interpretation:
- recovered@100: 69
- recovered@50: 41
- top-100 dominant precision: 0.7677499561973543
- MRR: 0.05055989766869565
- qualified families: 95
- scaled Fisher score SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`
- parent k=1 margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`

Binding diagonal candidate:
- recovered@100: 66
- recovered@50: 42
- top-100 dominant precision: 0.7540211954462825
- MRR: 0.04770457443012051
- qualified families: 95
- raw median absolute score: 3.151168841240089
- unit factor: 0.1415449982626394
- raw score SHA256: `fe9863c359921cd577fd28c5a11b87e14ce8899f8e0767b84fc9f51f83d77287`
- scaled score SHA256: `376992e5c3e1d1a23e72428198226fda1813df1ad78ce66568f2ab5393eb605c`

The preregistered strict top-100, precision, and MRR gates failed. This exact diagonalized Ledoit-Wolf Fisher architecture is permanently closed. No raw diagonal variance estimator, full/diagonal interpolation, covariance weighting, parent/diagonal blend, feature change, calibration, diversity/fusion change, threshold, or post-result rescue is authorized.

Scientific interpretation: the full off-diagonal covariance structure contributes useful information to the 69-family Fisher parent. The full-vs-diagonal covariance simplification lane is closed.

Firewall remained intact: blind exclusion `[20.0,55.0]`; SonotaCo 2013/2014 access false; target information access false; target-region events accessed false; MAARSY scientific access false; DMS scientific access false.
