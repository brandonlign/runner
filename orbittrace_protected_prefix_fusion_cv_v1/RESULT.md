# OrbitTrace protected-prefix fusion CV v1 — binding result

## Verdict

`FAIL_PROTECTED_PREFIX_FUSION_CV_V1_GMN` — closed under the frozen ten-gate contract.

Binding workflow run: `32228331229`

Binding execution branch head: `0a7aa3264037e6a8703e285cf6a9e3019236d7ca`

Binding artifact: `9356396826` (`orbittrace-protected-prefix-fusion-cv-v1-binding-32228331229`)

Artifact digest: `sha256:52a5ae187131a4b793b9bf0dfae82d62f29ff80dfdc52c35bb7859afe31a5f39`

Source prelabel SHA-256: `7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd`

All exact-head, source-hash, frozen-artifact, target-exclusion, and held-out-selection checks passed. The test year was not used for configuration selection.

## Cross-year selections

One prefix quarter was selected on the opposite year across all four buckets at each scale:

- `d=128`, develop 2023 -> test 2022: `q=1.00` (exact recurrent-EOM baseline);
- `d=128`, develop 2022 -> test 2023: `q=0.75`;
- `d=1024`, develop 2023 -> test 2022: `q=0.75`;
- `d=1024`, develop 2022 -> test 2023: `q=1.00` (exact recurrent-EOM baseline).

## Held-out aggregate result

### Fine d=1024

Recurrent-EOM -> protected-prefix fusion:

- qualified total: `20 -> 21`;
- recovered @25/@50/@100/@500: `20/20/20/20 -> 21/21/21/21`;
- mean top-100 dominant precision: `0.3530315709574533 -> 0.3686565709574533`;
- mean fragmentation: `1.0 -> 1.0`;
- qualified nonlower panels: `8/8`;
- strict qualified wins: `1/8`;
- conditional mean MRR: `0.6959325396825397 -> 0.642361111111111`.

### Coarse d=128

Recurrent-EOM -> protected-prefix fusion:

- qualified total: `94 -> 97`;
- recovered @25/@50/@100/@500: `87/94/94/94 -> 87/97/97/97`;
- mean top-100 dominant precision: `0.3396191653933494 -> 0.37012272848036465`;
- mean fragmentation: `1.0 -> 1.0`;
- qualified nonlower panels: `7/8`;
- strict qualified wins: `2/8`;
- conditional mean MRR: `0.23584530975502274 -> 0.2305922306431908`.

## Gate result

Passed 8/10 gates. The only failures were:

- fine mean MRR nonlower;
- coarse mean MRR nonlower.

The valid FAIL is binding. Do not tune the prefix grid, prefix rounding, fusion order, disjointness rule, cross-year selector, admissibility rule, objective, budgets, or gates from this outcome.

## Diagnostic interpretation boundary

The inherited evaluator defines `mrr` as the mean reciprocal rank **only over labels that are represented at least once**. Therefore a successor can recover an additional real shower at a later rank, leave all previously represented showers unchanged, and still reduce this conditional MRR because the new late reciprocal rank enters the denominator. That mathematical property does not change the binding FAIL and must not be used to retroactively relax its gates.

For subsequent method development, this result argues against spending further work on the sparse-GMN ten-gate contract as the primary optimization target. The project-level algorithmic question remains the separately frozen symmetric SonotaCo macro-F1 benchmark, on which tuned ordinary HDBSCAN currently leads recurrent-EOM. Any successor aimed at the main claim should be evaluated under a prospectively frozen, mechanically symmetric protocol there.

## Firewall

The protected inclusive solar-longitude interval `[20°,55°]` remained excluded. OrbitTrace target information/events, SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS were not accessed by this endpoint.
