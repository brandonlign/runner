# OrbitTrace final MAARSY 2020/2021 normalizer — pre-value freeze v1

## Scope

This is a **schema/value-access contract only** for the permanent MAARSY 2020/2021 external panel. It is frozen while the final corrected M2 development run is unresolved and before any selected MAARSY 2020/2021 scientific event value is opened.

It adds no detector, ranker, membership threshold, validation threshold, or outcome-dependent rule. It supports either final GMN membership outcome:

- **M0:** geometry-only hard+P19+P20 catalogue and its frozen ranker; no orbit is needed for primary membership.
- **M2:** the same geometry-only family universe/rank, followed by the already-frozen P12-derived event-level membership layer if and only if M2 is ultimately promoted by the #846→#850→#852 chain.

## Frozen public schema mapping

Use only the already-established MAARSY RCS release interface:

- `sun_lon`: geocentric mean ecliptic solar longitude, degrees;
- `slon`: geocentric ecliptic radiant longitude minus Sun longitude, degrees;
- `slat`: geocentric ecliptic radiant latitude, degrees;
- `vels`: row-aligned geocentric velocity vector; Euclidean norm is km/s;
- `kepler`: row-aligned six columns `[a_m, e, i_deg, omega_deg, Omega_deg, true_anomaly_deg]`.

Internal geometry mapping:

- `sol <- sun_lon`;
- `sun_lon <- wrap180(slon)`;
- `ecl_lat <- slat`;
- `vg <- ||vels||`.

Internal orbit mapping if separately authorized for a frozen row ID:

- `a_AU = a_m / 149597870700.0`;
- `q_AU = abs(a_AU * (1-e))`;
- `e <- e`;
- `i <- i_deg`;
- `peri <- omega_deg mod 360`;
- `node <- Omega_deg mod 360`;
- true anomaly is unused by D_SH.

Stable event identity is `MAARSY|YEAR|ARCHIVE_MEMBER|ROW_INDEX_0BASED`.

No learned coordinate transform, proxy radiant, alternate speed statistic, unit inference, imputation, or outcome-dependent mapping is permitted.

## Schema-only prerequisite

Before reading any selected 2020/2021 scientific value, every structurally selected member must be shown without reading dataset/attribute values to have:

1. numeric one-dimensional row-aligned `sun_lon`, `slon`, and `slat`;
2. numeric row-aligned `vels` with a shape compatible with one velocity vector per row;
3. numeric row-aligned `kepler` with shape `(n,6)`;
4. one common row count `n`;
5. calendar identity determined from archive/member structure, not event values.

Any violation is an architecture-compatibility failure. No replacement year, proxy field, or method change is allowed.

## Stage A — geometry-only access, generator, and ranking

For each selected member:

1. read only `sun_lon`;
2. validate its frozen degree representation;
3. remove every row with `20.0 <= sun_lon <= 55.0`;
4. only for retained rows, read `slon`, `slat`, and `vels`;
5. normalize the exact four geometry fields above;
6. **do not read `kepler`**.

Across exact 2020/2021 geometry rows, execute the selected method's frozen pair-portable hard+P19+P20 generator and frozen #839/#853 ranker. Freeze and hash:

- complete row manifest;
- all family IDs and geometry memberships;
- all 4,504-architecture-equivalent source types actually produced on the external pair;
- all ranker feature rows/predictions;
- complete catalogue order.

No orbit value may affect candidate existence, source type, family geometry membership, score, diversity suppression, or rank.

## Stage B0 — M0 membership

If final GMN selection is M0, the Stage-A family member sets are the primary external member sets. `kepler` remains unread for primary external validation unless a separately frozen post-scientific corroboration analysis is later authorized; it cannot affect the external verdict.

## Stage B2 — M2 pre-orbit proposal freeze

This stage exists only if final GMN adjudication selects M2. It is dormant forever if M0 is selected.

M2 may require D_SH for non-core P12-style additions. To prevent orbit information from entering discovery/ranking or choosing which arbitrary rows receive orbit access, proceed in this exact order after Stage A is frozen:

1. reconstruct the frozen P12/M2 **observation-space side** for each eligible hard-family direction using only Stage-A geometry fields and the exact M2 deployable source;
2. evaluate every retained Stage-A event through all M2 pre-orbit conditions that can be evaluated without `kepler` (source/target-year direction, drift-conditioned observation representation, exact observation ceiling and any other orbit-independent frozen eligibility rule);
3. form the **superset** of event IDs for which the exact M2 implementation would next need orbital quantities to determine membership;
4. freeze, sort, and SHA-256 hash that proposal-ID superset before reading any `kepler` value;
5. no event ID may be added to the proposal superset after the first `kepler` read.

If the exact M2 implementation cannot expose such an orbit-blind pre-orbit proposal boundary without changing its scientific rule, M2 is externally architecture-incompatible and fails closed. It may not read all MAARSY orbits as a convenience workaround.

## Stage C2 — restricted orbit access and exact M2 membership

Only after the Stage-B2 proposal-ID manifest is frozen may the runner:

1. read `kepler` rows **only for those frozen proposal IDs**;
2. derive exact `[q,e,i,peri,node]` as above;
3. compute the exact frozen D_SH/orbit features and remaining M2 feature vector;
4. apply the exact full-GMN fitted M2 classifier, probability threshold, additions/core cap, and hard-core-never-removed rule;
5. freeze the resulting one primary member set per hard family.

P19-soft and P20-soft memberships remain exactly their Stage-A geometry memberships. Candidate existence and the Stage-A catalogue order remain immutable.

The external scientific evaluator may then evaluate exactly those final primary member sets. It may not switch between M0/M2 representations after external truth/performance is visible.

## Firewall and claim boundary

This contract itself reads no MAARSY value and authorizes no MAARSY value access. Scientific access still requires:

1. final GMN method mechanically selected and frozen;
2. selected method packaged as one deployable executable;
3. permanent SonotaCo 2013/2014 literature superiority PASS;
4. candidate-specific MAARSY performance/power gates frozen before MAARSY values are opened.

No SonotaCo 2013/2014 value, MAARSY 2020/2021 value, target-region event, OrbitTrace coordinate/member/identity, or prior OrbitTrace recovery result is accessed by this protocol.
