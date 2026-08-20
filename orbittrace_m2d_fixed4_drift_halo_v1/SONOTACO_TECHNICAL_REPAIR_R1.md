# SonotaCo transfer technical repair r1

Binding run `32316234675` failed before any halo construction, pretruth artifact creation, SonotaCo truth download, or scientific endpoint. The first exception was:

`RuntimeError: frozen catalogue-v3 runtime was not decoded`

The frozen dependency `orbittrace_sparse_support_multiplicity_v5.run_holdout.load_frozen_runtime()` requires exact audited catalogue-v3 source to exist at `/tmp/run_wavelet_catalogue_v3_development.py`. The original transfer runner installed the same immutable source checkout but omitted the pre-existing source-audit call that materializes that exact file.

Repair r1 changes only execution plumbing in `run_sonotaco_transfer.sh`: before any scientific input or truth access, run exact immutable `frozen-v8/orbittrace_wavelet_catalogue_v3/audit_development_source.py`, verify decoded source SHA-256 `ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51`, and require the decoded runtime file to exist with that hash.

No method source, fixed4 seed, confidence level, drift fit, covariance, parent catalogue, candidate order, event membership rule, truth artifact, paired evaluator, success gate, target firewall, or scientific parameter changed.

The first technically valid execution after this exact repair is binding. Any duplicate execution is confirmation-only.