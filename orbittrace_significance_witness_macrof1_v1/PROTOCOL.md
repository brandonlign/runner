# OrbitTrace significance-witness macro-F1 v1 — frozen protocol

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID MACRO-F1 DEVELOPMENT OUTCOME.**

This is a new catalogue architecture, not a reinterpretation or rescue of the binding `FAIL_SIGNIFICANCE_PRUNED_TOPOMODAL_V1` result. That prior method remains failed under its own preregistered sparse-GMN MRR/recovery gate. The new method reuses only its immutable **pre-truth candidate memberships**, because those statistically pruned physical components repeatedly showed large recovery and purity gains while the old conditional MRR definition penalized later first hits.

The development evaluator is changed prospectively for this new method to match the metric family actually used in the OrbitTrace paper: one-to-one Hungarian macro-F1 at fixed candidate capacity plus recovered-shower count at `F1>0.5`. No old result is rescored into a PASS and no old gate is relaxed.

## 1. Frozen candidate sources

Use exact immutable significance-pruned prelabel from binding run `31969105299`:

- artifact `9269343581`;
- artifact digest `sha256:64048af08159ca8423834bee9749648abdc133381ec907eb4c00bba31be15925`;
- prelabel SHA-256 `bb5f071e19a39297170730985c65181a05ca92dbe7b366f1a84e77d99e074a9a`.

For every one of the eight frozen target-excluded pooled GMN sparse subsets, this prelabel already contains before truth:

- exact recurrent-EOM candidates and ranks;
- exact statistically significance-pruned physical candidates and ranks;
- exact event-universe SHA and annual counts;
- equal recurrent candidate budget `K`;
- all significance-pruning provenance and firewall fields.

No candidate membership, significance threshold, physical graph, q-density coordinate, permutation count, alpha, support floor, or source prelabel is recomputed or changed here.

## 2. Significance-witness catalogue

For each sparse subset independently, construct one complete candidate order as follows.

Let recurrent candidates be `R_1,...,R_K` in their exact frozen recurrent-EOM order and significance-pruned components be `S_1,...,S_M` in their exact frozen order.

Traverse recurrent candidates in ascending recurrent rank.

For each recurrent candidate `R_i`:

1. compute exact event-count overlap `|R_i intersect S_j|` with every significance component;
2. if the maximum overlap is positive, select the significance component(s) attaining that maximum and break ties by ascending frozen `family_hash`;
3. emit that winning significance component only if it has not already been emitted;
4. if **all** significance overlaps are zero, emit the exact recurrent candidate itself as a recurrent orphan.

After all recurrent candidates have been traversed, append every not-yet-emitted significance component in its exact frozen significance-pruned order.

No overlap fraction, Jaccard threshold, precision estimate, score blend, rank weight, top-K protection, prefix fraction, support threshold, route/year rule, or truth information enters construction.

The output is expected to remain pairwise disjoint because significance-pruned candidates form a partition, recurrent candidates form a partition, and any recurrent candidate retained as an orphan has zero overlap with **every** significance component by definition. This must be proved mechanically before truth.

Candidate prefix: `SWMF1`.

## 3. Why this is distinct from closed orphan/witness lanes

The closed support-cut witness/orphan methods used the support-resolved bifiltration candidate language. This method instead uses the statistically **significance-pruned broad physical partition** as its candidate language; all finite modal subdivisions failing the frozen graph-permutation familywise test were already merged before this method sees any candidate.

The scientific hypothesis is therefore different: recurrent-EOM supplies a label-free ordering witness for a statistically simplified physical partition, while exact recurrent orphans cover structures that the statistically pruned physical representation cannot express at all.

No alternate support-cut winner rule or rescue of the closed support-cut orphan catalogue is performed.

## 4. Development data and firewall

Use exactly the permanent target-excluded GMN 2022+2023 sparse development panels already frozen in the source prelabel:

- denominator 128, buckets 0,1,2,3;
- denominator 1024, buckets 0,1,2,3;
- deterministic `ORBITTRACE_SCALE_STRESS_V1` event hashes;
- protected solar longitude `[20.0,55.0]` excluded inclusively before the source prelabel was created.

Forbidden during candidate construction:

- shower truth;
- OrbitTrace target information/region;
- SonotaCo rows or truth;
- ASFN/EFN event rows;
- AMOS;
- MAARSY/DMS;
- result-informed candidate suppression or ordering.

The complete SWMF1 prelabel must be SHA-256 sealed before GMN truth is opened.

## 5. Prospective paper-aligned GMN evaluator

After prelabel seal only, reconstruct the exact annual event universes and known-shower labels from the same frozen target-excluded GMN source used by the prior sparse evaluations.

For each denominator/bucket/year panel:

- let `K` be the inherited recurrent-EOM candidate count from the frozen prelabel;
- evaluate exactly the first K recurrent candidates and the first K SWMF1 candidates;
- truth labels equal to exact `SPORADIC` are excluded from the shower set;
- a truth shower is eligible iff it has at least 4 events in that annual sparse event universe;
- restrict every predicted candidate to the same annual universe;
- form the full truth-shower × candidate F1 matrix;
- perform one-to-one Hungarian assignment maximizing F1, with zero padding exactly as in the current paper benchmark;
- report macro-F1 over **all eligible showers**, assigning zero to unmatched truth showers;
- report recovered shower count as assigned `F1>0.5`.

This is deliberately the same scoring semantics used in the current paper SonotaCo benchmark. Conditional MRR, top-100 dominant precision, and old positive-match qualification rules are diagnostic only and do not enter this new promotion gate.

## 6. Frozen GMN promotion gate

Aggregate separately over the eight annual panels at each scale (`4 buckets × 2 years`).

For denominator 1024 (fine) and denominator 128 (coarse), require:

1. mean Hungarian macro-F1 SWMF1 >= recurrent-EOM;
2. total recovered `F1>0.5` SWMF1 >= recurrent-EOM;
3. panelwise macro-F1 non-regression in at least 6/8 panels.

Across the two scales additionally require:

4. strict mean macro-F1 improvement at at least one scale;
5. candidate budget sufficient in all eight pooled subsets;
6. output candidate memberships pairwise disjoint in all eight pooled subsets;
7. mechanism active in at least one pooled subset.

All conditions are mandatory. A technically valid FAIL closes exact significance-witness macro-F1 v1. No overlap rule, tie rule, append rule, candidate source, budget, metric, eligibility threshold, or gate may be changed after outcome.

## 7. Exact current-paper validation

Before the first technically valid GMN macro-F1 outcome, freeze a separate dormant validation contingency.

Only if the GMN gate returns full PASS may exactly one SonotaCo validation execute, using the benchmark currently used in the paper:

- Sugar 2013, B=40;
- Sugar 2014, B=43;
- published-configuration HDBSCAN 2013, B=14;
- published-configuration HDBSCAN 2014, B=14;
- pooled 2013+2014 label-free access before truth;
- same route-specific universes;
- same eligible shower rule;
- same one-to-one Hungarian macro-F1 and `F1>0.5` recovery semantics.

The later symmetric tuned-HDBSCAN benchmark remains secondary characterization only and cannot replace or rescue the current-paper validation.
