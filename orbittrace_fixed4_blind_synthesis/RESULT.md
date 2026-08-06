# OrbitTrace fixed-4° blind catalogue synthesis

Classification: `BLIND_RECOVERY_WRAPPER_SENSITIVE`

Both preserved catalogue wrappers used the immutable fixed-4° coverage-normalized Mondrian anchored four-clique core and froze their rankings before canonical-member reveal. Their exact final artifact ZIPs were independently verified by SHA-256 before this synthesis.

## Broad ranked-quartet recurrence wrapper

- corpus: complete GMN sporadic years 2019–2025 plus January–July 2026;
- scanned trajectories: **2,394,515**;
- canonical members present in the catalogue: **101 / 101**;
- preserved families examined: top **5,000** at each fixed recurrence threshold;
- exact OrbitTrace overlap: **0** at thresholds 1.5, 2.0, and 2.5;
- verdict: `NO_BLIND_ORBITTRACE_RECOVERY`;
- final artifact: `8957230278`, ZIP SHA-256 `2ee3d5c9edf299c0f9ea69b2d6254d7918e0aa659f8cc2c659bb99ff2dfc0d17`.

## Calibrated component-family wrapper

- corpus: GMN sporadic January 2022–July 2026;
- searched residual events: **2,125,081**;
- recurrent families: **780**;
- selected family: **F0059**, blind rank **59**;
- family years / events: **4 / 39**;
- exact canonical overlap: **29 / 95**;
- overlap by year: **2022: 5, 2023: 4, 2024: 0, 2025: 15, 2026: 5**;
- precision / canonical recall: **0.7436 / 0.3053**;
- fixed-set hypergeometric p-value: **3.8688e-120**;
- 780-family Bonferroni value: **3.0176e-117**;
- verdict: `PARTIAL_BLIND_ORBITTRACE_RECOVERY`;
- final artifact: `8958194010`, ZIP SHA-256 `74c95a3fd59650126a2a298fc1bab5cc055caa91bff2feae6c9256521fdc00aa`.

The calibrated wrapper's final source was committed at `2026-08-06T05:40:18Z`, before the broader wrapper's result was recorded. Its positive result was therefore not constructed in response to the negative wrapper.

## Frozen interpretation

The catalogue-scale outcome depends materially on the generic wrapper around the frozen episode detector. The partial result is real and must be retained, but the broader negative result is equally binding. Together they do **not** justify presenting the novel detector as the primary blind discovery method or describing OrbitTrace as robustly rediscovered by it.

The defensible project structure is:

`exploratory HDBSCAN candidate discovery -> separately developed frozen detector recognition with mixed blind-deployment evidence -> observational validation`

The detector remains valuable as an independently developed sparse-stream method, a targeted frozen recognition path, and a method with one partial blind recovery. The blind-deployment evidence is not strong or stable enough to replace HDBSCAN as the discovery path.
