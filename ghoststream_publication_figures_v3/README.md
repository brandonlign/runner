# GhostStream publication figures v3

This directory preserves the exact programmatic renderer used for Figures 1-5 in the submission manuscript after the final visual redesign.

## Design goals

- minimal scientific styling with clear hierarchy
- no decorative infographic icons, gradients, or generated artwork
- enough depth to communicate the evidence structure through swimlanes, uncertainty bands, dumbbells, rainclouds, specification atlases, event timelines, empirical-tail curves, heatmaps, and population quantile strips
- no overlapping labels or duplicated figure objects at manuscript size

## Restore the renderer

The renderer is stored as deterministic gzip-compressed base64 text to keep the full source in one GitHub file:

```bash
base64 --decode render_figures.py.gz.b64 | gzip --decompress > render_figures.py
sha256sum render_figures.py
```

Expected renderer SHA-256:

```text
5d5c5db7d559bfccd0ab48458938c3aac894a8ec8f0f130576c17501488079bf
```

## Inputs

Set `GHOSTSTREAM_SUPPLEMENT_ROOT` to the extracted `GhostStream_Supplementary_Material` directory. The renderer also reads the two fixed4 benchmark JSON files already preserved by the v2 workflow under:

```text
$GHOSTSTREAM_FIGURE_ROOT/gsfig_work/method/dev/sonotaco_fixed4_final_development.json
$GHOSTSTREAM_FIGURE_ROOT/gsfig_work/method/rep/sonotaco_2023_fixed4_confirmation.json
```

The v2 workflow pins and verifies the source artifacts that provide those files.

## Render

```bash
python -m pip install -r requirements.txt
export GHOSTSTREAM_FIGURE_ROOT=/path/to/work-root
export GHOSTSTREAM_SUPPLEMENT_ROOT=/path/to/GhostStream_Supplementary_Material
export GHOSTSTREAM_FIGURE_OUTPUT=/path/to/output
python render_figures.py
```

The script writes PNG, PDF, and SVG versions of all five figures.
