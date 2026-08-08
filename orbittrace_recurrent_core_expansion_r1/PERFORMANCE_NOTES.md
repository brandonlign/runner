# R1 implementation-only performance track

This track is strictly separate from the frozen R1 scientific rule and from the live frozen development execution. It must not be used to tune any scientific parameter, threshold, ranking, medoid definition, growth rule, or gate.

## Static hotspot finding

Static inspection of the SHA-pinned frozen R1 source (`806e6577b19f5771d58531b036fdb991526999aa6d83795d3e5c864d7c2e8a15`) identifies `expand_memberships` as the dominant post-scoring candidate: it spans frozen-source lines 205–320 and contains 11 loops. The source is not executed during this audit and no catalogue rows, labels, target-region events, or OrbitTrace target information are accessed.

The frozen implementation constructs `medoid_cache` for every component before it begins family expansion. `component_orbit_medoid` builds a complete pairwise D_SH matrix over each component's valid seed-event orbits and takes the median row distance to select the actual-event medoid.

The pinned target-excluded v6 development artifact used by the R1 execution records 2,074 components for 2022 and 1,845 for 2023, or 3,919 total. The 226 recurrent families in the same pinned artifact reference 1,313 unique component IDs. Because R1 can only access components listed in `family["component_ids"]`, medoids for the remaining 2,606 components cannot affect any proposal, conflict, assignment, ranking, diagnostic, or gate. Computing those medoids is implementation dead work.

## Exact-only optimization scope

The proposed optimized expansion performs only the following:

1. Construct medoids only for component IDs actually referenced by recurrent families.
2. Memoize the unchanged `event_center(event)` result by Python event-object identity.
3. Memoize the unchanged frozen `scalar_dsh(event_orbit, medoid_orbit)` result by event ID and medoid event ID.
4. Remove the frozen function's unused `scan_lookup` construction.
5. Add progress/timing output.

No geometric prefilter, numerical approximation, alternative D_SH implementation, threshold adjustment, medoid change, recursive growth, ranking change, or gate change is permitted.

The frozen `literature_comparators.py` D_SH comparator remains byte-identical and is still called for every cache miss.

## Equivalence firewall

Before any optimized full R1 execution is authorized, a target-excluded bounded diagnostic must compare the complete return value of the frozen reference `expand_memberships` against the optimized implementation on the same deterministic family subset and require exact Python equality.

The bounded proof also includes one real target-excluded component not referenced by the sampled families when available. This directly tests that eliminating an unreferenced medoid leaves the complete returned expansion structure and diagnostics unchanged.

The diagnostic is hard-wired to exit immediately after the equality proof and therefore cannot produce a competing full R1 scientific verdict.

## Progress indicators

Future optimized execution emits:

- `R1_EXPANSION_START` with family, total-component, active-component, and seed counts.
- `R1_MEDOID_PROGRESS` every 25 active medoids with elapsed seconds.
- `R1_EXPANSION_PROGRESS` every 10 recurrent families with component attempts, geometry passes, physical passes, event-center cache hits, D_SH cache entries/hits, and elapsed seconds.
- `R1_EXPANSION_COMPLETE` with final assignment/cache/timing counts.

An external `r1_process_heartbeat.sh` helper is also retained for diagnostic runs where process CPU/RSS/thread activity is useful; it does not alter the scientific process.
