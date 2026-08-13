# Frozen result — GMN v31 second-support-radius v1

Binding workflow run: `31668340422`

Binding job: `94347681787`

Execution head: `b49dbd5b4c4ddb194a34c189c72cc64a2f64ae2f`

Frozen protocol commit: `d6d00498300e80f2b14e93dc51421669667de2e0`

Frozen implementation commit: `ae0fd70a9270d3749b89fc61cc63ecc85db471ea`

Verdict: **FAIL_GMN_V31_SECOND_SUPPORT_RADIUS_V1**

## Provenance and engineering gates

All pre-science and post-result enforcement gates passed:

- exact runtime/source compilation passed;
- exact diversity/evaluator source verification passed;
- deterministic analytic second-support-radius engineering self-tests passed with `PASS_SECOND_SUPPORT_RADIUS_ENGINEERING_SELF_TESTS`;
- authoritative GMN v31 offline package verification passed with `PASS_AUTHORITATIVE_OFFLINE_PACKAGE_BEFORE_SECOND_SUPPORT_RADIUS`;
- exact 226x23 feature matrix and 226x8 centroid matrix hashes passed;
- exact five strict whole-shower OOF folds and positive/nonpositive reference semantics passed;
- parent raw Euclidean OOF margin reproduced exactly at `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- exact v31 fused parent control reproduced;
- all firewall assertions passed.

Artifact:

- ID: `9168784885`
- digest: `sha256:5a6de5f9b60bc3d0a6324bc914c780cdcaded4f034d94e832213746280cc23ec`

## Binding candidate metrics

Exact v31 parent:

- recovered@25 = **23**
- recovered@50 = **41**
- recovered@100 = **66**
- top-100 dominant precision = **0.7229521515453452**
- MRR = **0.050244164168646674**
- qualified matches = **95**

Frozen second-support-radius equal-rank-fused candidate:

- recovered@25 = **22**
- recovered@50 = **40**
- recovered@100 = **64**
- top-100 dominant precision = **0.7304013345470249**
- MRR = **0.04489810132750275**
- qualified matches = **95**

Local-only second-support-radius diagnostic:

- recovered@25 = **21**
- recovered@50 = **42**
- recovered@100 = **61**
- top-100 dominant precision = **0.6317184221802771**
- MRR = **0.04012989562502354**
- qualified matches = **95**

Metric-unit preservation was applied exactly as frozen:

- parent median absolute k=1 margin = `0.4460321881586118`
- raw second-support median absolute margin = `0.4010322762528463`
- fixed unit factor = `1.1122101999525682`
- raw second-support margin SHA-256 = `d92b96a60270eebfcfcadf6aa0af4e1f449b8023c331e32cf515e44ac685b35f`
- scaled second-support margin SHA-256 = `80e0725a7eb07bde1cb8e6dd06af9218f919100e5b5caae74a1d44c410d057b0`

## Binding gate result

Passed:

- top-100 dominant precision not below parent: **0.7304013345470249 > 0.7229521515453452**;
- qualified count identical: **95**.

Failed:

- recovered@100 must be >66: **64**;
- recovered@50 must be >=41: **40**;
- recovered@25 must be >=23: **22**;
- MRR must be >=0.050244164168646674: **0.04489810132750275**.

The precision improvement is real but cannot rescue failure of the preregistered recovery and MRR gates. This is a binding scientific failure and does not authorize SonotaCo access for this successor.

## Scientific interpretation

The fixed hypothesis was that requiring two same-class local references would reduce dependence on a unique atypically close prototype while preserving v31's local cross-survey-friendly geometry. On target-excluded GMN, that redundancy made the fused top 100 slightly purer but reduced recovery at all three frozen budgets and materially degraded MRR. Therefore the exact `k=2` support-radius mechanism does not improve the v31 parent under the frozen promotion criterion.

No inference is made that all multi-neighbour classifiers fail. However, this result cannot be used to search the neighbour order or aggregation rule after outcome.

## Closure

The exact second-support-radius mechanism is permanently closed. Do not rescue it with:

- `k=3`, `k=4`, or any k search;
- adaptive or class-specific k;
- averaging, median, maximum, trimmed mean, voting, kernel, or weighted aggregation over neighbours;
- first/second-neighbour blends;
- distance weighting;
- reference deletion, pruning, relabeling, or weighting;
- metric, feature, scaling, calibration, diversity, or fusion changes informed by this result.

A future method may use a genuinely independent architectural mechanism only if motivated without tuning from this outcome and after a repository duplicate/governance audit.

## Firewall

No SonotaCo 2013/2014 scientific outcome was accessed for this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remained inaccessible. No raw GMN event rows, raw event IDs, or raw hidden-label event mapping were accessed by this offline successor.
