# OrbitTrace recurrent-EOM direct-GMN literature fairness audit v1

## Status

Post-result fairness adjudication frozen before the matched-capacity calculation. This audit does not create, retune, rerun, or modify any scientific clustering method. It reuses only immutable outputs from binding direct-GMN literature run `32152924956` and the exact recurrent-EOM artifacts that run already consumed.

The original direct comparison is preserved unchanged. Its large full-catalogue margins are not treated as a valid capacity-matched superiority claim because recurrent-EOM exposes ~2,097 ordered candidate families whereas the literature catalogues expose much smaller unordered candidate sets.

## Question

At the exact candidate capacity supplied by each frozen literature comparator, does the already-frozen recurrent-EOM ordering still outperform that comparator under the same annual one-to-one Hungarian shower-F1 evaluator?

## Frozen rule

For comparator `m` and year `y`:

1. Let `K(m,y)` be the complete candidate count in the already-sealed literature catalogue from direct benchmark run `32152924956`.
2. Keep the comparator catalogue completely unchanged. It remains unordered and all of its `K(m,y)` candidates are evaluated.
3. Truncate the immutable recurrent-EOM catalogue to its first exactly `K(m,y)` candidates. No family membership or order is changed.
4. Evaluate both catalogues against the same annual eligible-shower truth using the exact direct-benchmark one-to-one Hungarian F1 semantics.
5. A pairwise matched-capacity win requires recurrent-EOM macro-F1 to be strictly greater and recurrent-EOM recovered showers with assigned F1 > 0.5 to be at least the comparator count.

The four primary panels are Sugar-core 2022/2023 and catalogue-HDBSCAN 2022/2023. Report full-catalogue values only as historical diagnostics.

## Interpretation boundary

- This fixes the candidate-capacity asymmetry only. It does **not** upgrade the GMN Sugar implementation into the full uncertainty-resampled Sugar pipeline; the GMN Sugar result remains explicitly `deterministic published core only`.
- The catalogue-HDBSCAN comparison retains the already-frozen published-configuration transfer and its structural eligibility.
- MRR is not defined head-to-head because the literature outputs are unordered catalogues. Recurrent-EOM's internal zero-filled MRR remains a separate retrieval diagnostic.
- A 4/4 matched-capacity PASS would support direct GMN superiority to these tested comparator implementations at equal catalogue capacity. It would not prove universal literature superiority or pristine cross-survey generalization.
- The pristine NASA ASFN 2018/2019 negative result remains binding and may not be used to tune or rescue recurrent-EOM.

## Scientific firewall

No method-shopping, parameter search, threshold search, reranking, membership change, comparator retuning, budget search, or post-result rescue is authorized. The candidate budget is mechanically determined by each comparator's already-frozen complete catalogue count.

The protected GMN solar-longitude interval `[20°,55°]` remains excluded exactly as in the parent direct benchmark. OrbitTrace target information/events, AMOS, MAARSY, DMS, ASFN/EFN event-level data, and new SonotaCo scientific data are inaccessible to this audit.

The first technically valid execution of this exact audit is binding. Technical repairs are allowed only if this protocol, sealed inputs, candidate orders/memberships, evaluator semantics, and four matched-capacity gates remain unchanged.
