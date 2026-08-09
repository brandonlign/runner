# P16 core-rank / halo-membership catalogue freeze

## Status

Frozen before any P15/P16 matched pretruth checkpoint, comparator cluster value, known-shower truth value, matched F1/superiority result, external result, or OrbitTrace target access.

P16 is an output-architecture successor, not a new detector. It reuses the already-frozen P14/P15 primary recurrent-core family universe and support-safe multiplicity order unchanged, while promoting the already-frozen label-free P15/P12 halo from characterization-only to the catalogue membership reported for those same families.

## Scientific rationale fixed before matched truth

Target-excluded development already established two complementary facts independently:

- P13/P14 primary recurrent cores preserve the strong discovery/ranking endpoint: 95 qualified known-shower matches, 58 recovered in the top 100, 95 in the top 500, MRR `0.045531138942766655`, top-100 dominant precision `0.6884631112636006`, core pretruth SHA `12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c`.
- exact P12 label-free halo membership substantially improves membership quality on the same 226-family development universe: macro F1 `0.37661279333940806`, top-100 dominant precision `0.6904890277588119`, large-shower recall `0.24179462579908398`, large-shower precision `0.8778478363509471`, halo membership SHA `f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3`.

The canonical P12/P13 development artifacts establish 226/226 one-to-one family IDs; each core event set is a subset of the corresponding halo event set; and the frozen halo-added event IDs are exactly `halo IDs − core IDs`. P16 therefore does not infer a new family correspondence or propose a new member.

## Exact P16 architecture

For each already-frozen comparator-specific P15 pretruth checkpoint:

1. keep the complete primary family universe exactly unchanged;
2. keep `v8_multiplicity_order` / P14 support-safe multiplicity order exactly unchanged;
3. keep every core event set frozen and serialized for discovery provenance;
4. require exactly one stored halo family with the same stable `family_id` for every core family and no extra halo family;
5. require `core_event_ids ⊆ halo_event_ids` for every family;
6. require the stored P12/P15 added-event IDs to equal exactly `halo_event_ids − core_event_ids`;
7. expose that exact halo event set as the evaluator-facing/reportable family membership, with compatibility `p3_added_event_ids` defined deterministically as the exact set difference so the unchanged evaluator can reconstruct the original core for its internal nonregression diagnostic;
8. recompute only hashes/metadata describing the evaluator-facing membership object; do not recompute any detector score, member proposal, family construction, rank, or scientific distance;
9. freeze the transformed checkpoint before any comparator cluster value or known-shower truth is opened.

P15 support-poor directions remain governed by the already-frozen P15 rule: a `<128`-negative secondary direction contributes zero proposals. P16 cannot fill, pad, resample, borrow, or otherwise rescue unavailable halo evidence. Whatever P15 halo membership exists pretruth is used exactly.

## Discovery vs membership semantics

P16 deliberately separates two catalogue questions:

- **Does a recurrent family exist, and where is it ranked?** Answered only by the immutable P14/P15 recurrent core and support-safe multiplicity order.
- **Which meteors does that already-discovered family report as members?** Answered by the immutable label-free P15/P12 halo.

Halo membership cannot create a family, delete a family, merge families, alter family qualification, alter the primary rank, or seed any additional growth. It can affect membership F1 and membership false-positive burden because those are precisely the outputs P16 changes.

## Matched benchmark

P16 inherits the exact frozen SonotaCo 2023/2025 HDBSCAN and Sugar row universes, truth denominator, parsers, assignment files, pairwise matching, F1 calculation, false-positive burden calculation, and sparse-superiority gates. No benchmark threshold or comparator selection changes.

The unchanged sparse promotion standard remains separately required against both catalogue HDBSCAN and Sugar in both years:

- 4–9-member mean F1 >= comparator +0.10;
- combined 4–24-member mean F1 >= comparator +0.10;
- overall macro F1 no more than 0.10 below comparator;
- retain >=80% of comparator count of showers with F1>0.5;
- all common-universe/integrity/firewall gates pass.

P16 is evaluated as a distinct frozen pretruth challenger. Its result cannot be used to alter P15, P16 membership, rank, thresholds, or external protocol.

## Development compatibility requirement

Before P16 can be promoted, a development adjudicator must verify from immutable canonical artifacts that:

- the P16 family universe/order/core identity is exactly the P13 promoted core identity;
- the P16 reported membership is exactly the canonical P12/P13 halo identity `f158ebfa...`;
- no family correspondence is missing or duplicated;
- every core is a subset of its halo and every halo addition is exactly the already-frozen added-ID set;
- P16 introduces no scientific event or member not already present in the canonical P12 halo artifact;
- the target-excluded P13 core endpoints and P12 halo membership metrics above are reproduced exactly;
- no matched comparator, external, or target information is used.

## External and target boundary

P16 does not inherit external or target authorization merely by passing the matched benchmark. Any external use must be separately frozen before its result and must preserve the same core-rank/halo-membership separation. OrbitTrace target access remains forbidden until a frozen method has passed the required matched literature comparison and a defensible no-retuning external validation. Final target recovery must still use the separately frozen exact-ID blind firewall and primary family rank; halo membership cannot independently satisfy blind recovery.
