# OrbitTrace GMN P20 transfer-support diagnostic v1

## Purpose

Determine whether the already-frozen target-excluded GMN 2022/2023 development corpus contains enough **high-quality P20 recurrent-isolated-quartet examples** to support a future source-specific transfer architecture. This is a diagnostic only. It does not define, fit, or evaluate a SonotaCo successor.

The motivation is the exposed SonotaCo ranking diagnosis: the global strict-group ranker can catastrophically shrink a rare high-quality P20 family. Before changing the model, we must determine whether the earlier GMN development corpus actually supplied comparable P20-positive support.

## Frozen inputs

Reconstruct exactly the #839/#853 GMN development universe:

- exact target-excluded GMN 2022/2023 development catalogue behind the frozen 20°–55° firewall;
- exact v8 hard families;
- exact P19 prelabel families;
- exact P20 prelabel recurrent-isolated-quartet families;
- exact #839 scientific source `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`.

Expected candidate counts are exactly 226 hard + 1,075 P19 + 3,203 P20 = 4,504.

## Diagnostic quantities

Use the exact #839 family-truth semantics already used to train the active ranker: eligible recurrent labels, one best-F1 label per family, and a positive family only when dominant precision >= 0.5 and overlap >= 4. The training target is the exact positive-family F1, otherwise zero.

For each generator source (`hard`, `p19`, `p20`) record:

- family count;
- number of positive families;
- number of distinct positive recurrent-label groups;
- number of families with training target > 0.5;
- number of distinct recurrent-label groups represented by target > 0.5 families;
- target mean, median, q90, q95, q99, and maximum;
- the deterministic five-fold occupancy of target > 0.5 recurrent-label groups.

For P20 additionally record the same statistics restricted to target > 0 and the SHA-256 of the sorted high-quality family IDs and high-quality recurrent labels. Do not publish label names or use them to define a rule.

`F1 > 0.5` is not a newly selected threshold: it is the already-frozen catalogue recovery criterion used by the literature evaluator.

## Interpretation boundary

This diagnostic may answer whether a future GMN-trained P20-positive transfer model has actual source-domain training support. It may not:

- select a SonotaCo family, rank, quota, threshold, or feature;
- train a SonotaCo successor;
- use Sugar/HDBSCAN matched subsets;
- access SonotaCo 2013/2014;
- access MAARSY, DMS, OrbitTrace target information, or target-region events.

No P20/P21 no-go is reversed. Candidate generation and membership remain unchanged.