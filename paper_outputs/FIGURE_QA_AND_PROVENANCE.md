# OrbitTrace recurrent-EOM paper figures — QA and provenance

## 🟢 PASS — generated figures are paper-ready evidence visualizations

Binding generation run: `31890245545`  
Execution head: `c29af33d93d1d5c05567ad2c5aa95da841aa9ce3`  
Artifact: `9248350445`  
Artifact digest: `sha256:59f8ed264b661888d085b17cb2f9d1c91393b849f5a3709dac03e702274912f4`

The renderer reads only `ORBITTRACE_PAPER_EVIDENCE.json`; it does not open any event-level catalogue or protected target information.

Frozen source identities used by the run:

- paper evidence Git blob: `6de9ce9c01df45257780c3436cae6488bca27320`;
- figure renderer Git blob: `89f9d0ca4e950887faf473552b9b38b6b8cbf6bf`;
- selected recurrent-EOM kernel referenced by the evidence: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

## Generated outputs

### Figure 1 — target-excluded GMN fixed-budget recovery

Files:

- `figure_gmn_recovery.pdf` — SHA-256 `98141c6d1bc7fda221f1d37c0fabb4e552df586c7f7900b452ecb1cdb93489a5`
- `figure_gmn_recovery.png` — SHA-256 `fda3d9dddf6b297bc07118e1aa789e669f71eee3d2577bf4cd1cf92011502a86`

Source table:

- `gmn_ordinary_vs_recurrent.csv` — SHA-256 `c8a3e7a2cc3669a791215f83025bf60fc9fd6c2fe164db3a761f14a8c58715cd`

The figure displays the two preregistered fixed-budget recovery metrics most central to the development gate (`@50` and `@100`) for ordinary HDBSCAN EOM and recurrent-EOM in 2022 and 2023. The vertical axis begins at zero; no visual axis truncation exaggerates the modest absolute differences.

### Figure 2 — exposed SonotaCo matched-budget macro-F1

Files:

- `figure_sonotaco_macro_f1.pdf` — SHA-256 `0be6d1964fa958af0536e739f669a57268705881bc0e2140ec00e68fc470a9e5`
- `figure_sonotaco_macro_f1.png` — SHA-256 `8ff1e195b8502df2f8a9ffa7bb48f43b4cfd57edbf7b4d595e86032f4939005e`

Source table:

- `sonotaco_recurrent_vs_v31_literature.csv` — SHA-256 `309feac9aa74e364d2e0a8b2a3cf762efd5e4822b58cb280ee6d1740cee9da72`

The figure shows recurrent-EOM, v31, and the corresponding frozen literature comparator side-by-side for all four established SonotaCo matched-budget panels. SonotaCo is explicitly labelled an **exposed benchmark** in the figure title; the visualization does not imply pristine external validation.

## Visual QA

Manual visual inspection after the binding run found:

- no overlapping labels or clipped axes;
- all bar values legible at normal manuscript viewing size;
- panel labels distinguish Sugar and catalogue-HDBSCAN routes and years;
- zero-based y axes for both figures;
- plotted values exactly match the generated CSV source tables;
- no target-region or event-level information is visualized.

## Scientific scope

These figures visualize already-frozen evidence only. They introduce no new scientific test, selection rule, metric, method change, threshold, dataset, or inference.

Protected solar longitude `[20°,55°]`, OrbitTrace target information/events, MAARSY and DMS remain inaccessible. AMOS is not used.
