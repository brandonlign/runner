# OrbitTrace v29 fixed-catalogue oracle diagnostic v1

## Purpose

Diagnose the authoritative exposed-development failure of v29 without defining a successor.

Input is the already-frozen **single canonical v29 SonotaCo catalogue** from run `31437739544`, artifact `9081660704`, catalogue SHA-256 `dd751abd4330f58b4056eb8da473ee4d19ae756211f0538c41b252ffc9fb352b`. That catalogue contains 334 fixed families (25 hard, 84 P19, 225 P20) with fixed memberships and fixed v29 ranks. No candidate generation, membership expansion, model scoring, or ranking is rerun.

The immutable exposed truth/comparator package is run `31405109267`, artifact `9069505548`.

## Diagnostic question

Does the fixed 334-family catalogue contain enough membership-quality headroom for **one common nested ranking** to beat the frozen literature comparator on all four panels, or is the v29 failure already a candidate/membership ceiling?

## Conservative joint-oracle construction

To avoid ambiguity from panel-specific inactive families, restrict the oracle's first 46 positions to families that have at least one member in **all four** immutable panel truth-ID universes. This is deliberately conservative.

Find binary nested selections of exact sizes 9, 11, 34, and 46, with top9 subset top11 subset top34 subset top46. These correspond to the frozen comparator budgets:

- HDBSCAN 2014: 9;
- HDBSCAN 2013: 11;
- Sugar 2013: 34;
- Sugar 2014: 46.

Use exact one-to-one F1 assignment semantics. A mixed-integer feasibility/optimization problem may use truth because this is explicitly an exposed oracle diagnostic. For every panel, require at least the frozen literature recovery count (`F1 > 0.5`) and strictly greater total F1 than the frozen literature macro-F1 threshold. The objective only maximizes total normalized F1 after those pass constraints; it does not define a deployable score.

After solving, construct one common nested order and re-evaluate it with the exact frozen Hungarian evaluator. The diagnostic counts as positive headroom only if the actual evaluator passes all four panels.

## Required outputs

Report:

- number of fixed catalogue families and all-panel-active families;
- actual v29 four-panel metrics;
- exact joint-oracle four-panel metrics;
- current-v29 versus oracle source composition at top9/top11/top34/top46;
- current v29 ranks used by each oracle tier and hashes of selected family identities;
- proof of nesting;
- solver status/optimality;
- conclusion `RANKING_TRANSFER_FAILURE_NOT_CANDIDATE_MEMBERSHIP_CEILING` only if the verified common oracle order passes all four panels.

Do not output known-shower label names.

## Scientific boundary

This diagnostic is **not a method**. The truth-aware order, selected ranks, source composition, or family identities may not be used directly as a deployable ranking, source quota, cutoff, training target, or post-result rescue. No parameter sweep is authorized. Any successor must be independently motivated and separately frozen.

No MAARSY, DMS, OrbitTrace target information, or target-region event access is authorized.