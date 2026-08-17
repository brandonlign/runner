# Pre-result engineering optimization

Workflow run `31995044205` began the exact frozen CV-survival method but was still inside the scientific runner, with no completed result/enforcement/artifact, when a deterministic performance defect was identified: `best_fold_jaccard()` rebuilt the same fold-level event→candidate lookup for every full-data candidate.

This is computational redundancy only. The frozen scientific definition is unchanged.

The optimized execution precomputes/caches, once per immutable fold-candidate list, exactly the same:

- set of event IDs for every recurrent-EOM parent fold candidate;
- event-ID → flat-candidate index map.

For every full candidate and fold it then computes the identical retained member set, identical overlap counts, identical Jaccard denominator `|C_f| + |D| - |C_f ∩ D|`, and identical maximum Jaccard. No candidate, fold, overlap metric, tie rule, score, ranking rule, truth field, threshold, or gate changes.

The original frozen scientific runner remains preserved. `run_development_optimized.py` only memoizes this invariant lookup and delegates every other operation to it. Any scientifically valid endpoint from either implementation must therefore be numerically identical; disagreement is an engineering failure, not a second scientific chance.
