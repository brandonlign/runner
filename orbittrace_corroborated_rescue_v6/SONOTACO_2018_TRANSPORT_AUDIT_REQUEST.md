# SonotaCo 2018 transport-only audit request

This stage begins only after the passing v6 development architecture is frozen.

Permitted outputs are archive/member hashes, archive structure, schema/header metadata, and row counts needed to construct a deterministic SonotaCo 2018 parser from the already validated SonotaCo parser source.

This stage must not evaluate shower labels or compute detector scores, empirical p-values, recall, false-positive rates, AUROC, threshold performance, candidate identities, or any other v6 method-performance result on SonotaCo 2018.

The frozen v6 rule remains:

`(p_v3 <= 17/513) OR ((p_fixed4 <= 15/513) AND (p_v3 <= 122/513))`.
