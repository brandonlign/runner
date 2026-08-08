# OrbitTrace methodology synthesis after v11

## Current scientific decision

The promoted incumbent remains **v8 pooled-year-centroid label-free sparse-support multiplicity**.

This document is a synthesis only. It does not modify or execute a detector, open an external catalogue, access the 20°–55° withheld region, or authorize an OrbitTrace reveal.

## Why v8 remains the incumbent

Passed v8 target-excluded GMN 2022/2023 development:

- recurrent families: **226**;
- qualified known showers: **95**;
- multiplicity recovery@100: **58**;
- persistence recovery@100: **59**;
- Brown recovery@100: **55**;
- v3 recovery@100: **55**;
- multiplicity top-100 dominant precision: **0.6884631113**;
- multiplicity MRR: **0.04553113894**;
- artifact: `9009728299`;
- artifact ZIP digest: `sha256:88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`;
- verdict: `PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT`.

v8 exists because passed v6 contained a real source-semantic defect: a connected family could contain multiple same-year components while the family centroid dictionary silently retained only one of those component centroids. v8 repairs that representation by recomputing each family-year centroid from the union of all unique same-year family events using the source-grounded component statistic. The repair is non-vacuous (75 families / 118 family-years affected). Although v6 multiplicity recovery was 60/100 and v8 is 58/100, v6's overwritten-centroid semantics are not acceptable as the final scientific implementation.

## Successors that did not beat v8

### One-component-per-year v7

Changing the family topology to maximum-cardinality/minimum-distance one-to-one recurrence produced 533 families but destroyed recovery: multiplicity 2/100 and persistence 44/100. Permanent no-go.

### Reciprocal/mutual-nearest recurrence

A separately frozen mutual-nearest formulation produced 370 families, persistence 48/100 and multiplicity 16/100. Permanent no-go.

### Complete-link recurrence

Earlier frozen linkage benchmarking showed single-link connected recurrence substantially outperformed complete-link on both development and held-out known showers. Permanent no-go as a replacement family topology.

### Support-ball overlap v9

Parameter-free maximum-member-radius support balls produced 445 families but multiplicity recovery 36/100 and persistence 43/100. Permanent no-go. Artifact `9011423691`.

### Multiplicity/persistence rank consensus v10

Exact v8 families/scores were retained and two preregistered equal-weight rank fusions were frozen before labels. `rank_product` improved development-panel recovery to 29 versus v8 multiplicity 25 and persistence 28, but MRR 0.053518 was below the v8 multiplicity development-panel MRR 0.057477. The preregistered authorization gate therefore kept the validation-label panel unopened. Permanent no-go. Run `31226223630`, artifact `9012506250`, digest `sha256:2745bf01f6254004efa2a48feae5134a5400be3bea8ce5370f4c9c39a5f7fe37`.

### Exact observed-support contact v11

Different-year components were linked iff at least one actual member-event pair had the exact inherited frozen distance <=1.5. Every accepted component edge had an exact member-pair witness. The contact graph contained 9,317 edges versus 7,933 v8 fixed-centroid edges, including 1,384 contact-only edges and zero fixed-only edges. It generated 369 recurrent families and 108 qualified known showers, but ranking quality regressed:

- multiplicity recovery@100: **56**;
- persistence: **51**;
- Brown: **51**;
- multiplicity top-100 precision: **0.5910866521**;
- multiplicity MRR: **0.0401793783**.

Thus v11 failed the preregistered persistence, multiplicity-recovery, precision and MRR gates. Permanent no-go. Run `31227586508`, artifact `9012964026`, digest `sha256:08f02a4e6c574255dad05f43e650f641fc7ca00515f212e9fda8615eef8a9113`.

## What the negative results imply

The useful sparse-stream signal is not preserved by forcing exclusive cross-year matches, complete-link compactness, adaptive support balls, or broad exact support contact. v8's fixed-radius connected-family topology is currently the only tested family formulation in this lineage that simultaneously preserves the multi-fragment recurrence structure and the strong sparse-shower ranking.

Simple post-hoc structural reranking and equal-weight multiplicity/persistence rank fusion have also failed to improve v8 under preregistered gates.

Therefore no further recurrence-radius, contact-count, overlap-fraction, nearest-neighbor, complete-link, one-to-one, support-radius, rank-weight or rank-fusion tuning is scientifically authorized from these results.

## One remaining clean-room methodology question

There is one unresolved layer that is logically distinct from the failed topology/rank-fusion paths:

**When a valid v8 connected family contains multiple components from the same year, is the source-grounded pooled-year centroid representation the best way to construct the family-year scoring evidence, or can a separately preregistered representation of the already-existing same-year components preserve the semantic repair while retaining more of the v6 ranking signal?**

This document intentionally does **not** specify an aggregation rule, score, threshold, weight, or candidate set for that question. Doing so here would create a new method after the analyst-session blinding event described below.

A future successor, if pursued, must:

- start from exact v8 proposal/component/family topology;
- leave radius 1.5 and connected-family semantics unchanged;
- change only the family-year evidence representation/scoring for duplicate same-year components;
- be preregistered in a separately isolated clean-room methodology session before target-region or new external-value access;
- use target-excluded development data only;
- require non-regression against the exact v8 recovery, precision and MRR baselines;
- become a permanent no-go if its frozen gates fail;
- never use OrbitTrace target information to choose a representation.

If no such clean-room successor is pursued, or if it fails, **v8 should be treated as the final methodology architecture** for the pending external-validation and blind-discovery tracks.

## Analyst-session blinding boundary

The v11 protocol, source, workflow, parent commit and execution were fully frozen and launched before a later source-archaeology read in the methodology-lead analyst session opened a legacy historical file containing forbidden target constants. That file was not used by v11 and no v11 choice changed afterward. The event was recorded prospectively on PR #373 while v11 was still running.

Accordingly:

- v11 remains a valid frozen pre-exposure experiment;
- this analyst session may synthesize already-frozen evidence but must not design or execute another target-blind successor;
- any post-v11 successor must be designed in a separately isolated clean-room methodology track.

## Current boundary

No OrbitTrace reveal is authorized by this synthesis. The 20°–55° target region remains unavailable to methodology development. External validation, literature benchmarking and the dormant final blind-discovery firewall remain separate tracks.
