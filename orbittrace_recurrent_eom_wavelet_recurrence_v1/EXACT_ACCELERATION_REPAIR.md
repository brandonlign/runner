# Exact wavelet acceleration after prelabel no-result

No scientifically valid wavelet-recurrence GMN outcome exists yet.

The brute-force frozen v3 implementation constructs a full pairwise `n x n` radius matrix for each annual family. Inspection of the already-authorized binding recurrent-EOM prelabel (membership only, no new truth) shows that some candidate families are very large, making the direct matrix implementation unnecessarily memory-heavy. The cancelled/technical runs produced no completed successor order, no prelabel, and no scientific result.

This repair changes implementation only, not the statistic.

The frozen v3 weight is nonzero only when

`r^2 = angular_term + speed_term <= TRUNCATION_RADIUS^2 = 16`.

Because `speed_term >= 0`, every nonzero contribution must satisfy

`angular <= 4 deg * 4 = 16 deg`.

The exact accelerator therefore:

1. maps every radiant to the same unit vector used by the frozen v3 source;
2. uses a Euclidean unit-sphere KD-tree only to obtain a superset of contributors within exactly 16 degrees of each test radiant;
3. recomputes the original angular term, asymmetric 10%-of-test-speed term, `r^2`, truncation, weight formula, self-exclusion, coefficient sum, positive clipping, top-4 selection, and L2 energy exactly as frozen v3 defines them.

No approximate radius, fitted neighborhood size, altered kernel, downsampling, family-size cap, parameter, score normalization, candidate change, ranking change, gate change, or truth use is allowed.

Before another GMN execution, the accelerator must reproduce the direct frozen v3 implementation on deterministic synthetic and randomized fixtures to tight numerical tolerance, including longitude wrap, dense clusters, dispersed points, and varying speeds.

The protocol and strong `+2` recovered@100 gate remain unchanged. The first technically valid post-prelabel outcome remains binding.