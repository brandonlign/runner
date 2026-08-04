# Mondrian partition-invariant clique: authoritative retrospective result

Runner workflow `30874109169` executed the full frozen four-panel matrix from source SHA-256 `e3dc3dfcbfbfdc15bead220464213ee271f7411cbf550bbecf0536153b85344e`.

GhostStream remained excluded by removing solar longitude 20.0°–55.0° before every stratum, pool, window, score, fold, and endpoint.

## Preserved evidence

- 2021 artifact `8878913797`, digest `sha256:efd84e6e42c9f608076252ad70f65f393e186c861dc53f592e2f2004db505fae`;
- 2024 artifact `8878912322`, digest `sha256:f045083ba3a720ee64ba5f56b20564df8b5e872521b7b9cd7876406072de8d4c`;
- 2025 artifact `8878915816`, digest `sha256:f69c28918689943ea2a29119b67cb61e68cee405e999525c5424f9bdd6a5bb6d`;
- 2026 H1 feasibility artifact `8878893781`, digest `sha256:87d5c2438d3c28215efefbaaf4af2e727c65705e307fd7f18f832ce7e23c4909`.

## Complete-panel results

The 2021, 2024, and 2025 panels each supported 33 globally anchored 10° solar-longitude strata and passed every frozen calibration, discrimination, fold, and recall gate.

### 2021

- eligible showers: **174**;
- negative / weak-positive windows: **2,112 / 2,088**;
- clique weak AUROC: **0.79548**;
- split / density / DBSCAN AUROC: **0.79290 / 0.77037 / 0.75088**;
- pooled FPR at alpha 0.05 / 0.01: **0.03741 / 0.00947**;
- worst 60° reporting-sector FPR at alpha 0.05: **0.07813**;
- k=4 recall at alpha 0.05 / 0.01: **0.15661 / 0.05747**;
- five clique fold AUROCs: **0.83348, 0.77267, 0.77266, 0.78295, 0.81684**.

### 2024

- eligible showers: **135**;
- negative / weak-positive windows: **2,112 / 1,620**;
- clique weak AUROC: **0.80697**;
- split / density / DBSCAN AUROC: **0.80602 / 0.78223 / 0.76377**;
- pooled FPR at alpha 0.05 / 0.01: **0.03835 / 0.00521**;
- worst 60° reporting-sector FPR at alpha 0.05: **0.05729**;
- k=4 recall at alpha 0.05 / 0.01: **0.20370 / 0.06852**;
- five clique fold AUROCs: **0.81151, 0.78691, 0.79402, 0.82813, 0.81557**.

### 2025

- eligible showers: **181**;
- negative / weak-positive windows: **2,112 / 2,172**;
- clique weak AUROC: **0.79197**;
- split / density / DBSCAN AUROC: **0.78681 / 0.76766 / 0.75386**;
- pooled FPR at alpha 0.05 / 0.01: **0.04924 / 0.00473**;
- worst 60° reporting-sector FPR at alpha 0.05: **0.07552**;
- k=4 recall at alpha 0.05 / 0.01: **0.17680 / 0.07182**;
- five clique fold AUROCs: **0.82376, 0.79276, 0.80472, 0.77367, 0.76493**.

These three panels independently support the scientific diagnosis that fixed 10° phase conditioning can calibrate the partition-invariant clique score while retaining weak-shower power.

## Frozen 2026 H1 feasibility failure

The fourth predeclared panel did not reach scoring. After exact source and input verification, the frozen implementation found only **15** supported 10° strata in January–June 2026 outside the blind interval. The protocol required at least **20** supported strata in every panel.

The source terminated with:

`RuntimeError: Only 15 supported 10-degree bins`

This is a legitimate failure of the exact four-panel formulation, not a software or provenance failure. The partial-year H1 corpus does not cover enough solar phase to satisfy the prospectively frozen panel-feasibility requirement.

## Frozen outcome

Verdict: **`KILL_MONDRIAN_CLIQUE_FOUR_PANEL_FORMULATION`**.

Do not lower the 20-stratum gate, count unsupported blind-interval strata, alter the width or boundaries, replace H1 with a different spent panel, or reinterpret the three passing panels as a four-panel pass. The unused July 2026 snapshot is not authorized for confirmation under this protocol.

The positive three-panel result may motivate a separately frozen formulation whose coverage requirement is defined prospectively for a complete-year confirmation corpus, but no result from this PR may validate that replacement or authorize a GhostStream application.
