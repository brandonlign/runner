# OrbitTrace v3-primary catalogue v6 — checkpointed development fallback

## Status

Infrastructure-only fallback for the exact frozen target-excluded catalogue-v6 development computation. This protocol is frozen while the original repaired execution in PR #491 / workflow run `31270206927` is still running.

It may be executed only if that run ends without a scientific PASS/FAIL verdict because of timeout, runner failure, cancellation, or another technical failure. A scientific `PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT` or `FAIL_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT` from the original repaired run is authoritative and makes this fallback unnecessary.

No OrbitTrace target-containing scan is authorized. Solar longitude 20°–55° remains excluded exactly as in the frozen support parser.

## Scientific identity

The scientific source is the exact v6 source SHA-256:

`a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`

The only source repair is the already-audited PR #490 two-line fix:

- `primary_components = component_records_track_v6(old, year, primary_capped, event_lookup, base, "v3")`
- `rescue_components = component_records_track_v6(old, year, rescue_capped, event_lookup, base, "fixed4_rescue")`

No score, proposal rule, calibration rule, alpha, episode size, proposal cap, member assignment, component rule, recurrence rule, family rule, ranking rule, evaluation rule, gate, or threshold changes.

## Checkpoint decomposition

The frozen `main()` computes 2022 and 2023 by calling `scan_year_v6(...)` once per year, accumulating only the three returned objects `(audit, anchors, components)`, and performing recurrent-family construction/evaluation only after both year calls return.

The fallback therefore:

1. runs the exact repaired `scan_year_v6(...)` for 2022 in one job;
2. runs the exact repaired `scan_year_v6(...)` for 2023 in a second independent job;
3. stores each returned triple in a pickle checkpoint together with hashes of the exact ordered scan and calibration event rows;
4. starts the exact repaired original `main()` in a combine job;
5. allows `main()` to parse the catalogue, labels, sources, baseline, and all modules normally;
6. temporarily replaces only `scan_year_v6` with a replay function that recomputes the ordered input-row hashes and refuses the checkpoint unless they are byte-canonical identical to the inputs seen by `main()`;
7. returns the saved `(audit, anchors, components)` for that year;
8. leaves the original repaired `main()` to perform family construction, hidden-label evaluation, gates, output files, and the final scientific verdict unchanged.

Thus the fallback does not reimplement the post-scan science.

## Checkpoint firewall

Year checkpoints contain no hidden-label dictionary and no scientific development verdict. They contain only:

- year;
- frozen/repaired source identity;
- exact ordered scan/calibration row hashes;
- source-provenance hash for that year;
- the exact `scan_year_v6` returned audit/anchors/components;
- explicit stage/firewall flags.

Checkpoint SHA-256 sidecars are required at replay. Replay fails if source identity, year, checkpoint bytes, scan rows, or calibration rows differ.

## Efficiency/observability

The two expensive year scans may run in parallel because the frozen main has no cross-year scientific operation until after both returned triples are accumulated. Each job emits an external CPU/RAM/elapsed-time heartbeat once per minute. Completed year checkpoints are independent artifacts, so a later infrastructure retry can reuse a completed year rather than recompute it.

This changes wall-clock scheduling and failure recovery only; it does not skip or approximate any scientific calculation.
