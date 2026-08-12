# OrbitTrace GMN thinning family-stability diagnostic v1 — binding result

## Scientific conclusion

The preregistered diagnostic **does not justify a thinning-stability successor**.

Family persistence under the four frozen deterministic event-thinning panels is not a monotone or sufficiently specific proxy for family quality on the target-excluded GMN 2022/2023 union. In particular, the rare high-quality P20 mode is not isolated by increasing stability: maximal stability is dominated by low-quality P20 families.

This is a diagnostic conclusion, not a detector FAIL/PASS gate; the protocol deliberately selected no stability threshold or fusion rule.

## Frozen provenance

- protocol-only freeze commit: `708ba3176abc12cd6425fc5fe0249537e48fbb80`
- implementation commit: `6357919475d3025cddfd45a648b4d628e6e5a706`
- original workflow commit: `8fac88c9be99c7f6fc96a7e34db64e0daf774b6b`
- execution-only registered-workflow commit: `dc28b902bec506bd36437a04796ba4744e39b244`
- first technically valid binding execution: run `31615201183`, job `94176170359`
- binding artifact: `orbittrace-gmn-thinning-family-stability-diagnostic-v1`
- artifact ID: `9149007071`
- artifact digest: `sha256:6f3802830b32219dd436bb79ff2bdb4b0493f388b8f1d05c2a01c23a41e1ce2f`
- stability-table SHA-256: `eddd025950a0c5595f841d8b8c63e9b4e019db488c1dba88a23e93673eacc4a3`

The four frozen #842 panel artifacts were used unchanged:

- A10 artifact `9046663526`, digest `sha256:7982bc48cfc78ce70cde9bf3d360c6f3c49f1ee78617325f0301d5933377430c`
- B10 artifact `9046670988`, digest `sha256:85acd4d96bb93f84543eec4e2276cbbd0c4c65fe09482bfd89518504b43862bf`
- C20 artifact `9046651217`, digest `sha256:47bddb3f223c2f40710f151e9e48b9460bfa9332cd1c5d7180f00353a2b0cbe6`
- D20 artifact `9046644994`, digest `sha256:b04a4ac3a0cca8d517ce9fef9cec2bb22a6dbb936c73bc499ea3e64cda8b6d2d`

No panel was regenerated or selected after outcome.

## Exact diagnostic result

Universe:

- hard: 226
- P19: 1,075
- P20: 3,203
- eligible recurrent labels: 355
- fixed agreement radius: 1.0

### Hard

| stability | families | positives | mean target F1 | q90 target F1 | target F1 > 0.5 |
|---:|---:|---:|---:|---:|---:|
| 0 | 57 | 19 | 0.0359088 | 0.108808 | 0 |
| 1 | 71 | 27 | 0.0380410 | 0.105263 | 1 |
| 2 | 50 | 24 | 0.0743494 | 0.250210 | 1 |
| 3 | 27 | 23 | 0.2220183 | 0.486031 | 1 |
| 4 | 21 | 18 | 0.1228540 | 0.280899 | 0 |

Hard-family quality rises through stability 3 but falls again at stability 4; high-quality counts are too sparse to define a reliable monotone rule.

### P19

| stability | families | positives | mean target F1 | q90 target F1 | target F1 > 0.5 |
|---:|---:|---:|---:|---:|---:|
| 0 | 143 | 29 | 0.0353286 | 0.105853 | 3 |
| 1 | 330 | 98 | 0.0527934 | 0.158321 | 8 |
| 2 | 345 | 92 | 0.0433395 | 0.160694 | 3 |
| 3 | 195 | 64 | 0.0698346 | 0.272283 | 7 |
| 4 | 62 | 29 | 0.0823870 | 0.323084 | 1 |

P19 has some enrichment at higher stability but it is non-monotonic and high-quality families remain spread across stability levels.

### P20

| stability | families | positives | mean target F1 | q90 target F1 | target F1 > 0.5 |
|---:|---:|---:|---:|---:|---:|
| 0 | 433 | 119 | 0.0148492 | 0.0403202 | 1 |
| 1 | 765 | 180 | 0.0123843 | 0.0356748 | 0 |
| 2 | 669 | 206 | 0.0152103 | 0.0435967 | 0 |
| 3 | 320 | 129 | 0.0160441 | 0.0361174 | 2 |
| 4 | 1,016 | 960 | 0.00555050 | 0.0145502 | 0 |

Only **3** P20 families have target F1 > 0.5. Their frozen stability histogram is:

- stability 0: 1
- stability 1: 0
- stability 2: 0
- stability 3: 2
- stability 4: 0

The decisive negative result is stability 4: it contains **1,016 P20 families**, **960 positives**, but **zero** high-quality families and the lowest mean/q90 target quality. Therefore simple persistence count is not a defensible positive quality feature for the rare P20 mode.

## Interpretation boundary

Do **not** create a successor by selecting stability 3, excluding stability 4, choosing a source-specific cutoff, changing the radius, choosing different thinning fractions/salts, weighting panels, or fitting a post-result transform of stability. Those choices would be selected after seeing this diagnostic and would constitute rescue/tuning.

Any future use of event-thinning information must be a genuinely new, independently motivated mechanism with a separately frozen protocol; it may not be a threshold rescue of this stability count.

## Protected-data firewall

Binding execution preserved:

- blind exclusion `[20.0, 55.0]`;
- `sonotaco_2013_2014_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.

The complete label-free 4,504-family stability table was computed and hashed before GMN shower truth was parsed.
