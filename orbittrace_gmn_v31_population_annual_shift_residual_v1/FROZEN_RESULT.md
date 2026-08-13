# Binding result — FAIL

Frozen protocol commit: `770f2045138392a1175825489d4361ad8a56b709`.

Exact offline parent reproduced before candidate scoring:
- feature SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- centroid SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`
- parent margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- parent metrics `23/41/66`, precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified `95`.

Frozen leave-one-family-out population annual-shift residual SHA-256: `77a8be327c656ef90e5beb234e4392292431b6b28b1d89daf024a500c4861eec`.

Candidate:
- recovered@25 = `23`
- recovered@50 = `43`
- recovered@100 = `65`
- top-100 dominant precision = `0.7133013418287458`
- MRR = `0.050242496699099616`
- qualified matches = `95`

Verdict: `FAIL_GMN_V31_POPULATION_ANNUAL_SHIFT_RESIDUAL_V1`.

@50 improved by 2, but @100, precision, and MRR failed their frozen gates. This exact mechanism is closed. Do not rescue with another population center, embedding/scale, norm, weighting, or centering rule. No SonotaCo benchmark is authorized. Protected 20-55, OrbitTrace target information/events, MAARSY, DMS, and SonotaCo were not accessed.