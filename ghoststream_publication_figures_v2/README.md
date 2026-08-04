# GhostStream publication figures v2

This renderer revises the first GhostStream figure package for manuscript, LISEF/ISEF poster, and presentation use. It is figure-production code only: it does not alter candidate membership, detector thresholds, methods, scores, or scientific conclusions.

## Figure suite

0. **Graphical summary** — poster/presentation overview of the moving radiant, exposure-normalized activity, independent evidence, and the unresolved NOP 004 branch question.
1. **Discovery signature and physical coherence** — direct candidate-versus-local-background activity, annual recurrence, radiant drift, and cross-archive orbital coherence.
2. **Validation and robustness** — annual recurrence, disjoint geographic replication, the frozen 81-cell specification curve, and external-archive support.
3. **Methods workflow** — schematic separation of the historical blind discovery pipeline from the later targeted frozen fixed4 confirmation.
4. **Fixed4 measured evaluation** — exact empirical calibration, independent comparator AUROCs, recovery by stream size, and the retained failed strict recall gate.
5. **Nearest MDC solution** — frozen-rule comparison with NOP solution 004, explicitly preserving that distinct stream versus related branch remains unresolved.

Figures 1–5 are designed around approximately 7.4-inch full-manuscript width. Figure 0 is a wider graphical abstract/poster panel. Every figure is emitted as vector PDF, editable SVG, and 400-dpi PNG.

## Immutable evidence inputs

The workflow downloads and verifies these exact GitHub Actions artifact ZIPs before rendering:

- Canonical GhostStream expert bundle: artifact `8814798136`, SHA-256 `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`.
- Frozen GhostStream fixed4 application: artifact `8899766878`, SHA-256 `0288bd50c88c1dee8bf5b72bd52937116d81026f074667450c99cb8d8c56653c`.
- SonotaCo 2025 fixed4 development: artifact `8896176320`, SHA-256 `b3dd9c80759b749420407e95de0a5ed581e208bbd39c806d9472c00ae9a3529e`.
- Independent SonotaCo 2023 fixed4 confirmation: artifact `8897103051`, SHA-256 `291a1e738b6e63cc36226b7bea1f69b253dcea18ebb97e620006f7ed2544fc3c`.

The renderer also fails closed if preserved scientific invariants change: the 95-member GMN table and yearly counts, five significant confirmation years, source-preserving antihelion rejection, three geographic replications, 81/81 specification passes, 16 external events across eight years, zero hard MDC duplicates among 2,174 solutions, the NOP 004 nearest solution, full targeted GhostStream fixed4 recovery, and the single retained failed independent fixed4 gate.

## Claim boundaries

- The canonical GhostStream discovery is validated.
- Ordinary structured antihelion background is rejected.
- Fixed4 produced strong targeted frozen recovery, but it was not the historical discovery method and did not perform a full blind catalogue rediscovery.
- The official duplicate screen rejects ordinary identity with NOP 004; distinct stream versus a dynamically related branch remains unresolved.
- The Shober–EDMOND subset is shown as supportive but provenance-limited.

## Outputs and provenance

The repository stores the renderer source as checksum-verified compressed parts; the loader verifies its exact byte count and SHA-256 before execution, and CI exports the decoded source alongside the figures.

The workflow uploads all figures, `FIGURE_CAPTIONS.md`, `FIGURE_MANIFEST.json`, the complete output SHA-256 inventory, Python version, and pinned environment. Figure 3 is the only schematic; all other panels plot preserved measured or benchmark records.
