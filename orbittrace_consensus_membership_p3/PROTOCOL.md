# OrbitTrace P3 — frozen dual-membership consensus successor

## Status and activation

This protocol is frozen before the authoritative P2 development verdict exists. It accesses no OrbitTrace target information, no event from the excluded 20°–55° interval, no P2 scientific endpoint, and no future literature/external result.

P3 is a dormant successor. It may execute only after the active P2 chain becomes objectively non-promotable under an already-frozen gate:

1. exact P2 scientific development `FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO`; or
2. exact P2 development PASS followed by frozen matched-literature `NO_LITERATURE_SUPERIORITY` / input-ineligibility; or
3. exact P2 development + literature superiority followed by frozen external/generalization failure or power-inconclusive outcome.

Technical/integrity failure never activates P3; equivalence-preserving repair must resolve first. If P2 satisfies all promotion gates, P3 remains dormant. The activation rule is fixed now so P3 cannot be selected from a favorable P2 endpoint.

## Motivation fixed from already-allowed target-excluded evidence

Promoted v8 has a stable 226-family recurrent core/rank and strong top-ranked precision, but incomplete memberships limit macro F1. P1 demonstrated that membership expansion contains substantial real signal: macro F1 increased from 0.1736657194465356 to 0.351168136248689 and top-100 dominant precision increased from 0.6884631112636006 to 0.7047748177418498. However P1 assigned 111,502 non-seed events and lost three qualified matches and two recovery@100 showers, so unconstrained one-view expansion was not promotable.

P2 was frozen independently before its result and uses a substantially different membership view: cross-year predictive observation-space OAS distance plus exact D_SH, one global self-supervised discriminator, and joint family/background responsibility.

P3 is deliberately simple: it accepts only membership additions on which the already-frozen P1 and P2 architectures independently agree on the same immutable v8 family. It introduces no new score, fitted parameter, threshold, window, orbit formula, covariance model, background model, responsibility rule, or rank.

## Immutable scientific inputs

Exact promoted-v8 identity remains:

- 226 recurrent families;
- immutable original seed-event unions;
- immutable promoted-v8 multiplicity order;
- qualified matches 95;
- recovery@100 58;
- MRR 0.045531138942766655;
- top-100 dominant precision 0.6884631112636006;
- macro F1 0.1736657194465356.

Exact P1 scientific source identity remains SHA-256 `e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508` with seed-only OAS covariance, 99% candidate ellipsoid, 99%–99.99% shell background, one-sided 95% Garwood background, joint responsibility >0.5, immutable seeds, no recursive growth, and no refit.

The authoritative P1 target-excluded development pretruth membership is fixed at SHA-256 `ba0269bab1e3db76bd981364225a815d719d8154348c5c39d124ece0f400f73a` from run `31288682378`. Its scientific no-go does not invalidate the pretruth membership architecture as an input to a separately preregistered successor.

Exact canonical P2 scientific source identity remains SHA-256 `f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb`, including:

- cross-year source-seed OAS Mahalanobis observation distance;
- minimum exact Southworth–Hawkins D_SH to immutable opposite-year seeds;
- ±5° target-year local nonseed background;
- at least 128 negatives per family-direction;
- equal 0.5 positive / 0.5 negative total weight per direction;
- StandardScaler + L2 LogisticRegression, C=1.0, lbfgs, max_iter=1000, tol=1e-10;
- unit background odds weight;
- strict maximum family responsibility >0.5;
- immutable v8 seeds/rank and no recursive growth.

If canonical P2 requires an equivalence-preserving technical transport repair, P3 accepts only the sole authoritative repaired lineage designated before its P2 scientific result. Duplicate/equivalence-only P2 outputs may never be chosen by outcome.

## P3 membership rule

P3 has exactly one operation.

For each immutable v8 family `f`:

1. Let `S_f` be the exact original promoted-v8 seed IDs.
2. Let `A1_f` be the non-seed IDs in the exact frozen P1 final assignment to family `f`.
3. Let `A2_f` be the non-seed IDs in the exact frozen P2 final assignment to family `f`.
4. Define the P3 additions as `A3_f = A1_f ∩ A2_f`.
5. Define the P3 membership as `M3_f = S_f ∪ A3_f`.

An event assigned by only one parent architecture is not added. An event assigned by P1 and P2 to different families is not added anywhere. Original seeds never move. No family is created, deleted, merged, split, re-ranked, or re-centered.

The intersection is on exact stable event IDs and exact family IDs only. No probability, posterior, responsibility, D_SH value, Mahalanobis value, distance, rank, label, or target coordinate is used by the consensus operator.

No union, fallback, confidence override, family-specific exception, threshold relaxation, or selected subset is permitted after execution.

## Pretruth ordering

For target-excluded development execution:

1. verify exact authoritative P1 pretruth membership identity;
2. verify exact authoritative P2 source/run lineage and extract only its already-frozen pretruth membership payload;
3. verify both payloads use the exact same 226 v8 family IDs and exact original seed unions;
4. compute exact same-family ID intersections;
5. serialize the complete P3 memberships and SHA-256 freeze them;
6. only then evaluate against the already-allowed target-excluded known-shower truth using the exact promoted-v8 evaluator.

The P3 combiner itself may not read known-shower labels, comparator assignments, OrbitTrace target IDs, target coordinates, target rank, or events from 20°–55°.

## Evaluation

Use the exact promoted-v8 multiplicity order and exact promoted-v8 `evaluate_order` implementation for both v8 baseline and P3 memberships. No matching, qualification, tie, rank, F1, or dominant-label rule may change.

Preserve the exact P2 large-shower subset definition: frozen-v8-qualified known showers with at least 100 target-excluded labelled events in GMN 2022/2023. P3 may not redefine that subset.

## One-shot development gates

Every integrity gate must pass:

- exact 226-family v8 universe and rank reproduced;
- exact v8 baseline metrics reproduced;
- exact P1 pretruth membership SHA reproduced;
- exact authoritative P2 pretruth payload lineage verified;
- P1 and P2 original seed unions each exactly equal v8 seeds;
- P3 additions are exactly the same-family set intersection and nothing else;
- all original seeds remain immutable;
- no non-seed belongs to more than one P3 family;
- P3 memberships hash-frozen before truth evaluation;
- no parameter/feature/model/threshold/variant search;
- no target-region or OrbitTrace target information access.

Every scientific gate must pass simultaneously, using the same material standard already frozen for P2:

- expansion is non-vacuous;
- qualified known-shower matches >= 95;
- recovery@100 >= 58;
- top-100 dominant-label precision >= 0.65;
- macro F1 >= 0.2536657194465356 (exact v8 + 0.08);
- exact frozen large-shower mean recall >= 1.5× exact v8 large-shower mean recall;
- exact frozen large-shower mean precision >= 0.85.

A pass is `PASS_DUAL_MEMBERSHIP_CONSENSUS_P3_DEVELOPMENT`.

A scientific failure is `FAIL_DUAL_MEMBERSHIP_CONSENSUS_P3_NO_GO` and permanently rejects this exact consensus architecture. No parent threshold or consensus rule may be changed from that result.

## Literature transfer

A P3 development pass is not a literature-superiority claim.

Matched SonotaCo comparison must use the exact already-frozen pairwise HDBSCAN and Sugar universes and the same broad/sparse superiority bars used for v6/P1/P2. On each panel, rerun exact panel-specific promoted-v8 cores, exact frozen P1 architecture, and exact frozen P2 architecture from those same immutable cores, freeze both parent memberships before truth/comparator access, then intersect exact same-family assignments. GMN P1/P2 fitted models or memberships are never transported.

P3 receives no comparator label, known-shower label, native shower/background designation, or target information before both parent memberships and the P3 intersection are frozen.

## External/generalization transfer

If P3 passes development and literature superiority, it requires a separately frozen no-retuning cross-survey validation on an event-value-unexposed panel before any final target access. A panel already consumed by P2 cannot be silently reused as pristine P3 validation unless the P3 protocol explicitly treats it as previously exposed rather than independent.

## Claim boundary and firewall

P3 is a conservative consensus membership architecture, not a new core detector. Any superiority claim must be phrased as superiority of the complete target-free v8-core + consensus-membership pipeline under the frozen matched benchmark.

The solar-longitude 20°–55° interval remains inaccessible throughout development, literature comparison, and external method selection. No OrbitTrace coordinate, member, identity, prior rank, target-containing result, or withheld exact target ID may influence P3.

Only a method that passes frozen development, matched-literature superiority, and no-retuning external/generalization gates may advance to the separately frozen final blind exact-ID reveal firewall.