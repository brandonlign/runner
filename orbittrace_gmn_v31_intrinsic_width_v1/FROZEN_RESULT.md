# Frozen result — GMN v31 intrinsic-width successor v1

**Status: NEGATIVE / permanently closed.**

The first technically valid target-excluded GMN 2022/2023 outcome is binding.

## Provenance

- Corrected protocol frozen before implementation/outcome: `dea15f0902dc9ebd80750cf3f25807729d12c49e`
- Protocol blob: `bce47ebcafab14effef8dbb4dc39d250df31fac5`
- Implementation commit: `acb2b8ceb7e6e903f42b7d313abf792e2b44ae46`
- Implementation blob: `011d54d800013ee8c7c5cb68fac8f099a1f5ed01`
- Binding workflow head: `1f24c03fafb2efcc5280e7442fd5cd0489f7615d`
- Binding workflow run: `31813351186`
- Binding job: `94809012028`
- Artifact: `9224069103`
- Artifact digest: `sha256:697e6eda62d38cf032873cb49b41c04d070357ceb235625531f39179e50d95c8`
- Authorizing uncertainty-audit run: `31812584375`
- Fixed-member uncertainty artifact: `9223741916`
- Fixed-member uncertainty gzip SHA-256: `01de5502aab911fa251656cd7a71ab4b6ef6158abf3a675495c4ba4d1c349622`
- Exact uncertainty-covered fixed members: 8,794/8,794.

The initial protocol-only commit `9513524308b2360a58aaff5d46f3c3975908d7e4` was superseded before any implementation or candidate outcome by the documented tangent-plane geometry correction in `dea15f0...`. No candidate feature, OOF margin, ranking, or truth endpoint existed before that correction.

## Binding verdict

`FAIL_GMN_V31_INTRINSIC_WIDTH_V1`

Exact v31 parent reproduced:

- recovery@25: **23**
- recovery@50: **41**
- recovery@100: **66**
- top-100 dominant precision: **0.7229521515453452**
- MRR: **0.050244164168646674**
- qualified matches: **95**

Frozen intrinsic-width successor:

- recovery@25: **23** — preserved
- recovery@50: **41** — preserved
- recovery@100: **65** — **FAIL**, below parent and not strictly improved
- top-100 dominant precision: **0.7124850747624788** — **FAIL**, below parent
- MRR: **0.05021055537406366** — **FAIL**, below parent
- qualified matches: **95** — preserved

All 226 families had finite widths and exact uncertainty coverage remained complete.

The preregistered quality-only uncertainty ablation was not a promotion candidate and was worse:

- recovery@25: **23**
- recovery@50: **40**
- recovery@100: **65**
- top-100 dominant precision: **0.7151650418542107**
- MRR: **0.04996174019786922**
- qualified matches: **95**

## Scientific interpretation

The intrinsic-width coordinate is not noise: annual drift-adjusted, measurement-noise-deconvolved widths are directionally smaller among the frozen positive families.

- positive median intrinsic width: **0.20292660906798568**
- nonpositive median intrinsic width: **0.2950781004799579**

The formal measurement-noise width alone shows only a weaker difference:

- positive median quality width: **0.20364396931633164**
- nonpositive median quality width: **0.2274442000204845**

Thus the physical deconvolution reveals a genuine population-level distinction, but inserting that scalar into exact v31's strict-OOF local geometry moves the fixed-budget ranking in the wrong direction. This is a scientific failure, not an applicability or transport failure.

## Permanent closure

Do **not** rescue this result with:

- uncertainty multipliers or reported-error rescaling;
- radiant-only or speed-only intrinsic widths;
- mean/min/geometric-mean annual width combinations;
- alternate drift orders, robust regressions, or no-drift variants;
- alternate variance estimators, eigenvalues, determinants, quantiles, MADs, or clipping rules;
- direct width rewards, width thresholds, feature weighting, transforms, or reranking;
- metric, k, standardization, reference-pool, diversity, or fusion changes;
- selecting or blending the quality-only ablation;
- post-result family-specific exceptions.

No SonotaCo benchmark is authorized by this failure.

Protected solar longitude 20°–55°, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS remained inaccessible during this development run.
