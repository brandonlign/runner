# OrbitTrace v6-LF — pristine MAARSY 2018/2019 external validation

## Status and activation

This protocol is frozen before any v6-LF development verdict, before any v6-LF matched-literature result, and before any OrbitTrace-project access to MAARSY 2018/2019 event-level scientific values.

It is dormant unless, without retuning:

1. exact frozen v6-LF target-excluded GMN 2022/2023 development returns `PASS_V6_LABEL_FREE_ALL_EVENT_NULL_DEVELOPMENT`;
2. the exact frozen pairwise SonotaCo Sugar/HDBSCAN adjudication returns `BROAD_CATALOGUE_SUPERIORITY` or `SPARSE_STREAM_SUPERIORITY` against both comparator panels;
3. an execution-time full-repository freshness audit still finds no prior MAARSY 2018/2019 event-value scientific access.

If development or literature superiority fails, MAARSY 2018/2019 remains unopened for the next legitimately active successor. Marker text alone cannot authorize access.

## Why 2018/2019 is the external panel

Completed OrbitTrace MAARSY science consumed 2016/2017 only. The geometry and orbital runners explicitly stopped at the first `data/2018/` header, and repository-history searches before this freeze found no 2018/2019 event-value scientific execution. The already-completed 2016/2017 panel is therefore historical design evidence; 2018/2019 is the earliest consecutive event-value-unexposed pair available for a new prospective cross-survey validation.

This replaces the invalidated GMN 2024/2025 prospective-holdout idea. Repository history shows GMN 2024/2025 had already been used scientifically in PR #453 / run `31235104333`, including known-shower labels and F1 endpoints. That panel may not authorize final target access.

If later history audit discovers any prior MAARSY 2018 or 2019 event geometry, velocity, orbit, label, score, family, or scientific endpoint access, this protocol must block rather than downgrade the claim.

## Immutable v6-LF method

The external detector is exactly the development-promoted v6-LF method:

- exact repaired v3-primary catalogue-v6 scientific source;
- all-event target-excluded calibration: every geometrically valid retained scan row enters the Mondrian null reservoir;
- no catalogue shower/background designation selects calibration;
- exact proposal cap 512/window and annual primary proposal budget 36,864/year;
- exact v3 primary and fixed4 rescue scoring, exact rescoring, component construction and two-year recurrence;
- the v3 primary family order is the only external ranking eligible for the scientific gate;
- fixed4 rescue remains diagnostic and cannot satisfy primary ranking retention;
- no parameter search, null trimming, density-aware retuning, membership expansion, or MAARSY-specific score threshold.

## Frozen MAARSY transport

Reuse the already-established MAARSY geometry semantics without reinterpretation:

- `sun_lon` = solar longitude;
- `slat` = geocentric ecliptic radiant latitude;
- `slon` = radiant-minus-Sun geocentric ecliptic longitude;
- `norm(vels)` = geocentric speed in km/s;
- deterministic event IDs encode year, archive member and zero-based row index.

Remove solar longitude 20°–55° before retained-row geometry/velocity values enter calibration, proposals, components, recurrence, ranking, or the promoted-v8 baseline.

Inherit the exact external-survey density transport already frozen for MAARSY: at most 10,000 events per frozen solar-longitude bin selected by deterministic identity-only SHA-256 order. The same retained event-row universe is supplied to v6-LF and the promoted-v8 comparator. No alternative cap, binning, or subsample may be tried after seeing 2018/2019 values.

## Stage G — geometry-only dual-method freeze

Before any MAARSY `kepler` value is read:

1. verify only fixed 2018 and 2019 scientific members are eligible;
2. apply the 20°–55° exclusion before geometry use;
3. apply the exact inherited identity-only 10,000/bin cap;
4. run exact v6-LF with all-event calibration and freeze its complete primary family universe/order;
5. independently run exact promoted-v8 pooled-year-centroid multiplicity on the identical retained row universe and freeze its complete family universe/multiplicity order;
6. serialize and SHA-256 freeze all input identities, event IDs, method/source identities, family memberships, rankings and geometry-stage audits.

No orbit, `kepler_std`, native shower label, known-shower truth, catalogue identity, OrbitTrace target information, or result-dependent model choice may enter Stage G.

### Geometry power floor

Require before orbit access:

- at least 50 recurrent v6-LF primary families;
- at least 50 promoted-v8 recurrent families;
- every evaluated family spans both 2018 and 2019 under its exact frozen recurrence semantics;
- exact all-event v6-LF calibration and all frozen proposal-budget/integrity checks pass.

The 50-family floor is inherited from the v6-LF development viability gate and also makes the frozen top-50 external endpoint nonvacuous. If integrity passes but either family universe is smaller, return `INCONCLUSIVE_V6_LF_MAARSY_2018_2019_EXTERNAL_GEOMETRY_POWER` without opening orbital values.

## Stage O — frozen orbital semantics

Only after both complete family universes and rankings are immutable may orbital values be read.

Reuse the already-frozen MAARSY native interpretation and physical comparator exactly:

- native `kepler`: `a_m, e, i_deg, omega_deg, Omega_deg, nu_deg`;
- `AU_m = 149597870700.0`;
- `q_AU = abs((a_m/AU_m) * (1-e))`;
- exact Southworth–Hawkins comparator;
- `D_SH < 0.05`;
- minimum four events from each year in one single-link orbital component;
- minimum family orbital-corroboration precision 0.50.

`kepler_std` remains forbidden. Only orbit rows belonging to already-frozen family event IDs may be read. No orbit value may feed back into event filtering, family membership, recurrence, ranking or detector calibration.

## Prospective power rule

The earlier MAARSY 2016/2017 v8 validation was power-inconclusive because its preregistered `Q >= 30` family floor was incompatible with the realized survey yield: N=107 but only Q=11 families satisfied the strict frozen D_SH family criterion. That completed result is used here only to design a feasible **future-panel** power floor; no 2018/2019 value has been seen.

For 2018/2019, require after orbit access:

- `Q_v6lf >= 10` physically corroborated v6-LF primary families;
- `Q_v8 >= 10` physically corroborated promoted-v8 families;
- at least 90% of all frozen family-event rows in each method have valid native orbit rows.

Ten corroborated families is fixed prospectively as a nontrivial multi-family physical-validation sample while remaining compatible with the observed MAARSY 2016/2017 yield. It is not a retroactive reinterpretation of the 2016/2017 test.

If integrity passes but any power condition fails, return `INCONCLUSIVE_V6_LF_MAARSY_2018_2019_EXTERNAL_POWER` and do not change the floor or rerun a different subset.

## Frozen scientific generalization gates

This stage tests cross-survey **retention of physical discovery quality**, not a second literature-superiority claim. Superiority must already have been established on the matched Sugar/HDBSCAN panels.

For each frozen method define:

- `Q` = number of orbitally corroborated families in its complete recurrent universe;
- `T25` = corroborated-family count in the first 25 ranks;
- `T50` = corroborated-family count in the first 50 ranks;
- `MRR_Q` = mean reciprocal rank over all orbitally corroborated families in that method's frozen order;
- `median_precision_Q` = median family orbital-corroboration precision over corroborated families.

v6-LF passes external generalization only if all of the following hold:

1. `Q_v6lf >= ceil(0.80 * Q_v8)`;
2. `T25_v6lf >= max(2, ceil(0.80 * T25_v8))`;
3. `T50_v6lf >= max(4, ceil(0.80 * T50_v8))`;
4. `MRR_Q_v6lf >= 0.80 * MRR_Q_v8`;
5. `median_precision_Q_v6lf >= 0.60`;
6. the complete v6-LF primary family order and complete promoted-v8 multiplicity order remain byte-identical to their Stage-G pre-orbit freezes.

The 80% retention factor is deliberately reused from the project's already-frozen sparse-superiority retention convention rather than selected from MAARSY 2018/2019. The absolute T25/T50 minima prevent a weak promoted-v8 realization from making the ranking test vacuous. The 0.60 median physical-precision floor is stricter than the 0.50 family inclusion criterion while remaining below the historical 2016/2017 promoted-v8 median corroboration precision (~0.724); it is fixed before 2018/2019 access.

Return exactly:

- `FAIL_V6_LF_MAARSY_2018_2019_EXTERNAL_INTEGRITY` for a non-power interface/source/firewall failure;
- `INCONCLUSIVE_V6_LF_MAARSY_2018_2019_EXTERNAL_GEOMETRY_POWER` for pre-orbit family-universe insufficiency;
- `INCONCLUSIVE_V6_LF_MAARSY_2018_2019_EXTERNAL_POWER` for post-orbit physical power insufficiency;
- `PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION` if every integrity, power and scientific generalization gate passes;
- `FAIL_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION` if power is adequate but one or more scientific gates fail.

A scientific FAIL is a permanent v6-LF external no-go. An inconclusive result does not authorize threshold changes, alternate MAARSY years, or a second look at 2018/2019 under different rules.

## Final-target authorization boundary

Only exact `PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION`, following v6-LF development PASS and matched literature superiority, can satisfy v6-LF's independent-generalization prerequisite for the final full-region GMN Stage A.

The external pass does not itself access the withheld target region and does not reveal OrbitTrace. Final Stage A and exact-ID Stage B remain separately frozen and must verify all prerequisite artifacts before any target-containing GMN row or withheld target-reference value is accessed.

## Firewall

No OrbitTrace coordinate, identity, canonical member, historical target rank/recovery, target-region GMN event, withheld reference, Stage-A target ranking, or Stage-B reveal artifact may be accessed. Solar longitude 20°–55° remains excluded before any MAARSY scientific geometry is used.
