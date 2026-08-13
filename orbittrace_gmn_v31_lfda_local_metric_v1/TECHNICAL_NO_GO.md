# GMN v31 LFDA local-metric v1 — frozen technical no-go

Status: **TECHNICAL NO-GO — no scientific ranking outcome produced**.

Authoritative first execution: GitHub Actions run `31664668975`, job `94336548470`, commit `15a981c05e97ae0054248bd7534db0f0413a0ca1`, artifact `9167471484`, artifact digest `sha256:9862c69da9e632ca8449a334b755a6c272f5a104ecd304f483711324affd3874`.

All frozen source/package checks passed before LFDA construction, including the authoritative target-excluded offline package and exact v31 evaluator provenance.

The first outer-fold LFDA construction then failed the preregistered feasibility condition:

`LFDA within scatter is not positive definite; no regularization rescue allowed`

The failure occurred before a complete LFDA transform, before any 226-family LFDA score vector, before diversity/fusion, and before any recovery/precision/MRR result was produced. Therefore this is **not** a scientific PASS/FAIL against v31; it is a technical infeasibility of the exact frozen unregularized full-r=23 LFDA mechanism on the GMN development representation.

The frozen protocol explicitly prohibited ridge regularization, shrinkage, pseudoinverse/generalized-singular handling, eigenvalue cutoff, reduced output dimension, alternate local-scaling K, kernel LFDA, affinity changes, or Euclidean/LFDA blending. Those are not authorized as post-failure rescues.

Accordingly the exact `GMN_V31_LFDA_LOCAL_METRIC_V1` method is closed as technically infeasible. Any future method using a regularized or reduced-rank local discriminant construction would require a genuinely new independently motivated protocol and may not be presented as a rescue of this failed frozen execution.

Scientific firewall remained intact: only the authoritative target-excluded GMN 2022+2023 offline development package was accessed; no raw event rows/IDs, SonotaCo 2013/2014, protected 20°–55° target-region data, OrbitTrace target information/events, MAARSY, or DMS were accessed.
