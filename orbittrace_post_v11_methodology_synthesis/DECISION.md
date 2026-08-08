# OrbitTrace final methodology synthesis after v12

## Current scientific decision

The final methodology architecture is **v8 pooled-year-centroid label-free sparse-support multiplicity**.

This document is synthesis only. It does not modify or execute a detector, open an external catalogue, access the 20°–55° withheld region, or authorize an OrbitTrace reveal.

The sole remaining clean-room representation question identified after v11 has now been tested prospectively as v12 and failed its preregistered successor gate. No further methodology successor is authorized from this lineage before the blind-discovery application.

## Why v8 is final

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

## Successors that did not replace v8

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

### Component-projected centroid v12

A separately isolated clean-room track first ran source-only geometry audit PR #404 on the exact target-excluded v8 family universe. The audit used no shower labels or target-region events and found:

- exact v8 family count: **226**;
- family-years: **452**;
- duplicate same-year family-years: **118** across **75** families;
- median maximum separation among constituent same-year component centroids: **1.6866** in the frozen metric;
- maximum constituent separation: **8.9582**;
- the exact v8 pooled centroid remained within 1.5 of at least one constituent component in all 118 duplicate family-years;
- source-only audit run `31229695771`, artifact `9013581721`, digest `sha256:50590e37a674e9562c776c86820c870a775b2c8c76259873f1259fc804b31ac2`.

Before labels, v12 then froze exactly one representation-layer successor: compute the exact v8 pooled all-event family-year centroid, then project that point onto the nearest existing same-year component centroid using the frozen metric, with stable component-ID tie-breaking. Single-component years remained unchanged. No family topology, proposal rule, radius, multiplicity formula, score threshold, rank fusion, or alternative component rule was searched.

The one-shot target-excluded development run `31231580731` at frozen commit `9e60cc1a077237b23f76f4443829a48915ed4d19` returned:

- recurrent families: **226**;
- qualified known showers: **95**;
- multiplicity recovery@100: **60**;
- persistence recovery@100: **59**;
- Brown recovery@100: **56**;
- v3 recovery@100: **56**;
- multiplicity top-100 dominant precision: **0.7047461025**;
- multiplicity MRR: **0.0450546490**;
- v8 multiplicity MRR baseline: **0.0455311389**;
- artifact `9014245840`;
- artifact ZIP digest `sha256:c62abf8001dc5468acb693576ba73a2c54be5878509b2f181a0280ff55ee93da`;
- verdict: `FAIL_COMPONENT_PROJECTED_CENTROID_V12_NO_GO`.

v12 therefore improved recovery and top-100 precision but failed the preregistered MRR non-regression gate. Because the successor rule and promotion gates were frozen before label evaluation, that failure is binding. v12 is a permanent no-go and does not authorize a different medoid, component-selection, weighted, score-based, or label-based representation.

## What the negative results imply

The useful sparse-stream signal is not improved robustly by forcing exclusive cross-year matches, complete-link compactness, adaptive support balls, broad exact support contact, equal-weight rank fusion, or replacing the source-grounded pooled family-year centroid with a nearest-constituent projection.

v8's fixed-radius connected-family topology plus source-grounded pooled-year-centroid representation is the only tested architecture in this lineage that both repairs the known v6 semantic defect and survives all frozen promotion requirements.

The fact that v12 increased recovery from 58 to 60 and top-100 precision from 0.6885 to 0.7047 does not justify promotion because its MRR regressed below the exact preregistered v8 baseline. The evaluation standard is unchanged after seeing the result.

Therefore no further recurrence-radius, contact-count, overlap-fraction, nearest-neighbor, complete-link, one-to-one, support-radius, component-selection, centroid-projection, medoid, rank-weight or rank-fusion tuning is scientifically authorized from these development results.

## Final methodology boundary

For the pending external-validation and blind-discovery tracks:

- **methodology architecture: v8 pooled-year-centroid label-free sparse-support multiplicity**;
- v7, mutual-nearest, complete-link replacement, v9, v10, v11 and v12 are permanent no-go paths;
- the final target-free discovery application must use the already-frozen v8 architecture rather than any successor;
- no further method development should be conditioned on blind-discovery or external-validation outcomes;
- external validation, literature benchmarking and the dormant final blind-discovery firewall remain separate tracks.

## Analyst-session blinding boundary

The v11 protocol, source, workflow, parent commit and execution were fully frozen and launched before a later source-archaeology read in the methodology-lead analyst session opened a legacy historical file containing forbidden target constants. That file was not used by v11 and no v11 choice changed afterward. The event was recorded prospectively on PR #373 while v11 was still running.

The later v12 successor was designed and executed in a separately isolated clean-room methodology track using only the target-excluded v8 architecture, source-only geometry audit, and frozen development labels after the v12 scoring/ranking rule was fixed. No OrbitTrace target coordinates, members, target-region events, Stage A output or Stage B output entered v12.

Accordingly:

- v11 remains a valid frozen pre-exposure experiment;
- v12 remains a valid separately isolated clean-room experiment;
- v12's failure closes the last authorized representation-layer successor question;
- v8 is final for the pending blind-discovery application.

## Current boundary

No OrbitTrace reveal is authorized by this synthesis. The 20°–55° target region remains unavailable to methodology development. The final target-free v8 blind-discovery firewall remains dormant until its separately frozen authorization conditions are satisfied.