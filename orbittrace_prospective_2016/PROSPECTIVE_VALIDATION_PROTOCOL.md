# OrbitTrace v8 SonotaCo 2016 one-shot prospective validation

## Frozen method

The prospective method is exactly `orbittrace_v3_fixed4_offset_pos050_v8`, selected before any 2016 scientific scoring.

Its statistic is:

`T = max(-log(p_v3), -log(p_fixed4) - 0.50)`

where both component p-values are bin-wise empirical upper-tail p-values, and the final T significance is calibrated against paired leave-one-out null T values from the same Mondrian bin. Reporting alpha is 0.05.

No rejected v8 candidate is permitted in the prospective runner.

## Frozen prospective universe

Detector-free audits fixed:

- SonotaCo archive SHA-256 `f1fc4586d3efe71b9dc419261c9ad252c5d4f12e80439e94b56c86445520e530`;
- annual member SHA-256 `6035614d6aa663f0ab0ed63e8e93f439d6e3969307085fc872eb2aaeff79be1f`;
- prospective parser SHA-256 `96035178fba30ecbfcbc53e35745b2032417ee9989a850009aeddb0041150cf2`;
- 33 supported Mondrian bins;
- 30 eligible showers;
- 4,224 calibration episodes;
- 2,112 held-out negative episodes;
- 480 positive benchmark episodes.

The 20°–55° OrbitTrace blind interval is removed by the frozen parser before label normalization/storage.

## Two-job firewall

The workflow first runs a **source-only audit job**. That job does not contain or access the 2016 archive URL. It reconstructs the exact parser, benchmark runner, selected v8 scoring layer, and prospective evaluator; audits that only the selected +0.50 v8 method is present; hashes the full source bundle; and uploads that exact bundle as an artifact.

The **one-shot validation job** depends on the source-only job. It downloads the exact audited source bundle from the same workflow run, verifies every source hash, then and only then downloads the frozen 2016 archive and executes the prospective benchmark once.

The science job may not rebuild or alter the detector after opening the prospective archive.

## Frozen prospective gates

A prospective pass requires every gate:

1. selected v8 weak-stream AUROC strictly above Brown-family wavelet;
2. selected v8 k=4 recall at alpha=.05 at least fixed4;
3. selected v8 k=6, k=8, and k=12 recall each no more than 0.03 below Brown-family wavelet;
4. pooled selected-v8 FPR at alpha=.05 <= 0.055;
5. worst reporting-sector selected-v8 FPR at alpha=.05 <= 0.08;
6. all source, parser, transport, count, calibration, comparator, and eligibility integrity gates pass.

A scientific failure is final for this prospective test. No margin, threshold, component, calibration rule, candidate family, or gate may be changed or rerun using the 2016 result.

A technical failure before prospective metrics are emitted may be repaired only if the repair changes no scientific rule and preserves explicit provenance.
