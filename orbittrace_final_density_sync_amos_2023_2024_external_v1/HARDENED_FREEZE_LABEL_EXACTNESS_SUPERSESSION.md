# Hardened AMOS freeze supersession — label-transport exactness gap

## Classification

**ENGINEERING-ONLY PRE-DATA PROVENANCE. NO AMOS SCIENTIFIC DATA OR OUTCOME EXISTS.**

The previously written `EXECUTION_FREEZE_HARDENED.json` (Git blob `804d37a0cc86b1cfd848ee9ea68192bc3a3b4ef7`) and its binding v3 audit run `31865942127` are preserved, but they are **not authoritative for future AMOS execution**.

## Why the earlier hardened freeze is superseded

Binding zero-data run `31865942127` completed successfully at execution head `36052457f36f250758f3391e2917e6e87d6c9b1a`, artifact `9242001104`, digest `sha256:255234e57f3cd582cfe21e50394ba03df8d9ad7f92b7b8069a97180911708394`.

That run used evaluator blob `bb2a1ba553fb57e573e85df39ccad1b69fe3b541`. After the run, adversarial review found that the label loader called `.strip()` on every supplied `shower_association`. The already-frozen `EVALUATOR_HARDENING_V3_FREEZE.md` requires valid non-background association strings to be preserved exactly and forbids relabeling/normalization. The v3 adversarial suite at that execution head tested exact `SPORADIC`/ambiguous aliases but did not test exact preservation of an ordinary valid shower code or rejection of surrounding whitespace.

Therefore the earlier run is a genuine PASS for the checks it executed, but it did **not establish complete conformance with the pre-existing v3 hardening freeze**. It cannot authorize the future AMOS label-evaluation endpoint.

This is not a scientific failure or scientific rerun. No AMOS provider request had been sent and no AMOS event row, geometry, association, protected target information, SonotaCo, ASFN, EFN, MAARSY, or DMS value had been accessed.

## Engineering-only conformance repair

The evaluator was corrected solely to enforce the already-frozen transport contract:

- current evaluator Git blob: `c45e4739ea68639945b13de54f6e24dc9d870ba3`;
- repair commit: `726032e3f815d8be0c5510b6b9a823eab2fef525`;
- it now compares raw label text to its trimmed form and fails closed on surrounding whitespace instead of silently normalizing it;
- exact valid association text is otherwise passed unchanged to the inherited frozen metrics.

A new zero-data audit was added:

- `audit_label_transport_exactness_v3.py` Git blob `b16778cd10cbbb7704a4ee007a14030b97e07500`;
- it requires exact `SPORADIC` acceptance;
- it requires an ordinary mixed-case synthetic shower code to survive unchanged into inherited metric label keys;
- it rejects all predeclared ambiguous no-association aliases;
- it rejects surrounding whitespace rather than normalizing it.

The v3 workflow was updated to pin the repaired evaluator and this new audit:

- workflow Git blob `0fe45c38e3f15c94c688326a969c7cb3a4975f55`.

## Required replacement evidence

Before future AMOS execution, a clean zero-data v3 retry must pass on the repaired evaluator/workflow. Only then may a new execution freeze supersede both:

1. the original `EXECUTION_FREEZE.json`; and
2. `EXECUTION_FREEZE_HARDENED.json` blob `804d37a...`.

The replacement freeze must record the new run/artifact/result hashes and the label-transport audit result explicitly. An independent freeze-integrity audit must then rehydrate the new binding artifact(s) by exact run ID.

No provider request or AMOS scientific execution is authorized by this record.
