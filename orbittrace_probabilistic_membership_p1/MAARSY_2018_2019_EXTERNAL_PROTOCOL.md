# OrbitTrace probabilistic membership P1 — reserved pristine MAARSY 2018/2019 external validation

## Status and reservation boundary

Protocol-only reservation frozen before any P1 scientific development result exists and before any MAARSY 2018/2019 event-level dataset value is read in the OrbitTrace project.

This protocol does not authorize immediate data access. It may activate only if all of the following have already occurred without P1 retuning:

1. exact frozen P1 development returns `PASS_PROBABILISTIC_MEMBERSHIP_P1_DEVELOPMENT`;
2. the separately frozen P1 matched-literature comparison completes;
3. that comparison returns at least `SPARSE_STREAM_SUPERIORITY` or `BROAD_CATALOGUE_SUPERIORITY` against both frozen Sugar and catalogue-HDBSCAN transports;
4. an execution-only child PR contains exactly the later-frozen activation marker for this protocol.

If P1 fails development or fails literature superiority, MAARSY 2018/2019 remains unopened and is not consumed by P1. No OrbitTrace target-containing search is authorized here.

## Why 2018/2019 is reserved

The public MAARSY archive spans later years, but the only completed OrbitTrace scientific MAARSY analysis used 2016 and 2017. The 2016/2017 geometry run froze its family/ranking output before orbit access, and the post-ranking orbital runner explicitly stopped at the first `data/2018/` archive header. Repository-history searches before this reservation found no MAARSY 2019 scientific run and no evidence of a 2018/2019 event-value analysis.

Therefore 2018 and 2019 are selected now, before P1 outcomes and before their scientific values are opened, as the earliest consecutive event-value-unexposed pair after the already-consumed 2016/2017 panel. Archive/member names and structural metadata are not treated as scientific exposure; event geometry, velocity, orbit, labels, scores, families, or target-region values are.

Any later discovery that 2018 or 2019 event-level scientific values were previously accessed by this project invalidates the pristine claim and blocks execution rather than silently downgrading the claim.

## Immutable method

The detector is exact frozen P1 on the exact promoted-v8 core/ranking architecture.

P1 remains unchanged:

- exact promoted-v8 recurrent cores and multiplicity order;
- seed-only same-year pooled-centroid residuals in the frozen 4D observation representation;
- pooled seed-only OAS covariance;
- frozen 99% candidate ellipsoid;
- frozen 99%–99.99% local-background shell;
- one-sided 95% Garwood upper background bound;
- simultaneous family competition against unit background;
- strict winning family responsibility `>0.5`;
- seeds never move;
- added events never refit, recurse, seed growth, or change the v8 ranking.

No MAARSY value may change any covariance estimator, containment probability, shell, background rule, responsibility rule, family definition, ranking term, or development/literature gate.

## Frozen MAARSY geometry transport

Reuse the already-established MAARSY 2016/2017 geometry semantics without reinterpretation:

- `sun_lon` is solar longitude;
- `slat` is geocentric ecliptic radiant latitude;
- `slon` is radiant-minus-Sun geocentric ecliptic longitude;
- `norm(vels)` is geocentric speed in km/s;
- exact deterministic event IDs retain year, archive member, and zero-based row index.

The target interval solar longitude 20°–55° must be removed **before** retained-row geometry/velocity values are used for core generation, P1 fitting, membership assignment, ranking, or any downstream evaluation.

Because MAARSY is much denser than the GMN development corpus, inherit the exact external-survey density transport already frozen and used for v8 MAARSY: at most 10,000 events per frozen solar-longitude bin selected by deterministic identity-only SHA-256 ordering. This is a transport normalization fixed before 2018/2019 values, not a parameter search. No alternative cap or binning may be tried from the result.

## Stage G — geometry-only discovery and membership freeze

Before any MAARSY `kepler` value is read:

1. verify that only the fixed 2018 and 2019 scientific members are eligible;
2. read solar longitude first and remove 20°–55°;
3. read only the retained rows' frozen geometry/velocity fields;
4. apply the exact inherited 10,000/bin identity cap;
5. construct the exact promoted-v8 cores and exact promoted-v8 multiplicity ranking on 2018+2019;
6. apply exact frozen P1 membership once, without truth/orbit access;
7. freeze and SHA-256 hash the complete v8 seed-family payload, complete ranking, P1 candidate/background-shell pair universe, conflict responsibilities, final added-member assignments, and all deterministic control-pair IDs defined below.

The geometry-only stage may decide only integrity and geometry-power conditions. It may not inspect `kepler`, `kepler_std`, native labels, catalogue shower identities, or any target information.

### Geometry power floor

Require at least `N >= 100` recurrent v8 seed families, inherited from the prior MAARSY external standard. If integrity passes but N<100, return an external-power inconclusive result and do not open orbital values.

## Frozen post-membership orbital semantics

Only after Stage G is immutable may orbital values be read.

Reuse the already-frozen MAARSY native orbit interpretation and external orbital comparator exactly:

- native `kepler` order: `a_m, e, i_deg, omega_deg, Omega_deg, nu_deg`;
- `AU_m = 149597870700.0`;
- `q_AU = abs((a_m/AU_m) * (1-e))`;
- exact Southworth–Hawkins comparator;
- `D_SH < 0.05`;
- minimum four events from each year in a single-link orbital component;
- minimum family orbital-corroboration precision 0.50;
- family-level orbital power floor `Q >= 30`.

`kepler_std` remains forbidden. No orbital value may feed back into P1 fitting, conflict resolution, family membership, or ranking.

## External membership endpoint

This validation is deliberately aimed at P1's claimed improvement—post-core membership assignment—not at inventing a new ranking endpoint.

For each P1-added event assigned to family F in year Y, define its **independent dynamical-consistency indicator** only after all P1 assignments are frozen:

- identify all immutable v8 seed events of F in the opposite year;
- the added event is dynamically consistent iff its orbit has `D_SH < 0.05` to at least one valid opposite-year seed orbit of F.

This nearest-opposite-year-seed rule is fixed before 2018/2019 orbit access. P1 itself never uses orbit distance.

### Deterministic local-shell controls

Before orbit access, construct a control pool from the exact P1 99%–99.99% local-background-shell event/family pairs.

For each family/year with P1 additions:

1. remove seed events and all finally assigned P1 events from that family/year control pool;
2. order the remaining shell pairs by SHA-256 of the canonical event ID plus canonical family ID;
3. retain up to the number of P1-added pairs for that same family/year;
4. freeze all retained control IDs in the Stage-G hash payload.

After orbit access, score each control pair with the exact same nearest-opposite-year-seed `D_SH < 0.05` rule. No control resampling, rematching, orbit-aware selection, or alternate shell is allowed.

## Power gates for P1 membership validation

After valid orbit rows are available, all of the following are required before scientific PASS/FAIL is interpreted:

1. `Q_seed >= 30` orbitally corroborated seed families under the inherited MAARSY family evaluator;
2. at least 200 valid-orbit P1-added event/family pairs within families having valid opposite-year seed orbits;
3. those additions span at least 30 distinct families;
4. at least 200 deterministic local-shell control pairs have valid orbits under the same eligible-family boundary.

If integrity passes but any power gate fails, return `INCONCLUSIVE_P1_MAARSY_2018_2019_EXTERNAL_POWER` and preserve the exact result without changing floors.

## Frozen scientific pass gates

Let:

- `A` = all power-eligible P1-added pairs;
- `C` = deterministic power-eligible shell-control pairs;
- `precision_A` = fraction of A dynamically consistent by the frozen D_SH rule;
- `precision_C` = fraction of C dynamically consistent by the same rule;
- `Q_seed` = orbitally corroborated family count using immutable v8 seed memberships;
- `Q_P1` = orbitally corroborated family count after adding exact frozen P1 memberships and applying the same inherited family corroboration rule;
- `coherent_seed_members` = number of valid seed events belonging to the inherited corroborating orbital components of seed families;
- `coherent_P1_members` = corresponding valid-event count after exact P1 membership expansion.

P1 passes this external validation only if every condition below holds:

1. all geometry, source, target-firewall, pre-orbit-freeze, and orbital-integrity gates pass;
2. `Q_P1 >= Q_seed` — no loss of orbitally corroborated families;
3. `precision_A >= 0.60`;
4. `precision_A >= precision_C + 0.15` absolute;
5. a one-sided Fisher exact test on dynamically-consistent vs inconsistent counts for A against C gives `p <= 0.01` in the favorable direction;
6. `coherent_P1_members >= 1.20 * coherent_seed_members`;
7. P1 membership expansion remains nonrecursive and the exact promoted-v8 multiplicity ranking is byte-identical before and after membership evaluation.

These thresholds are frozen before any P1 development, literature, MAARSY-2018/2019 geometry, or MAARSY-2018/2019 orbit outcome is known. They may not be relaxed after an inconclusive or failed result.

Return exactly:

- `FAIL_P1_MAARSY_2018_2019_EXTERNAL_INTEGRITY` for a non-power integrity/interface failure;
- `INCONCLUSIVE_P1_MAARSY_2018_2019_EXTERNAL_POWER` when integrity passes but a power floor fails;
- `PASS_P1_MAARSY_2018_2019_EXTERNAL_VALIDATION` when all power and scientific gates pass;
- `FAIL_P1_MAARSY_2018_2019_EXTERNAL_VALIDATION` when all power gates pass but one or more scientific gates fail.

A powered failure is a permanent P1 external no-go. An inconclusive result does not authorize threshold changes or a second 2018/2019 analysis.

## Claim boundary

A pass would provide a genuinely prospective **event-value-unexposed, cross-survey, no-retuning physical membership validation** of P1 on MAARSY 2018/2019, subject to the repository-history freshness audit succeeding at execution time. It would not prove universal meteor-stream superiority and would not retroactively make the earlier MAARSY 2016/2017 v8 test conclusive.

A pass still does not itself reveal OrbitTrace. Final target access remains subject to the separately frozen target firewall and blind-deployment authorization.

## Firewall

No OrbitTrace coordinate, identity, member, prior target rank/recovery, target-region GMN event, withheld reference, Stage-A target ranking, or Stage-B reveal artifact may be accessed here. Solar longitude 20°–55° remains excluded from the MAARSY scientific universe before geometry use.
