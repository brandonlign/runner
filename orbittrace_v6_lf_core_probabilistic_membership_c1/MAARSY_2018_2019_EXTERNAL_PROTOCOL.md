# C1-LF pristine MAARSY 2018/2019 external validation

## Eligibility and exclusive panel ownership

This protocol is frozen before any C1-LF development result, before any C1-LF matched-literature result, and before any OrbitTrace-project access to MAARSY 2018/2019 event-level scientific values.

It is dormant unless the active method chain reaches C1-LF legitimately:

1. v6-LF passes frozen development;
2. v6-LF returns exact `NO_LITERATURE_SUPERIORITY`, so v6-LF does **not** open MAARSY 2018/2019 under its own external protocol;
3. exact frozen C1-LF passes development;
4. exact frozen C1-LF returns `BROAD_CATALOGUE_SUPERIORITY` or `SPARSE_STREAM_SUPERIORITY` on its separately frozen matched Sugar/HDBSCAN comparison;
5. an execution-time repository-history audit still finds no MAARSY 2018/2019 event-level scientific access.

MAARSY 2018/2019 is an exclusive pristine panel for the first legitimately active method that reaches an external-validation gate. v6-LF, C1-LF and P1 may each have preregistered protocols for the panel, but only the active chain may open it. If any earlier active method has already opened the panel scientifically, this C1-LF protocol must block.

## Why this replaces GMN 2024/2025

GMN 2024/2025 is not a pristine prospective holdout. PR #453 / run `31235104333` already consumed target-excluded 2024/2025 known-shower labels and F1 endpoints. No C1-LF workflow may use that panel to claim independent generalization.

Completed MAARSY science consumed 2016/2017 only and stopped before the first 2018 data header. Repository-history searches before this freeze found no MAARSY 2018/2019 scientific-value execution. The execution-time freshness audit is binding.

## Frozen geometry transport

Use exactly the already-established MAARSY geometry transport:

- target exclusion 20°–55° before scientific geometry use;
- `sun_lon`, `slon`, `slat`, and `norm(vels)` under the previously frozen MAARSY semantics;
- deterministic stable IDs from year/member/row identity;
- deterministic identity-only SHA-256 cap of at most 10,000 retained events per frozen solar-longitude bin;
- the same retained row universe for the v6-LF seed-core construction and all C1-LF membership modeling.

No MAARSY-specific parameter, threshold, covariance rule, shell definition, event filter, rank rule, or density cap may be changed after 2018/2019 values are opened.

## Stage G — seed/core and membership freeze before orbit access

Before any native `kepler` value is read:

1. run the exact frozen v6-LF all-event-null detector on MAARSY 2018/2019 target-excluded geometry;
2. freeze the complete recurrent **primary** v6-LF family universe and exact primary rank;
3. fixed4 rescue families remain diagnostic and may not seed C1-LF;
4. apply the exact development-frozen C1-LF membership engine jointly across 2018/2019 to primary families only;
5. preserve every immutable v6-LF seed and preserve the exact primary family order;
6. freeze every C1-LF candidate identity, local-background-shell identity, OAS model, Garwood background quantity, conflict responsibility, final added-member assignment, expanded membership and diagnostic needed to reproduce the result;
7. select local-background controls from each family's already-frozen 99%–99.99% shell by deterministic identity-only SHA-256 order, before orbit access;
8. SHA-256 freeze the complete seed/core rank, C1-LF expanded memberships and controls.

The C1-LF model remains exactly:

- seed-only OAS covariance;
- 99% candidate ellipsoid;
- 99%–99.99% local-background shell;
- one-sided 95% Garwood background upper bound;
- joint assignment responsibility strictly >0.5;
- immutable seeds;
- no refit or recursive growth;
- no reranking after membership expansion.

No native orbit, `kepler_std`, known-shower label, catalogue identity, OrbitTrace target information, or post-reveal result may enter Stage G.

## Stage O — frozen orbital validation

Only after Stage G is immutable may native `kepler` values be read.

Reuse exactly the existing MAARSY physical semantics:

- `kepler = [a_m, e, i_deg, omega_deg, Omega_deg, nu_deg]`;
- `AU_m = 149597870700.0`;
- `q_AU = abs((a_m/AU_m) * (1-e))`;
- exact Southworth–Hawkins comparator;
- `D_SH < 0.05`;
- no `kepler_std`.

### Seed-family corroboration

A seed v6-LF family is orbitally corroborated iff one single-link `D_SH < 0.05` orbital component contains at least four immutable seed events from 2018 and at least four immutable seed events from 2019, and at least 50% of all valid-orbit seed events in that family lie in the component.

Let `Q_seed` be the number of such orbitally corroborated seed families.

### Added-member physical endpoint

For an event added by C1-LF to family F, define it as dynamically consistent iff it has a valid native orbit and is within `D_SH < 0.05` of at least one **opposite-year immutable v6-LF seed orbit** in F.

This opposite-year rule is fixed before orbit access and prevents same-year local geometry from validating itself.

A local-background control is evaluated by the identical rule against the same opposite-year immutable seed set of its family. Controls come only from the pre-orbit frozen C1-LF background shell and never affect the membership model.

## Power gates

The power requirements are inherited unchanged from the already-preregistered P1 MAARSY 2018/2019 membership-validation protocol rather than chosen for C1-LF:

- at least 200 C1-LF-added events with valid native orbits;
- additions span at least 30 distinct primary families;
- at least 200 valid-orbit shell controls;
- both years contribute valid-orbit additions;
- exact Stage-G source/rank/membership/control hashes verify;
- target exclusion, density cap and fixed4 non-seeding invariants verify.

If any power condition fails after integrity succeeds, return `INCONCLUSIVE_C1_LF_MAARSY_2018_2019_EXTERNAL_POWER` and do not change thresholds, years or control sampling.

## Frozen scientific gates

With adequate power, C1-LF passes only if all of the following hold:

1. `Q_C1 >= Q_seed`, where C1-LF expanded families are evaluated for family-level orbital corroboration under the same frozen D_SH family criterion;
2. dynamically consistent precision among valid-orbit C1-LF additions is >= 0.60;
3. addition consistency precision exceeds frozen shell-control consistency precision by >= +0.15 absolute;
4. one-sided Fisher exact test for addition-vs-control consistency enrichment gives `p <= 0.01`;
5. the total number of dynamically coherent family-member assignments across corroborated families increases by >=20% relative to the immutable v6-LF seed support;
6. every original v6-LF seed remains present and the primary family order is unchanged.

These are the same physical membership-transfer bars already frozen for P1's reserved MAARSY 2018/2019 panel; C1-LF does not receive easier external thresholds.

Return exactly:

- `FAIL_C1_LF_MAARSY_2018_2019_EXTERNAL_INTEGRITY` for a source/firewall/interface failure;
- `INCONCLUSIVE_C1_LF_MAARSY_2018_2019_EXTERNAL_POWER` for adequate integrity but inadequate preregistered power;
- `PASS_C1_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION` if every power and scientific gate passes;
- `FAIL_C1_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION` if power is adequate but one or more scientific gates fail.

A scientific FAIL is a permanent C1-LF external no-go. Inconclusive external power does not authorize final target access and may route only according to the already-frozen successor hierarchy; it may not trigger threshold relaxation or a second look at 2018/2019.

## Final-target boundary

Only exact `PASS_C1_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION`, after exact C1-LF development PASS and matched-literature superiority, can satisfy C1-LF's independent-generalization prerequisite for a final target-containing Stage A.

No OrbitTrace coordinate, member, identity, historical target rank/recovery, target-region GMN event, withheld target reference, Stage-A result or Stage-B reveal value may be accessed here.
