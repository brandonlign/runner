# ASFN pristine validation attempt 31834974219 — technical no-result

Run `31834974219`, job `94879143992`, execution commit `e2cc9947683254f8a5c60f15c0b27eb8be2f69ea` is **not a scientific ASFN result**.

All frozen source pins passed and the exact archive SHA-256 was verified. The scientific runner then stopped in its first-pass parser at physical record 1 with:

`RuntimeError: invalid ASFN time at record 1`

The failure occurred before HDBSCAN fitting, before candidate construction, before the prelabel payload, before `shw` access, and before any metric/result JSON.

Preserved artifact `9232130761`, digest `sha256:352aaeecd954bcb7fcb85ff36a711a613e1f1580dd578b8743e7e49d05eedaa7`, contains only environment/version/execution/source provenance. It contains neither `RECURRENT_EOM_ASFN_2018_2019_PRELABEL.json` nor `RECURRENT_EOM_ASFN_2018_2019_VALIDATION.json`.

The frozen scientific protocol, years, eligibility, representation, HDBSCAN settings, recurrent-EOM objective, ranking, external label semantics, evaluator, and gate remain unchanged. Only a separately audited file-framing/parser repair may precede another binding execution.
