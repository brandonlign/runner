# Engineering repair 1 — lineage-balanced v1

Run `31963429131` is a **NO-SCIENTIFIC-RESULT** attempt.

The generator aborted on the first subset before `TOPOMODAL_LINEAGE_BALANCED_V1_PRELABEL.json` existed. The seal-before-truth, truth evaluation, and result-contract steps were skipped. Therefore no shower truth was evaluated and the frozen successor remains scientifically unopened.

The failure was an implementation error in `generate_prelabel.py`: it correctly reconstructed the *set* of GUDHI finite persistence pairs, but used the sorted persistence array position as though it identified the corresponding `children_` merge node. The frozen scientific definition never specified that shortcut; it specifies each candidate's **density-level lifetime between its own formation and next enclosing merge**.

`generate_prelabel_repair1.py` preserves the frozen architecture, candidate universe, lineage assignment, score definition, ranking rule, support floor, radius, density, comparator, and ten gates. It changes only how the already-defined merge density is calculated:

- for each fixed pair of ToMATo child memberships, compute the highest density superlevel at which those children are connected by the already-fixed radius graph;
- use that exact graph saddle as the node's merge density;
- require the resulting losing-mode `(birth density, merge density)` pairs to reproduce GUDHI's finite persistence diagram to absolute tolerance `1e-12`;
- require every child formation density to be >= its parent merge density;
- independently reproduce the complete exact #1284 candidate membership universe before writing any prelabel.

If any audit fails, the workflow remains a pretruth engineering no-result. No fallback, alternate score, result-informed parameter, or ranking change is authorized.