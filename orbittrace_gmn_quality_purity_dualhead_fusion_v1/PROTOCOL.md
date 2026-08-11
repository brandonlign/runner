# OrbitTrace GMN quality-purity dual-head fusion v1

## Scientific motivation

The active #839 regression target is family F1 on the **seed membership**. This is appropriate for ordinary components but systematically penalizes exact-4+4 P20 seeds for low recall even when their seed membership is pure. The current downstream method later performs fixed conformal membership expansion, so seed purity is potentially complementary evidence rather than a replacement target.

A prior strict-group classifier (#840) already learned the exact #839 `positive` predicate (dominant precision >= 0.5 and overlap >= 4) on the same frozen 4,504-family target-excluded GMN universe. As a standalone catalogue it failed badly through excessive concentration: recovery@100=16 despite top100 precision=0.98. It is therefore not revived as a detector. This experiment asks only whether its purity probability is complementary to the successful #839 F1-quality signal after applying the exact #839 geometric diversity rule.

## Frozen inputs

- GMN 2022/2023 behind the exact 20°–55° target firewall;
- exact hard/P19/P20 union: 226 + 1,075 + 3,203 = 4,504;
- exact #839 quality-regression source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
- exact #840 source blob `976ae788ec76a2da7035735ea62118c7289adc5e`;
- exact #839 model: ExtraTreesRegressor, 600 trees, depth 4, leaf 5, all features, seed 20260809;
- exact #840 selected classifier model: HistGradientBoostingClassifier, learning rate .05, 250 iterations, 31 leaves, L2=1, seed 20260809;
- no #840 event-Jaccard suppression is used, because family deletion/suppression is a separate scientific no-go and would confound the signal test.

## OOF signals

### Quality head

Reproduce #839 exactly:

- target = best family F1 if the #839 positive predicate passes, else 0;
- same-shower strict grouping exactly as #839;
- exact #839 grouped weights;
- exact #839 34-dimensional features;
- exact five deterministic OOF folds.

### Purity head

Reproduce the selected #840 classifier signal exactly except for its rejected output suppression:

- target = exact #839 positive predicate as binary 0/1;
- strict grouping exactly as #840, including nonqualified near-misses with their best known shower;
- exact #840 diversity weights;
- exact #840 feature vector and fixed HGB-31 model;
- exact five deterministic OOF folds.

Each family therefore receives two independently valid OOF predictions. No family or same-shower group contributes labels to the model prediction used for that head.

## Geometric diversity and fusion

1. Pass the quality OOF score through the exact #839 diversity rule at the already-selected setting `lambda=0.8`, `scale=1.0`.
2. Pass the purity OOF probability through the **same exact** diversity rule and tie semantics.
3. Fuse the two resulting complete orders using exactly the two parameter-free forms previously frozen in OrbitTrace v10 and reused in v19:
   - rank sum;
   - rank product.
4. No family is deleted. The complete 4,504-family universe is backfilled in every order.

The two fusion forms are the entire candidate set. No weight, classifier, diversity, feature, suppression, cutoff, or model search is authorized.

## Required controls

The quality-only OOF order must reproduce exact #839 best metrics:

- recovery@25 = 22;
- recovery@50 = 40;
- recovery@100 = 75;
- recovery@500 = 159;
- top100 dominant precision = `0.7645689180574315`;
- qualified matches = 256.

Failure to reproduce aborts the experiment.

## Promotion rule

For each fused order compute the exact #839 monotone catalogue metrics. The preregistered comparison key is:

`(recovery@100, recovery@50, recovery@25, top100 dominant precision, MRR)`.

A fused successor passes only if:

1. it satisfies the original #839 viability gates:
   - recovery@100 >= 75;
   - recovery@50 >= hard-v8 recovery@50;
   - top100 precision >= hard-v8 precision - 0.05;
   - qualified matches >= 230;
2. its comparison key is **strictly greater** than the reproduced #839 quality-only key.

The winner between rank-sum and rank-product is selected by the same comparison key. A tie with #839 is not a pass.

## Boundary

This is target-excluded GMN development only. No SonotaCo 2013/2014, Sugar/HDBSCAN matched subset, MAARSY, DMS, OrbitTrace target information, or target-region event may be accessed. P19, P20, and #840 remain standalone scientific no-gos. A PASS would justify only freezing the selected dual-head ranking architecture for a separately executed exposed-SonotaCo development test.