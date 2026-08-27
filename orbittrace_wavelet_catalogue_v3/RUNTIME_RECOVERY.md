# Wavelet catalogue v3 runtime recovery

Run `31115251099`, attempt 1, was cancelled externally during the exact-rescoring stage after all 72 development windows for 2022 had completed their provisional scan. It produced no development verdict and did not reach the integrity gate. The preserved artifact contains only source, environment, and source-audit provenance.

The recovery changes implementation only:

- groups provisionally retained anchors by their already-selected 10° window;
- computes each window's radiant vectors and speeds once;
- retains the complete-window exact rescore for every provisional anchor;
- preserves stable nearest-neighbour tie ordering;
- keeps every scientific constant, calibration rule, threshold, component rule, family link, ranking rule, development year, and blind exclusion unchanged.

The scalar and grouped exact-rescore implementations were compared on deterministic synthetic windows. Wavelet scores, positive-lobe memberships, fixed4 quartet scores, and stable tie handling matched. The authoritative recovery workflow repeats this equivalence test before accessing the development catalogues.

The cancelled attempt is not a scientific pass or failure and is not eligible for promotion. Only a run that reaches the frozen integrity gate and uploads the complete result artifact may be interpreted.
