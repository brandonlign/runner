# OrbitTrace development and final-candidate policy — v1

## Purpose

Make method development aggressive without consuming the permanent test panel. The objective remains a target-free meteor-stream discovery method that can beat the strongest relevant literature methods, generalize without retuning, and only then enter the blind OrbitTrace search.

## Development evidence

The only method-selection corpus is target-excluded GMN 2022/2023.

A successor may be designed after a scientific failure, but it must attack a diagnosed mechanism rather than merely alter a nearby threshold. Previously exposed literature-test results may motivate broad architectural questions, but their numerical outcomes cannot choose a new parameter, threshold, feature weight, rank cutoff, or membership boundary.

Because GMN 2022/2023 is the permanent development corpus, architecture search, feature selection, parameter fitting, ablations, diagnostics, and model selection may deliberately use its labels after the target interval has been removed. The scientific protection comes from the sealed SonotaCo 2013/2014 final test, not from pretending that each GMN development experiment is a new pristine holdout.

## Internal development standard

A candidate considered for eventual final-test promotion must demonstrate all of the following on GMN 2022/2023 before the permanent SonotaCo test is opened:

1. **Sparse-stream gain:** material improvement in weak/sparse known-shower recovery, including the 4–9-member regime, not only aggregate F1.
2. **Overall non-regression:** no material loss in qualified-family count, ranking recovery, and dominant-family precision relative to the strongest surviving development baseline.
3. **Year robustness:** the claimed gain must appear independently in both development years rather than being driven by one year.
4. **Stress robustness:** the gain must survive fixed internal perturbations/ablations appropriate to the architecture, such as leave-window-out, support thinning, bootstrap/resampling, or deterministic subpanel checks, without changing the scientific rule after seeing those stress outcomes.
5. **Mechanistic plausibility:** the architecture must have a clear reason to improve the failure mode it targets. Tiny post-failure threshold edits do not qualify as a new architecture.
6. **Target independence:** no OrbitTrace target information or target-region result may enter development.

Development gates can be stricter for a particular successor when frozen before execution. They may not be weakened after a result is observed.

## Development metric semantics

Future architecture selection must separate **discovery/ranking quality** from **membership quality**.

### Monotone discovery recovery

For a fixed rank cutoff `K`, a known shower is `recovered@K` if **at least one** candidate among ranks `1..K` satisfies the frozen qualification rule for that shower. Adding a new candidate below rank `K` cannot make a previously recovered shower unrecovered.

A development evaluator must not choose the globally highest-F1 family first and then use that family's rank as the recovery rank. That historical evaluator is non-monotone: a better-membership family at a worse rank can make an unchanged top-K detection disappear numerically.

The exact frozen P19 verdict is not retroactively changed by this clarification. P19 remains a permanent no-go under its preregistered evaluator/gates. Its result is diagnostic evidence for future architectures only.

### Membership/catalogue quality

Membership precision, recall, F1, size-stratum F1, and catalogue-quality summaries are evaluated separately from monotone `recovered@K`. A candidate may improve membership without improving rank, and vice versa; both dimensions must be reported.

For development comparisons involving many candidate families per truth shower, the evaluator must additionally report duplicate/split burden. Before final-candidate declaration, the intended one-primary-catalogue matching/evaluation semantics must be frozen so that duplicate candidates cannot inflate catalogue performance.

### Ranking diagnostics

Every architecture that adds or changes families must report at minimum:

- monotone recovery@25, @50, @100, and @500;
- qualified known-shower count;
- rank distribution / MRR under the monotone qualified-candidate definition;
- top-100 dominant precision;
- catalogue/membership macro F1 and annual size-bin F1;
- candidate count and duplicate/split diagnostics.

No single one of these metrics is sufficient for final promotion.

## Architecture triage

Scientific failures are used to kill architectures quickly.

- P18 is a permanent matched-literature no-go.
- B1 is a permanent development no-go.
- P19 is a permanent development no-go under its exact frozen triplet/radius/reciprocity/membership/ranking/evaluator contract.
- No P18, B1, or exact-P19 threshold/feature/model rescue is allowed from their observed results.
- P19 nevertheless established a useful broad mechanism: sub-component cross-year recurrence can recover substantial sparse structure. A future architecture may use that qualitative mechanism only as part of a materially different formulation with independently developed GMN parameters and unified ranking/deduplication.
- P20 is a separately preregistered isolated-quartet contingency and may receive its exact frozen development test. A P20 result does not constrain development of a more general architecture on the same GMN corpus.

A successor after P19 should be materially different. Repeated nearby variants of the rejected exact P19 mechanism should not be treated as independent progress.

## Preferred post-P19 architecture direction

The current evidence identifies three separable bottlenecks that a serious final-candidate architecture should address jointly rather than through append-only patches:

1. **Family existence for weak streams:** recurrent sub-component/microcore evidence must be able to create candidates below the old two-quartet component floor.
2. **Unified ranking and duplicate control:** hard and soft candidates must compete in one label-free ranking or suppression framework; appending every soft family behind an immutable hard prefix is not sufficient.
3. **Full reported membership:** the method needs a deterministic label-free membership rule capable of representing ordinary and large showers, rather than benchmarking only tiny recurrent cores. The strong historical P12 drift-conditioned membership result is development evidence that this is achievable, but exact P12 remains a historical no-go as a universal single-output rule.

Development should therefore prefer a unified recurrent-catalogue architecture over a long chain of one-off rescue variants.

## Final-candidate declaration

Passing one development experiment does not automatically consume the permanent SonotaCo test.

The permanent SonotaCo 2013/2014 test is opened only when the project explicitly declares a candidate **FINAL_FOR_LITERATURE_TEST**. Before that declaration:

- scientific source is frozen;
- all method parameters are frozen;
- complete candidate-generation, family-construction, membership, ranking, deduplication, and output semantics are frozen;
- exactly one primary output member set per reported family is frozen;
- Sugar and catalogue-HDBSCAN interfaces are frozen;
- pairwise matched-universe construction is frozen;
- superiority and integrity gates are frozen;
- the target firewall is source-audited;
- no SonotaCo 2013/2014 scientific value has been inspected.

This declaration is intentionally expensive. It should occur only after the method is strong enough on GMN that we are willing to accept the one-shot test result without retuning.

## Test consequence

The SonotaCo 2013/2014 result is final evidence for the declared candidate. If it fails, that exact candidate does not have a literature-superiority claim. The result may not be used to retune the same candidate and then claim a fresh pass on the same panel.

The permanent split is designed to delay this event until development is mature, not to create an endless supply of test panels.

## External consequence

Only a literature-test pass can activate MAARSY 2020/2021. MAARSY remains no-retuning validation, not development data.

Only satisfaction of the external-generalization requirement can activate the final blind OrbitTrace search.
