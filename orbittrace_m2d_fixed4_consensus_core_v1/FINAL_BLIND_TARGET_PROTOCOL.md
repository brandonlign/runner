# M2D x fixed4 consensus core v1 — final blind OrbitTrace application

## Activation hierarchy

This protocol is dormant unless both exact upstream verdicts exist without retuning:

1. `PASS_M2D_FIXED4_CONSENSUS_CORE_V1_GMN_DEVELOPMENT` from PR #1398;
2. the exact no-retuning SonotaCo transfer preregistered in `SONOTACO_TRANSFER_PROTOCOL.md` also passes its frozen paired-utility gates.

A failure at either stage permanently disables this target application. This file is frozen while the GMN development result is still unresolved, before any consensus-core target membership exists.

## Immutable blind parent

The primary target discovery object is the already-frozen **baseline** support-resolved TopoModal + exact M2D blind replay from PR #1378, not any later support-pruned variant.

Its complete primary ranking was frozen before exact OrbitTrace IDs were revealed:

- candidate count: `8,469`;
- frozen pretruth gzip SHA-256: `6d72b0f9558b89228953dd73b3760c61df039b713f233473079ae4fac563a100`;
- frozen pretruth inner SHA-256: `7ff3b13bc45e19b4b886453b4d8cc3b4f18090bf8a2291e39850540fd69b5e53`.

The historical exact-ID reveal later established that the parent candidate at rank 84 contained all 18 canonical 2022+2023 OrbitTrace IDs, but that revealed information cannot enter consensus-core construction, candidate selection, reranking or expansion.

## Stage A — consensus core freeze with target reference absent

Using only the exact frozen blind parent candidate memberships plus the same event geometry that generated them, apply the exact PR #1398 consensus rule to **every** parent candidate in the complete ranking:

- split membership by year;
- each event anchors once;
- exact frozen fixed4 distance to every other same-parent/same-year event;
- three nearest others with stable event-ID tie order;
- canonical four-ID quartet;
- retain quartets selected by at least two distinct anchors;
- consensus core = union of all retained quartet events;
- no calibration threshold, score cutoff, distance threshold, best-component selection, expansion, family merge, fallback or reranking.

The complete 8,469 parent-to-core mapping must be serialized and SHA-256 frozen before the canonical OrbitTrace ID file or any reveal artifact is available in the workspace. Stage A must explicitly record `target_reference_access=false` and `target_information_used=false`.

The primary M2D parent rank is immutable. The consensus core is characterization membership only and cannot change whether a parent exists or where it ranks.

## Stage B — exact-ID-only reveal

Only after the Stage-A core artifact is sealed may the canonical 2022 and 2023 OrbitTrace event-ID sets be loaded.

Reveal is restricted to exact set intersection. Coordinates, radiants, speeds, activity intervals, orbital elements, nearest-neighbor matching, family merging, membership expansion and reranking are forbidden.

For every frozen parent/core pair, report:

- parent rank;
- parent member count;
- core member count;
- exact target overlap by year and total;
- exact core precision = target overlap / core size;
- exact target recall = overlap / 18.

## Frozen success classification

The rank and exact-ID support thresholds are inherited from the pre-existing method-agnostic final reveal firewall rather than chosen from the known rank-84 outcome:

- parent rank must be <=100;
- core must contain >=4 exact canonical IDs from 2022;
- core must contain >=4 exact canonical IDs from 2023;
- core must contain >=8 exact canonical IDs total.

To call the result a **clean consensus rediscovery**, two additional characterization requirements are frozen now:

- core precision >=0.50;
- core size <=32 members.

The 32-member compactness ceiling is four times the inherited minimum eight-ID two-year support requirement and is fixed before any consensus-core target membership exists. It is not a search parameter and cannot affect parent ranking or core construction.

Classification:

- `CLEAN_M2D_FIXED4_CONSENSUS_ORBITTRACE_REDISCOVERY`: all rank, exact-ID, precision and size requirements pass;
- `PARTIAL_M2D_FIXED4_CONSENSUS_ORBITTRACE_RECOVERY`: rank<=100 and the >=4/year, >=8-total exact-ID conditions pass, but precision or size cleanliness fails;
- `NO_M2D_FIXED4_CONSENSUS_ORBITTRACE_RECOVERY`: exact-ID support/rank conditions fail.

A clean result may be described as an independently frozen M2D discovery envelope with a fixed4-corroborated high-purity core. It may not be described as the historical first discovery, pristine external validation, or proof of formal IAU shower status.

## No-rescue rule

The first technically valid Stage-B classification is final. No one-anchor rescue, fixed4 threshold, alternate nearest-neighbor count, best quartet/component selection, target-aware trimming, parent switch, family merge, precision cutoff change, size-ceiling change or second reveal is authorized.