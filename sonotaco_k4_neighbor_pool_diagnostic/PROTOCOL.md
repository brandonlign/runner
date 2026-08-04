# SonotaCo 2025 bounded neighbor-pool quartet diagnostic

Status: frozen before any revised detector score is computed.

## Scientific question

The exact PR #38 score chooses an anchor and its three nearest neighbors, then measures the complete-link diameter of that quartet. Does this greedy nearest-three step lose real four-member streams because an accidental nearby sporadic event displaces one genuine member?

## Development boundary

SonotaCo 2025 is now explicitly the method-development survey. SonotaCo 2024 remains unopened and reserved for a separately preregistered one-shot confirmation after a final method is frozen. No SonotaCo 2024 archive, label, event, score, or aggregate may be accessed in this diagnostic.

The GhostStream blind solar-longitude interval 20°–55° is removed by the exact PR #69 adapter before labels, reservoirs, windows, scores, or endpoints. No GhostStream radiant, orbit, member list, score, or local region is used.

## Exact inherited components

The following remain byte-for-byte or numerically unchanged:

- PR #69 SonotaCo parser and native-prefix mapping;
- PR #38 four-dimensional distance and coordinate scales;
- 128-event windows and ±10° neighborhoods;
- globally anchored 10° Mondrian bins;
- 128 calibration negatives and 64 test negatives per supported bin;
- four positive replicates for k in {4,6,8,12};
- conservative rank p-values;
- positive, calibration, and negative seeds;
- complex/parent five-fold assignments;
- alpha levels 0.05 and 0.01;
- all false-positive, AUROC, fold, k=6, and k=8 standards.

## Frozen candidate family

For each anchor, take its m nearest neighbors for m in {3,4,5,6}. Enumerate every choice of three neighbors inside that bounded pool, compute the complete-link diameter of the anchor plus those three events, and retain the minimum diameter over all anchors and combinations.

- m=3 is exactly the original score and must reproduce PR #69 bit-for-bit.
- Larger m values alter only the greedy search approximation. They do not change the distance, quartet size, calibration, p-value, window, or threshold.
- The family stops at m=6. No result-dependent expansion or other score variant is allowed.

## Held-out selection

For each of the five complex/parent folds, select m using only the other four positive folds. A candidate is eligible only if its independently calibrated negative windows satisfy pooled FPR <=0.060/0.020, worst 60° sector FPR <=0.120, and training weak AUROC is no more than 0.01 below the original m=3 score. Among eligible candidates choose lexicographically by training k=4 recall at 0.05, then k=4 recall at 0.01, then weak AUROC, then the smaller m.

The diagnostic continues only if:

- the same m is selected in at least four of five held-out folds;
- cross-fitted k=4 recall reaches at least 0.15 at alpha 0.05 and 0.05 at alpha 0.01;
- the consensus m retains all FPR limits;
- consensus weak AUROC is no more than 0.01 below original;
- consensus k=6 and k=8 recall at alpha 0.05 are each no more than 0.02 below original;
- m=3 exactly reproduces the frozen PR #69 recall and FPR.

## Failure anatomy

For every k=4 positive window preserve the true quartet diameter, componentwise spread, reported uncertainty summaries, selected-quartet true-member count for every m, and the oracle p-value of the actual four injected members. These records are diagnostic only and cannot be used to add an unregistered candidate after this run.

A complete pass authorizes only a separately frozen full revised SonotaCo-2025 development benchmark. It does not authorize SonotaCo 2024, a catalogue scan, or GhostStream application.

Frozen diagnostic source SHA-256: `bdb136bf2c81b4a7b7c5f356800296c662102d34be151282af1848bdac5b97b2`.
