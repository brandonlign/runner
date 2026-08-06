# OrbitTrace fixed4 v2 wrapper source audit

## Purpose

Inspect the two already executed catalogue wrappers around the immutable fixed-4° coverage-normalized Mondrian anchored four-clique core before designing any revised method.

This stage is source-only. It must not download or parse a meteor catalogue, inspect shower labels, retrieve an OrbitTrace artifact, evaluate a candidate, rerank a family, or modify either frozen result.

## Sources

The audit begins from the existing calibrated blind-scan branch, which contains both inherited wrapper implementations:

- broad ranked-quartet recurrence wrapper: `orbittrace_blind_catalogue/run_blind_scan.py.gz.b64`;
- calibrated component-family wrapper: `orbittrace_fixed4_blind_catalogue/source_parts/part00.b64` through `part03.b64`.

The calibrated source must reproduce SHA-256 `48434df612f790924e6efce45b6b8d4de1401880f398994bc58eef2fce0987e5`.

## Audit outputs

The workflow must preserve:

1. decoded source for both wrappers;
2. SHA-256 and byte counts;
3. complete AST inventories of imports, constants, functions, classes, and call sites;
4. normalized source for key detector and wrapper functions;
5. a structural comparison separating immutable detector-core behavior from catalogue-wrapper behavior;
6. an explicit list of revision points that can be developed without changing the fixed 4° distance or using OrbitTrace information.

## Development boundary

The frozen fixed4 detector remains the baseline. A v2 method may revise the catalogue-scale evidence aggregation layer only after this source audit.

V2 development must use known non-OrbitTrace showers and controls with the solar-longitude interval 20°–55° removed before labels, tuning, wrapper selection, thresholds, ranking, or stopping decisions. OrbitTrace may be tested only once after the v2 source, parameters, and non-target benchmark result are frozen.

No previous negative or partial blind result may be erased or relabelled.