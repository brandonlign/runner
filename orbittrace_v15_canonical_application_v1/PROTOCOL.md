# OrbitTrace v15 canonical application — source-only freeze v1

## Purpose

Freeze one scientific application path after the canonical event interface. The same code must rank a two-year canonical event pair regardless of which survey adapter produced the rows.

This is a deployment/refactor freeze, not a new detector. It changes no proposal geometry, family construction, multiplicity definition, local window, multiscale fractions, rank rule, threshold, evaluation rule, or data role.

No scientific catalogue is read by this source freeze and there is no execution marker.

## Input boundary

The application accepts exactly:

1. an ordered pair of two distinct explicit calendar years;
2. one canonical event list for each year, using `orbittrace_v15_canonical_events_v1`;
3. the already-frozen pair-portable hard-v8 recurrent-family builder;
4. the already-frozen local-window / wavelet geometry runtime and base helper;
5. the already-frozen multiplicity episode scorer.

The application contains no survey-name branch. Dataset-specific parsing, units, coordinate conversion, quality cuts, and target firewall happen before this boundary in the frozen adapters.

## Final v15 deployment ranking

The deployed v15 method is the passing **nominal-128 multiscale consensus**. Its component caps are fixed as:

`(128, 96, 64)`

The nominal 96/64/32 panels from development were robustness stress panels, not post-result selectable deployment variants.

For each recurrent family, year, and component cap `C`:

1. use the exact frozen 10-degree local window around that year's family centroid;
2. set `k = min(C, N_local)`;
3. fail closed if `k < 4`;
4. use the exact frozen wavelet distance and stable-smallest-index rule to take the nearest `k` rows;
5. compute the exact frozen v5/v13 multiplicity `(multi-anchor-v3 / Brown)^2` with the Brown-equivalence guard.

For each component cap, order families exactly by:

1. descending worst-year multiplicity;
2. descending geometric-mean multiplicity;
3. stable family ID.

After all three component orders exist, assign zero-based ranks `(r128, r96, r64)` and order families by:

1. `median(r128, r96, r64)` ascending;
2. `r128` ascending;
3. `r96` ascending;
4. `r64` ascending;
5. stable family ID.

This is the exact v15 nominal-128 consensus semantics; no coefficient or scale is selected from the application data.

## Family generation

The application does not create an alternate family generator. It receives the existing pair-portable hard-v8 builder through a narrow callback and requires that every returned recurrent family contains exactly both requested years.

The intended deployment binding is the already-frozen pair-portable hard-v8 construction previously proven operationally equivalent on the GMN development implementation. A later binding audit must identify that source exactly; this package may not substitute a new scanner.

## Pre-truth boundary

The application accepts no truth mapping. All canonical rows, recurrent families, three component multiplicity orders, and the final v15 consensus order must be frozen and hashed before any scored-year known-shower truth is made available to an evaluator.

No label can alter family existence, membership, local support, component score, component rank, or consensus rank.

## Required implementation-equivalence proof

Before the canonical application is used on an external panel, a separate engineering-only run must reproduce the already-passed v15 nominal-128 ranking on its frozen development corpus using:

- the canonical projection;
- the exact pair-portable hard-v8 builder;
- this common application source;
- the exact frozen v15/v5 scoring runtime.

The family universe and final v15 nominal-128 order must match exactly. This is implementation equivalence only, not new scientific evidence.

## Firewall

This package must contain:

- no survey-specific scientific branch;
- no raw catalogue/network/HDF5/archive loader;
- no known-shower or truth loader;
- no DMS route or replacement-dataset rule;
- no target identity/coordinate/member surface;
- no `RUN.md` or external execution marker.

Passing its synthetic/source audit authorizes only the next implementation-equivalence step. It does not itself authorize SonotaCo, MAARSY scientific access, or OrbitTrace target access.
