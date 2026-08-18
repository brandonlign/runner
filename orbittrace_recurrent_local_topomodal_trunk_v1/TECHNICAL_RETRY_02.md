# Recurrent local TopoModal trunk v1 — exact Technical Retry 02

## Scientific status

The exact frozen method remains unresolved. Neither prior binding attempt produced a prelabel, truth metric, gate result, or scientific verdict.

- run `32090725251`: label-free geometry/source audits passed; frozen prelabel build was externally cancelled during rank 1 after the hosted runner received a shutdown signal.
- run `32091272769`: same classification; exact frozen prelabel build reached rank 1 (`n=32458`) and the hosted runner again received a shutdown signal. No prelabel artifact existed and truth never opened.

The later lazy-neighbor transport is not used in this retry. Its separate equivalence audit failed and therefore does not authorize lazy execution.

## Sole retry action

Technical Retry 02 executes the original frozen scientific implementation byte-for-byte:

- protocol blob `de8d040a1f9d3b0825ce56532efd5950acefc689`;
- geometry exporter blob `32abfb3e68520cfdc83585a88731fa3982900cde`;
- prelabel builder blob `cd3fb15263fd4b2e38e4b413ece9b347b64816d5`;
- truth evaluator blob `749a527b7a9ee3c5f1a70832669d83fa1af592d7`;
- exact density-synchronous parent artifacts/run unchanged.

No monkeypatch, batched graph, lazy graph, sharding, candidate change, rank change, truth change, or gate change is used.

The only orchestration change is to separate the label-free prelabel stage and truth stage into different jobs. The prelabel is uploaded and hash-sealed before the truth job can start. The truth job downloads that immutable artifact and runs the unchanged frozen evaluator.

## Governance

This retry cannot rewrite either previous technical no-result into a scientific outcome. The first complete truth JSON produced by the unchanged evaluator is binding. If the exact prelabel job is again externally cancelled, the run remains an engineering no-result and truth stays unopened.

Protected `[20°,55°]`, OrbitTrace target information/events/orbits, SonotaCo, ASFN/EFN event-level data, AMOS, MAARSY and DMS remain inaccessible. No post-result parameter search is authorized.
