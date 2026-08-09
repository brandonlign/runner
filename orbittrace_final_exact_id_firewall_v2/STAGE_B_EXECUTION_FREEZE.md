# OrbitTrace exact-ID Stage-B execution freeze

This file freezes execution plumbing only. It does not authorize or execute target access.

## Fixed sequence

1. The promoted detector must first pass its frozen target-excluded development gate, matched Sugar/HDBSCAN superiority gate, and independent prospective/generalization gate.
2. Only after all three promotion gates pass may a separate execution-only child PR run the withheld-reference seal workflow.
3. The seal workflow accepts the already-existing historical withheld-reference artifact by opaque artifact ID + ZIP SHA-256, reads it only after promotion has been proven, rejects non-ID fields, deterministically retains only GMN 2022/2023, and emits schema `orbittrace-withheld-exact-ids-v2` containing only exact stable event ID and year. Target IDs and target counts are never printed by the seal job.
4. The seal run must complete before the final target-uninformed Stage-A run begins.
5. Stage A independently freezes the complete `orbittrace-final-stage-a-ranked-families-v2` primary catalogue without access to the seal or target reference.
6. Stage B is activated only by a separate one-file child request containing the Stage-A run ID and seal run ID. It has no field for a target artifact locator.
7. Before target access, Stage B verifies both run identities/status, proves seal completion predates Stage-A start, downloads and validates the immutable Stage-A artifact, reproduces its canonical SHA sidecar, and passes the frozen Stage-A schema through `evaluate_reveal.load_stage_a`.
8. Only then does Stage B download the exact sealed artifact from the already-fixed seal run, verify its seal manifest and canonical payload SHA, and pass it through `evaluate_reveal.load_target_ids`.
9. The final evaluator is exactly `orbittrace_final_exact_id_firewall_v2/evaluate_reveal.py`; it performs exact stable-ID set intersection only and retains the frozen top-25/top-100 and >=4-per-year / >=8-total recovery gates.

No detector, catalogue, scorer, coordinate, orbit, activity-profile, nearest-neighbor, clustering, membership-growth, merge, or reranking code enters Stage B.

The seal and Stage-B request files are intentionally absent from this freeze branch. Their future execution-only child PRs must each differ from this branch by exactly one request file.
