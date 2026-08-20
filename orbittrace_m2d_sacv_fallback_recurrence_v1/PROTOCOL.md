# M2D SACV fallback-only recurrence v1 — frozen protocol

## Motivation

Frozen SACV v1 improves extraction on target-excluded GMN and transfers to SonotaCo, but its blind OrbitTrace application #1406 fell back to the entire parent because the independently selected annual top-1 hypotheses did not validate. Diagnostic #1407 established that admissible recurrent alternatives existed but were discarded before recurrence. #1407 is causal motivation only and cannot count as validation or supply target tuning.

Global replacement of SACV v1 by recurrence-component union (#1408/#1411), pair-only extraction (#1409), edge-consensus (#1412), and reciprocal-nearest sparsification (#1414) are preserved scientific no-gos. Their failures show that replacing already-successful SACV cases damages generic benchmark behavior.

## Sole scientific change

Preserve the exact frozen SACV v1 success path unchanged. For each M2D parent:

1. Enumerate every annual SACV-admissible hypothesis using the exact SACV physical metric, seasonal-analog null, contamination convention, support floor, radius ceiling, excess rule, and deterministic annual ordering.
2. Build the exact already-frozen cross-year reciprocal recurrence graph before discarding any non-top annual hypothesis.
3. If the original SACV annual top-1 pair is a validated recurrence edge, emit **exactly the original SACV v1 membership**: the union of those two annual hypothesis balls. No recurrence-first alternative may replace a successful SACV result.
4. Only if the original SACV top-1 pair would have failed and fallen back to the whole parent, inspect the already-frozen recurrence components. If any component exists, select the component using the unchanged recurrence-first ordering: edge count descending, node count descending, minimum cross-support descending, member count ascending, stable membership hash. Emit that selected component's natural membership union.
5. If neither the original SACV path nor an all-hypothesis recurrent component validates, emit the exact M2D parent unchanged.

No new threshold, radius, support rule, contamination rule, null, physical metric, component score, tie break, pruning rule, edge weighting, target-size cutoff, or sweep is introduced. This is a control-flow change only: recurrence-first extraction is permitted solely on the exact pre-existing SACV fallback path.

## Binding development

First scientific test is the exact target-excluded GMN Sugar2017/HDBSCAN2025 paired same-parent benchmark. Existing SACV v1 precision/F1 non-regression gates remain binding; no gate is relaxed. OrbitTrace target IDs/coordinates/memberships and SonotaCo scientific truth are prohibited.

A GMN FAIL permanently rejects this exact architecture and does not authorize a variant. A GMN PASS may authorize only an unchanged SonotaCo transfer. Only a subsequent unchanged SonotaCo PASS could authorize post-target-reveal OrbitTrace characterization; such a result could never retroactively become pristine independent-rediscovery evidence.
