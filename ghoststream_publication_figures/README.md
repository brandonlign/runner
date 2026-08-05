# GhostStream publication figures

This directory renders the checksum-backed figure set for the GhostStream paper, LISEF poster, and judge presentation.

## Figure set

1. **Morphology:** multi-year radiant drift, orbital coherence across archives, and exposure-normalized activity.
2. **Validation:** annual recurrence, disjoint geographic replication, the frozen 81-cell specification curve, and external-archive support.
3. **Fixed4 method:** complete-link quartet schematic, an exact empirical calibration example, independent SonotaCo comparator AUROCs, and recovery versus sparse-stream size.
4. **Manuscript methods schematic:** `render_methods_schematic.py` produces the restrained grayscale flowchart used to distinguish the historical discovery pipeline from the later targeted four-clique sensitivity analysis.

All scientific panels read preserved tables or records from exact GitHub Actions artifacts. The schematic panels are explicitly labelled and do not plot observed or benchmark records.

## Immutable evidence inputs

- Canonical GhostStream package: artifact `8814798136`, ZIP SHA-256 `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`.
- Frozen GhostStream fixed4 application: artifact `8899766878`, ZIP SHA-256 `0288bd50c88c1dee8bf5b72bd52937116d81026f074667450c99cb8d8c56653c`.
- SonotaCo 2025 fixed4 final development: artifact `8896176320`, ZIP SHA-256 `b3dd9c80759b749420407e95de0a5ed581e208bbd39c806d9472c00ae9a3529e`.
- SonotaCo 2023 replacement independent replication: artifact `8897103051`, ZIP SHA-256 `291a1e738b6e63cc36226b7d2d09c888f3476d4dc7abf0175ea9c8103b62ee4`.

## Outputs

The main workflow emits each evidence figure as:

- vector PDF;
- editable SVG;
- 400-dpi PNG;
- manuscript-ready captions in `FIGURE_CAPTIONS.md`.

The manuscript methods schematic is emitted as a 300-dpi PNG at its final 6.5-inch manuscript width. It uses only solid or dashed grayscale outlines, text, and arrows.

The branch is figure production only. It does not alter any detector, candidate membership, threshold, score, or scientific conclusion.
