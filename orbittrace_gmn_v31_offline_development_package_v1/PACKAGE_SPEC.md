# OrbitTrace GMN v31 offline development package v1

## Role

Engineering/provenance artifact only. This package does **not** define, evaluate, select, or modify a scientific successor. Its sole purpose is to make future already-frozen v31-family GMN 2022+2023 development runs deterministic and independent of repeated downloads from the GMN public host.

The exporter executes the exact passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` source and requires its authoritative hashes/metrics. It captures only data already created inside that exact target-excluded development execution.

## Authoritative parent requirements

Require exact parent source git blob `b4e2d72e532e47aa95ed335f690748423d11ea59` and exact parent result:

- candidate count 226;
- feature dimension 23;
- prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- recovered@25/50/100 = 23/41/66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified labels = 95.

## Allowed exported contents

Only:

1. exact parent 226x23 intrinsic feature matrix `X`;
2. exact parent 226x8 centroid matrix used by the frozen diversity routine;
3. immutable family IDs and hard-order IDs;
4. exact deterministic strict whole-shower development group string and fold ID for each family;
5. exact per-family development truth **summary** returned by the frozen `family_truth` function (`positive`, `best_label`, overlap, precision, recall, F1, dominant precision);
6. eligible development shower-label names;
7. exact parent baseline and fused metric summaries;
8. hashes/provenance/firewall metadata.

## Forbidden exported contents

- raw GMN monthly event rows;
- raw event IDs;
- raw hidden-label mapping keyed by event ID;
- any event in protected solar longitude 20°–55°;
- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific data;
- MAARSY or DMS scientific data;
- any new feature, score, model, rank, threshold, or successor outcome.

The package is development truth, not blind validation material. It may be used only for the already-fixed GMN 2022+2023 target-excluded development role.

## Firewall

Every package manifest must assert:

- `blind_exclusion = [20.0, 55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `raw_event_rows_exported = false`;
- `raw_event_ids_exported = false`;
- `raw_hidden_label_mapping_exported = false`.
