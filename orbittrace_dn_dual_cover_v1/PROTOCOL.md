# OrbitTrace Valsecchi D_N dual-cover HDBSCAN v1 — frozen protocol

## Goal

Test one structural change aimed directly at the project goal: **meaningfully improve meteor-stream recovery with a geometry that is physically designed for meteor similarity and is plausible across observing networks**.

This is not a family reranker. It replaces the GEO6 Euclidean neighbourhood geometry that constructs the HDBSCAN hierarchy.

Valsecchi, Jopek & Froeschlé (1999) introduced `D_N` from directly observed/geocentric meteor quantities. Later optical and radar studies found `D_N` among the strongest D-criteria for separating shower members from the sporadic background, with weights `w1=w2=w3=1`. This protocol uses that published metric without fitted weights or thresholds.

## Locked development data and parent

- Development population: exact target-excluded GMN 2022+2023 population already used by the current methods.
- Inclusive protected solar-longitude exclusion: `[20.0,55.0]` before any fit or truth access.
- Comparator: exact density-synchronous recurrent-EOM GMN winner from binding run `31852836840`, artifact `9238142199`, with total recovered@100 `179` (`89` in 2022, `90` in 2023).
- The parent comparator is rehydrated from its exact binding artifact; it is not recomputed as another scientific chance.

## Exact D_N coordinates from the already-locked GMN fields

The current locked event representation provides:

- solar longitude `sol`;
- Sun-centred ecliptic radiant longitude `L = lambda_radiant - lambda_sun`;
- ecliptic radiant latitude `beta`;
- geocentric speed `v_g`.

With the D_N Earth-centred frame `x` opposite the Sun, `y` in the Earth's direction of motion, and `z` to ecliptic north, the **geocentric velocity direction is opposite the radiant**, giving

- `u = v_g / 29.7 km/s`;
- `Ux/u = cos(beta) cos(L)`;
- `Uy/u = cos(beta) sin(L)`;
- `Uz/u = -sin(beta)`;
- `cos(theta) = Uy/u`;
- `phi = atan2(Ux, Uz)`.

The published D_N encounter longitude is the Earth's heliocentric longitude. The stored solar longitude differs by a common `pi` shift; all D_N pairwise `Delta lambda` chord terms are unchanged by applying the same `pi` shift to every event. Therefore this implementation uses the stored `sol` directly as the angular coordinate.

All angles are converted to radians. No data-dependent normalization is introduced.

## Published D_N metric

With `w1=w2=w3=1`:

`D_N^2 = (u2-u1)^2 + (cos(theta2)-cos(theta1))^2 + Delta_xi^2`

where

`Delta_xi^2 = min(Delta_phi_a^2 + Delta_lambda_a^2, Delta_phi_b^2 + Delta_lambda_b^2)`

and

- `Delta_phi_a = 2 sin((phi2-phi1)/2)`;
- `Delta_phi_b = 2 sin((pi + phi2-phi1)/2)`;
- `Delta_lambda_a = 2 sin((lambda2-lambda1)/2)`;
- `Delta_lambda_b = 2 sin((pi + lambda2-lambda1)/2)`.

## Exact Euclidean dual cover

Define

`z(phi,lambda) = [cos(phi), sin(phi), cos(lambda), sin(lambda)]`.

Each physical meteor `i` is lifted to two 6-D representatives:

- `X_i(+) = [u_i, cos(theta_i), +z_i]`;
- `X_i(-) = [u_i, cos(theta_i), -z_i]`.

Then for every pair of physical meteors `i,j`:

`D_N(i,j)^2 = min(||X_i(+)-X_j(+)||^2, ||X_i(+)-X_j(-)||^2)`.

The same equality holds starting from either sheet of `i`. This is an algebraic identity, not an approximation. It turns the published projective angular minimum in D_N into ordinary Euclidean distances on a two-sheet cover and avoids an `N x N` precomputed distance matrix.

The exact equality and sheet symmetry must pass the zero-data synthetic audit before GMN geometry is allowed.

## Candidate construction

1. Build the two-sheet cover for all accessible GMN events, with all `+` representatives first and all `-` representatives second.
2. Duplicate each event's year label onto both sheets.
3. Fit one pooled HDBSCAN hierarchy on the cover with:
   - Euclidean metric;
   - `min_cluster_size=10`;
   - `min_samples=10`;
   - `cluster_selection_method='eom'`;
   - `cluster_selection_epsilon=0`;
   - `allow_single_cluster=False`;
   - `prediction_data=False`.
4. Apply the exact density-synchronous recurrent-EOM objective from the current GMN winner to the cover hierarchy. Because each year's accessible population is exactly doubled, the annual normalization changes by a global factor only; no new weight is fitted.
5. Convert each selected cover cluster into a physical candidate by replacing representative indices with original event IDs.
6. A selected cover cluster containing **both sheets of the same physical meteor is not a valid physical candidate and is discarded deterministically**. This prevents one observation from counting twice in a candidate.
7. Require at least 10 unique physical meteors after folding.
8. If multiple selected cover clusters fold to the exact same physical membership set (the expected mirror symmetry case), retain one physical family only, choosing deterministically by:
   - larger density-synchronous cover stability;
   - then larger ordinary cover stability;
   - then smaller selected node ID.
9. Rank physical families by:
   - descending density-synchronous cover stability;
   - descending ordinary cover stability;
   - descending unique physical member count;
   - stable membership hash.

No post-hoc score, cutoff, D_N threshold, learned weight, sheet preference, or rank blend is used.

## Pre-truth engineering gate

Before hidden known-shower labels may be opened, the complete physical candidate catalogue must be persisted and must satisfy:

- exact protected-data firewall;
- cover row count exactly `2 * 738682 = 1477364`;
- each sheet contains exactly the same 738682 physical event IDs once;
- exact published D_N / dual-cover identity was already proven in the frozen synthetic audit;
- mechanism active relative to the parent physical membership/order;
- at least one valid physical candidate;
- all emitted candidates have unique physical event IDs and at least 10 members;
- duplicate physical membership sets are absent after deterministic mirror folding.

A memory/runtime failure, a failure before candidate prelabel persistence, or an invalid cover construction is a **technical no-result**, not a scientific FAIL. Repair may only change implementation plumbing while preserving the exact frozen metric, HDBSCAN parameters, folding rules, and scientific gate.

## Frozen GMN scientific success gate

Parent total recovered@100 = `179`.

PASS requires **all**:

1. valid D_N candidate-construction mechanism is active;
2. successor total recovered@100 across 2022+2023 is at least `184` (**+5 or more**);
3. recovered@100 is not lower than the parent in either year;
4. recovered@50 is not lower in either year;
5. top-100 dominant precision is not lower in either year;
6. MRR is not lower in either year;
7. median top-500 fragmentation is not higher in either year.

`180–183` total is still a FAIL. The goal is meaningful improvement, not a one-shower win.

No rescue by changing D_N weights, speed normalization, HDBSCAN settings, cover folding, ranking, thresholds, or applying the method only to favorable regions is authorized after the result.

## If and only if GMN passes

Before any SonotaCo execution, freeze a direct transfer protocol that reconstructs the same published D_N coordinates and exact dual-cover candidate construction separately on each established SonotaCo 2013/2014 panel.

Transfer PASS must require:

- no regression versus the current recurrent-EOM benchmark on all four established panels in macro-F1 or recovered count;
- strict improvement on at least two of four panels;
- continued superiority over the corresponding frozen literature comparator on all four panels.

No SonotaCo tuning/rerun is allowed.

Only a method passing GMN and the pre-frozen SonotaCo transfer may be considered for the single untouched AMOS final test under a separately frozen pre-data protocol.

## Permanent protected-data and failure rules

During GMN development:

- SonotaCo 2013/2014 is inaccessible for this successor;
- ASFN/EFN are not used for design, tuning, rescue, or selection;
- AMOS remains pristine and inaccessible;
- OrbitTrace target information/events remain inaccessible;
- MAARSY and DMS remain inaccessible.

A technically valid GMN FAIL permanently closes exact Valsecchi D_N dual-cover HDBSCAN v1. Do not rescue it with approximate kNN graphs, alternate D-criteria, weights, thresholds, score blends, or local subsets.
