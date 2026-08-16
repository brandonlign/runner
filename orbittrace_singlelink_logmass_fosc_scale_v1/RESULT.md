# OrbitTrace scale-free log-mass FOSC pruning diagnostic v1 — result

## 🔴 NEGATIVE

Binding run: `31932663056`

Artifact: `9259769608`

Artifact digest: `sha256:602ac4ab5117026080d9ab86c8ce069c3b274619ae4b986ada1a1d3e6f5e9785`

Result SHA-256: `c6ce4d5d6bf40749428b4904dd051452424fe68cb7435cd360861ce6800cf818`

Exact frozen interpretation:

`REFUTES_LOGMASS_FOSC_CROSS_SCALE_PRUNING`

### Frozen cross-scale metrics

- log-mass FOSC pooled event-weighted mean best Jaccard: `0.09263490361735842`
- recurrent-EOM pooled event-weighted mean best Jaccard: `0.6787610921074515`
- log-mass FOSC median bucket event-weighted mean best Jaccard: `0.04067131916996047`
- recurrent-EOM median bucket event-weighted mean best Jaccard: `0.6919016744475399`
- log-mass FOSC strict bucket wins: `0/4`

Only the non-empty-output clause passed. Every comparative frozen gate failed.

### Structural failure mode

The result separates two questions that had previously been conflated:

1. PR #1274 positively established that the dimensionless single-link branch coordinate `log(d_parent/d_form)` is materially less sample-size-sensitive than raw linkage distance.
2. The present result shows that the exact threshold-free FOSC objective `Q=(m/n)*log(d_parent/d_form)` does **not** turn that coordinate into coherent cross-scale pruning.

The failure is visible structurally. In some frozen subsets the FOSC objective selected a near-root branch containing essentially the entire sample (for example `5856/5857` events at denominator 128 bucket 2 and `5815/5816` at denominator 128 bucket 3; at denominator 1024 bucket 1 it selected `736/739`). In other subsets it emitted hundreds of small branches. Thus the parent-vs-children additive mass-lifetime objective is unstable even though the underlying log-persistence coordinate itself is comparatively scale-normalized.

### Consequence

This exact log-mass FOSC pruning architecture is closed. Do not rescue it by changing:

- mass exponents or transforms;
- lifetime transforms;
- parent/child weights;
- tie rules;
- branch-size thresholds;
- persistence cutoffs;
- subset salts or denominators.

The next scientifically motivated route is **statistical branch significance / confidence pruning** on the support-free hierarchy, not another deterministic additive FOSC score.

No shower truth, protected target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed by this diagnostic.
