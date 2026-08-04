# Consensus-lowpass recurrence: frozen no-score source audit

Status: frozen before any candidate score, null catalogue, injection, threshold, recovery endpoint, or continuation decision is computed.

## Motivation from the preserved real-data no-go

PR #95 showed that the majority-conditioned recurrence method passed simulation but was structurally incompatible with the dominant real established-shower population:

- 353 of 400 labeled showers were active in four through seven GMN years at k=4;
- only 11 showers were active in exactly three years;
- annual quality-sporadic exposure grew from 32,760 in 2019 to 621,819 in 2025.

The failed method subtracted the complete pointwise annual median. That operation removes a real narrow shower whenever it is present in a majority of years. Its active-year definition and gates remain killed and are not changed here.

The new candidate separates **spatial scale** from **temporal prevalence**. It treats only the smooth spatial projection of cross-year consensus as nuisance, rather than treating all majority-persistent evidence as nuisance.

## Frozen candidate

Starting from the exact majority-conditioned source SHA-256 `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`, for each unchanged template width:

1. compute the unchanged annual one-sided Poisson evidence maps;
2. compute the pointwise median annual evidence across all fifteen years;
3. apply the already inherited null-model smoothing scale `(1.6, 1.6, 1.0, 0.9)` to that median map only;
4. subtract the smooth consensus map from every annual evidence map and truncate below zero;
5. take the unchanged third-strongest adjusted annual evidence;
6. maximize over the unchanged four template widths.

The smoothing scale is not tuned in this branch. It is copied exactly from the pre-existing pooled annual null fit. No alternate width, quantile, coefficient, rank, or recurrence order is screened.

A smooth observing/reduction structure shared across years should be removed. A spatially narrow shower may be present in most years and enter the median, but only its low-pass component is subtracted, leaving a localized residual.

## Frozen persistent-signal stress condition

The source retains the original five-of-fifteen recurrent injection and adds one predeclared real-data-motivated condition:

- a recurrent stream active in exactly twelve of fifteen years;
- injected into the unchanged shared-structure null family;
- the same per-active-year strengths `4, 6, 8, 12`;
- the same jitter, location selection, histogram grid, templates, and complete-search evaluation.

Twelve of fifteen is fixed before scoring as a majority-persistent stress regime. No active-year count is selected after results.

## Fixed comparators

- pooled virtual year;
- pooled plus annual confirmation;
- original hard third-year recurrence;
- worst-family soft recurrence;
- complete-median majority conditioning.

## Allowed source-audit operations

- reconstruct the exact worst-family source and exact majority-conditioned derivation from pinned commit `b8748f3e641e52dfe3b1500d6c7356bd9732f54a`;
- hash-verify the exact majority-conditioned source;
- apply the committed deterministic consensus-lowpass derivation;
- compile and statically inspect the derived source;
- record its exact SHA-256, bytes, lines, constants, functions, method keys, injection conditions, gates, and exact source.

## Forbidden operations

This branch may not install scientific dependencies, download the observed subset, import or execute the candidate, generate any histogram, sample either null family, inject a stream, compute a score, threshold, FWER, recovery value, or comparator endpoint.

A successful source audit authorizes only a separately frozen reduced kill screen with a new seed and prospectively declared trial counts and gates. It does not authorize real-shower testing, confirmation, catalogue scanning, or GhostStream application.