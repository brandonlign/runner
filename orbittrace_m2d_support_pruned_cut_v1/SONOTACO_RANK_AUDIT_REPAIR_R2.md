# SonotaCo M2D rank audit repair r2

The original zero-truth ranking workflow run `32288839233` entered the exact M2D ranking step but its independent brute-force verification set included candidate index 0. In the already-sealed support-pretruth catalogue, that candidate has 4,068 members, making the verification-only brute enumerator computationally pathological. The exact C++ M2D scorer and the ranking rule do not depend on the brute-audit indices.

This repair is engineering-only and is frozen before any SonotaCo truth access. It derives a temporary execution copy of exact `rank_sonotaco_m2d.py` Git blob `5cdf7e8b7d202a6335d832b89a8f81c7ff781d57` and replaces exactly one audit-loop line:

`for ci in sorted(set([0, n // 4, n // 2, (3 * n) // 4, n - 1])):`

with

`for ci in (28, 55, 93, 165, 211):`

These five audit indices are the same fixed moderate indices used by the binding internal-mass SonotaCo exact-accelerator audit. In the sealed support-pruned pretruth their member counts are 40, 13, 9, 6, and 7. The replacement changes only which independent brute-force checks are performed after exact graph construction; it cannot change any candidate membership, graph, exact C++ score, M2D ordering, tiebreak, parameter, or scientific gate.

The workflow must prove the source transformation is exactly one line and persist both original and derived source hashes before downloading scientific inputs. It then executes the same zero-truth ranking contract on the same rows, sealed support-pretruth, structural source, baseline helper, and exact C++ scorer. Truth artifacts remain absent throughout ranking. The repaired ranked payload is sealed and may be consumed by the already-frozen ranked-only truth evaluator.

Any mismatch in a repaired brute audit is a technical/scorer-integrity failure. It does not authorize changing the method or audit set.