# Final fixed-4° methodology evidence synthesis

Status: frozen after the standalone SonotaCo 2025 development result, the calibration-seed robustness result, and the sole authorized SonotaCo 2023 replacement independent replication. This workflow performs no detector run and opens no meteor record.

## Exact evidence

The synthesis may consume only these three already-frozen runner artifacts:

1. **Standalone SonotaCo 2025 final development**
   - workflow `30918739353`;
   - artifact `8896176320`;
   - artifact digest `sha256:b3dd9c80759b749420407e95de0a5ed581e208bbd39c806d9472c00ae9a3529e`;
   - result JSON SHA-256 `b985efacf1cb7edc070e17b2a304b6a08059dff94b32a2c83731b2ec8700e8cc`.

2. **SonotaCo 2025 calibration-seed robustness**
   - workflow `30919265521`;
   - artifact `8896413550`;
   - artifact digest `sha256:f8149e09dd1e1334e61635dc46269b29811dc0a7a4ad071057f0d2c3aa34e236`;
   - result JSON SHA-256 `4a1815f529893056cffd21011771889b956387074e6bc238dbe3a6cc99eb94a6`.

3. **SonotaCo 2023 replacement independent replication**
   - workflow `30921046797`;
   - artifact `8897103051`;
   - artifact digest `sha256:291a1e738b6e63cc36226b7bea1f69b253dcea18ebb97e620006f7ed2544fc3c`;
   - result JSON SHA-256 `ac7b06ba68672688cfcce46bb46150adf3de87622e5de05c6f74ef945d28a075`.

No record-level artifact is read. SonotaCo 2024 is not downloaded or inspected. GhostStream remains blinded.

## Frozen interpretation

The synthesis must preserve all three results without averaging away failures:

- the fixed-4° method passed the complete standalone SonotaCo 2025 final-development standard;
- it failed the preregistered calibration-seed robustness standard because fresh-panel median k=6 recall at alpha 0.05 declined materially from the original panel;
- it failed the sole replacement independent replication because strict-tail k=4 recall at alpha 0.01 was 3/164, below the frozen 9/164 requirement;
- nevertheless, the independent panel passed every calibration, false-positive, AUROC, comparator, fold, moderate k=4, k=6, k=8, and monotonicity gate.

The final status is therefore **promising and strongly transferring, but not fully robustly replicated under the preregistered complete standard**. It may be presented as a well-calibrated methodology candidate with explicit limitations. It may not be presented as independently confirmed, and the failed gates may not be repaired by more tuning, panels, seeds, calibration counts, or threshold changes.

This workflow authorizes no GhostStream application, catalogue scan, detector revision, or additional SonotaCo experiment.
