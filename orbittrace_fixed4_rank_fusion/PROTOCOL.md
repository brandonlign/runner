# Fixed4 persistence-anchored rank-fusion development

## Motivation

The target-excluded support-normalized wrapper experiment showed that mean year strength contains useful within-catalogue ordering information but is too aggressive as a full replacement for persistence. It improved mean reciprocal rank in both temporal panels while losing three top-100 recoveries on untouched 2024–2025 validation.

This stage develops a conservative rank fusion that preserves persistence as the dominant signal and permits only a small mean-strength adjustment.

## Frozen evidence

Development is artifact-only and uses the exact completed support-wrapper artifact:

- artifact `8971289223`;
- ZIP SHA-256 `01a7158ee5cf79e212689b3eb24438bbf98f959dc3588141f073412b1a9c5999`;
- source scanner SHA-256 `fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`;
- target-excluded panels 2022–2023 and 2024–2025.

No meteor catalogue is reopened, no family is rebuilt, and no OrbitTrace information is available.

## Candidate family

For each panel with `N` families, let `r_p` be the one-based persistence rank and `r_s` the one-based mean-year-strength rank. Candidate weight `w` receives the ascending fusion score

`F_w = (1 - w) * r_p / N + w * r_s / N`.

Ties use persistence rank, then mean-strength rank, then stable family identifier.

The complete frozen candidate grid is:

`w in {0.000, 0.010, 0.015, 0.020, 0.025}`.

No other score, rank transform, nonlinear fusion, panel-specific weight, or family-specific rule may be evaluated.

## Development evaluation

The two already exposed panels are treated jointly as development evidence. For every candidate and panel, the existing qualified known-shower match family is preserved; only its rank changes. Report top-100 recall, top-500 recall, and mean reciprocal rank.

Candidates are selected lexicographically by:

1. largest minimum top-100 recall delta versus persistence across the two panels;
2. largest total top-100 recall across the two panels;
3. largest minimum MRR delta versus persistence;
4. largest mean MRR delta;
5. smaller weight.

Development passes only if:

- the selected weight is nonzero;
- top-100 recall does not decline in either panel;
- at least one panel gains at least one top-100 recovery;
- top-500 recall does not decline in either panel;
- MRR strictly improves in both panels.

## Prospective boundary

A pass freezes one weight and authorizes a separately frozen full catalogue validation on complete GMN years 2019–2021. Solar longitude 20°–55° must be removed before labels. The prospective panel may not influence the weight.

The prospective validation must compare only persistence and the frozen fusion. It must preserve the exact fixed4 detector core, quartet calibration, component construction, family linkage, and target exclusion from the prior wrapper experiment.

A prospective pass may authorize one target-free OrbitTrace catalogue application. Development alone does not authorize OrbitTrace access or alter any earlier blind result.