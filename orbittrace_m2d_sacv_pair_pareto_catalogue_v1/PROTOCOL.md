# M2D SACV validated-pair Pareto catalogue v1 — frozen protocol

## Question
Can SACV's already-validated cross-year local-hypothesis pairs be reported as intact discovery candidates, rather than forcing one pair to replace each M2D parent, while fairly beating the published Sugar2017 and HDBSCAN2025 configurations on the existing target-excluded GMN sparse benchmark?

## Firewall
GMN 2022/2023 only, with the established solar-longitude exclusion 20–55 deg applied before candidate construction. No OrbitTrace target IDs, shower labels, SonotaCo scientific data, or post-result parameter search may enter candidate construction or ranking. Hidden GMN shower truth opens only after the candidate catalogue is sealed.

## Candidate universe
For each existing M2D parent, reconstruct the exact frozen SACV v1 annual admissible hypotheses and exact frozen cross-year recurrence validation. Every validated 2022×2023 hypothesis edge yields one candidate whose membership is the exact union of the two endpoint hypothesis memberships. No component unions, intersections, membership trimming, support pruning, reciprocal-nearest filtering, edge consensus, TopoModal decomposition, pair-size cut, or learned/weighted pair score is allowed.

Annual evaluation membership is the exact candidate union intersected with that frozen annual panel's event universe; equivalently it is the corresponding annual endpoint membership.

## Frozen ranking
Each validated pair has three native ranks, all minimized: (A) M2D parent rank, (B) the 2022 SACV local-hypothesis rank under SACV v1's original annual ordering, and (C) the 2023 SACV local-hypothesis rank under that same ordering.

Rank all pairs by ordinary non-dominated Pareto depth in (A,B,C). Within a Pareto layer, order deterministically by `(max(B,C), min(B,C), A, stable_pair_hash)`. This symmetric endpoint minimax tuple is a tie order only; it is not a fitted score. Exact duplicate event memberships are canonicalized after ranking to the earliest already-ranked provenance so an identical discovery cannot consume more than one literature-capacity slot.

The implementation may compute exact Pareto depth with an equivalent Fenwick dynamic program; this is only an algorithmic optimization and must return the same depth as ordinary Pareto peeling.

## Pretruth structural checks
Before shower truth opens, record per subset: parent count, annual-admissible hypothesis counts, validated pair count, Pareto layer count, exact-membership duplicate count, unique candidate count, pairwise-overlap diagnostics, and capacity shortfall against every already-frozen Sugar/HDBSCAN annual-panel capacity. Do not pad a short catalogue with parents or failed candidates.

## Binding truth benchmark
Use the immutable target-excluded GMN sparse literature-fairness pretruth SHA-256 `8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5` and its fixed comparator capacities. For each of the 16 annual panels and each comparator, truncate this candidate catalogue to exactly that comparator's fixed K (or all candidates if fewer), then use the existing candidate×shower F1 matrix and one-to-one Hungarian assignment.

Promotion requires separately for Sugar2017 and HDBSCAN2025: (1) successor mean assigned macro-F1 strictly greater than comparator mean macro-F1 over its 16 panels, and (2) successor total recovered showers at assigned F1>0.5 at least comparator total. Capacity shortfall is reported and never repaired after truth.

## Decision rule
If either literature gate fails, this exact full-pair three-view Pareto catalogue is a scientific NO-GO. No alternate Pareto objectives, tie orders, dedup order, pair scores, thresholds, quotas, or outcome-guided rescue sweeps are authorized. SonotaCo transfer is authorized only after a binding GMN PASS and must use the exact frozen construction unchanged.
