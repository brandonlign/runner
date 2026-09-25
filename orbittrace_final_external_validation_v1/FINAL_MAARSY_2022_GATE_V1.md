# OrbitTrace final MAARSY 2022 no-retuning generalization gate — v1

## Status and firewall

This is a **pre-result protocol freeze** for the final external-generalization stage. It is frozen before any SonotaCo 2013/2014 scientific result and before any MAARSY event-level scientific value, known-shower truth, detector output, or performance endpoint is opened.

It does not authorize MAARSY execution. It defines the candidate-specific external evaluation that must be implemented and source-audited before SonotaCo 2013/2014 scientific access.

The OrbitTrace target, target-region events, target identity, target coordinates/orbit/radiant/activity information, and prior target recovery information remain inaccessible. Solar longitude 20°–55° is removed from **both** MAARSY annual scans before any detector processing or truth access.

## Frozen method and annual roles

The final GMN-developed method is M0 / #839 URC union ranking with original frozen M0 memberships.

External detector input is the fixed ordered pair:

- **MAARSY 2021:** unlabeled recurrence-support scan only;
- **MAARSY 2022:** sole scored external-validation year.

MAARSY 2021 may provide only raw label-free detector input required by the exact two-annual-scan hard-v8/P19/P20 recurrence mechanism. **No 2021 known-shower truth, mapping, performance metric, recovery count, selection statistic, or success criterion may ever be opened or computed.**

No pseudo-year, alternate support year, alternate scored year, or post-result substitution is permitted.

## External comparison question

The external gate tests the exact development claim that #839 improves **catalogue ranking/recovery efficiency** over its frozen hard-v8 ancestor without buying that gain through broad membership degradation.

Therefore the no-retuning external comparison is:

- final #839 URC catalogue, versus
- exact hard-v8 catalogue,

on the same MAARSY (2021 support, 2022 scored) inputs and the same exact 2022 row universe.

This is not a literature-comparator test. Sugar and catalogue HDBSCAN are reserved for the one-shot SonotaCo 2013/2014 literature stage.

## Pre-truth output freeze

Before **any 2022 known-shower truth** is opened, both methods must freeze and hash:

1. exact shared 2021/2022 input-row manifests after identical quality cuts and target exclusion;
2. complete hard-v8 candidate list, family IDs, exact members by year, and rank order;
3. complete #839 candidate list, family IDs, exact members by year, 34 application features, serialized-model identity, diversity-order identity, and final rank order;
4. exact source/configuration hashes proving the pair-portable generator and ranker reproduce the frozen GMN method;
5. a statement that no truth label or catalogue mapping was available to either detector.

Any change to a detector output after 2022 truth opens invalidates the external test.

## Exact scored universe

Scientific scoring uses **2022 only**.

Let `U2022` be the exact 2022 event-ID row universe on which both methods and the known-shower reference can be represented after the identical frozen cuts.

For each candidate family, its scored member set is the intersection of its frozen 2022 members with `U2022`. 2021 members affect family existence exactly as the frozen detector requires, but they are never scored.

An eligible known shower is a non-sporadic 2022 truth label with at least **4** usable members in `U2022`.

Frozen size strata use eligible 2022 truth membership count:

- 4–9;
- 10–24;
- 25–49;
- 50–99;
- 100+.

The principal sparse/weak stratum is the union **4–24**.

## Candidate-burden parity

#839 may not claim external generalization merely because it emits more families.

Define the frozen candidate budget `B` as the number of hard-v8 candidate families with at least one scored 2022 member in `U2022`.

- hard-v8 is evaluated using all `B` such families in its frozen order;
- #839 is evaluated using the first `B` families in its frozen catalogue order that contain at least one scored 2022 member in `U2022`.

No padding is allowed if #839 has fewer than `B` eligible families.

Rank-prefix endpoints use `K = 25, 50, 100`; a required prefix that exceeds `B` makes the panel power-inconclusive rather than changing `K` post hoc.

## One-to-one truth assignment

At each required rank prefix and at the full budget `B`, candidate families and eligible known showers are matched by deterministic **maximum-total-F1 one-to-one bipartite assignment** on 2022 scored members only.

For one candidate/shower pair:

- `overlap = |candidate ∩ shower|`;
- `precision = overlap / |candidate|`;
- `recall = overlap / |shower|`;
- `F1 = 2PR/(P+R)` when `P+R > 0`, else 0.

Each candidate may match at most one shower and each shower at most one candidate. Equal-total-weight ties are resolved lexicographically by frozen candidate family ID then shower ID.

A matched shower counts as a **qualified recovery** only when the assigned pair has:

- overlap >= 4, and
- precision >= 0.50.

This preserves the development-era #839 recovery meaning while adding one-to-one anti-fragmentation protection.

For every eligible shower, unmatched or nonqualified assignments contribute F1 = 0 to macro calculations.

## Frozen power floor

The panel is eligible for a scientific PASS/FAIL only if all are true:

- `B >= 100`;
- at least **30** eligible 2022 known showers exist in `U2022`;
- at least **10** eligible showers are in the 4–24 sparse/weak stratum;
- hard-v8 has at least **10** qualified recoveries at rank 100.

Failure of any power condition returns `POWER_INCONCLUSIVE_FINAL_MAARSY_2022` and does not satisfy external generalization. It does not authorize a replacement year or dataset.

## Frozen primary endpoints

For each method compute:

- qualified recovered showers at ranks 25, 50, and 100: `r25`, `r50`, `r100`;
- qualified recovered sparse/weak 4–24 showers at rank 100: `sparse_r100`;
- full-budget one-to-one macro F1 over all eligible 2022 showers: `macro_f1_B`;
- full-budget number of qualified recovered showers: `qualified_B`.

The scientific effect bar for rank-100 improvement is fixed as:

`required_r100_gain = max(2, ceil(0.10 * hard_v8_r100))`.

This requires at least two additional recovered showers and at least a 10% gain over the frozen hard-v8 external baseline.

## Uncertainty check

Run a deterministic **10,000-replicate paired stratified bootstrap over eligible 2022 showers**, seed `20260809`.

Strata are 4–24 and >=25. Within each replicate, resample showers with replacement independently inside each stratum while preserving each stratum's observed sample size.

For each shower, the paired rank-100 recovery indicator is 1 if that shower is a qualified recovery under the method's frozen rank-100 one-to-one assignment and 0 otherwise. The bootstrap statistic is the #839 minus hard-v8 mean recovery-indicator difference over the resampled eligible shower set.

The exact percentile 2.5th percentile is the frozen 95% lower bound. The one-to-one assignments are **held fixed** during resampling; the bootstrap quantifies uncertainty over the shower population, not alternate catalogue rematchings.

## PASS gate

Only `PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION` satisfies the project external-generalization requirement.

A PASS requires **all** of:

1. all source, transport, output-freeze, target-firewall, and truth-boundary integrity checks pass;
2. the power floor passes;
3. `URC_r25 >= hard_v8_r25`;
4. `URC_r50 >= hard_v8_r50`;
5. `URC_r100 >= hard_v8_r100 + required_r100_gain`;
6. `URC_sparse_r100 >= hard_v8_sparse_r100 + 1`;
7. `URC_macro_f1_B >= hard_v8_macro_f1_B - 0.02`;
8. `URC_qualified_B >= hard_v8_qualified_B`;
9. the 95% bootstrap lower bound of the paired rank-100 recovery-rate advantage is **> 0**.

This gate demands a meaningful externally reproduced ranking gain, at least one additional sparse/weak recovery, broad membership non-regression, non-inferior total qualified catalogue yield, and positive uncertainty support.

## Verdict vocabulary

The external stage returns exactly one of:

- `PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION`;
- `FAIL_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION`;
- `POWER_INCONCLUSIVE_FINAL_MAARSY_2022`;
- `EXTERNAL_ARCHITECTURE_INCOMPATIBLE_FINAL_MAARSY_2022`;
- `INVALID_FINAL_MAARSY_2022_INTEGRITY`.

Architecture incompatibility is reserved for inability to reproduce a frozen required observable, annual scan, generator, feature, model, or rank operation exactly. It is not permission to invent a proxy or alter the method.

## Consequence and no-retuning rule

This protocol is frozen **before** SonotaCo 2013/2014 scientific access.

After any SonotaCo or MAARSY scientific value is opened, none of the following may change in response to the result:

- support/scored years;
- quality cuts or row universe;
- proposal rules;
- ranking features/model/diversity rule;
- family memberships;
- candidate budget rule;
- truth eligibility;
- assignment rule;
- power floor;
- endpoint definitions;
- effect bars;
- bootstrap procedure;
- PASS/FAIL criteria.

A scientific external FAIL is final for #839. A power-inconclusive or architecture-incompatible result does not unlock OrbitTrace and does not authorize retuning or dataset substitution.

Only a prior final SonotaCo literature-superiority PASS plus exact `PASS_FINAL_MAARSY_2022_NO_RETUNING_GENERALIZATION` may authorize the separately frozen blind OrbitTrace search.