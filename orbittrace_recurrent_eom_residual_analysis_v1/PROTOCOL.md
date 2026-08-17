# Recurrent-EOM residual-error analysis v1 — frozen protocol

## Scientific role

This is a diagnostic on the already-exposed SonotaCo 2013/2014 development benchmark. It does not modify recurrent-EOM, select parameters, access the protected `[20°,55°]` region, or constitute external validation.

The sole purpose is to determine which mechanism dominates the remaining recurrent-EOM errors before any successor is defined.

## Immutable parent

Parent method: exact recurrent-EOM HDBSCAN v1 from `agent/orbittrace-recurrent-eom-sonotaco-v31-benchmark-v1`, frozen head `0248177a2b4dc1f7a0969931d835097d3e86c06f`.

Parent pretruth artifact: workflow run `31829200215`, artifact `9230008341`.

Expected parent pretruth SHA-256 is read and verified from that immutable artifact. No candidate membership or rank may be regenerated after truth is opened.

Truth source is the already-exposed matched SonotaCo literature artifact from run `31405109267`, artifact `9069505548`. It is development truth only.

Panels and fixed evaluation budgets are inherited unchanged from the parent benchmark:

- Sugar 2013: 34
- Sugar 2014: 46
- HDBSCAN 2013: 11
- HDBSCAN 2014: 9

Eligible truth showers use the parent evaluator rule: at least four truth members and label not equal to `SPORADIC`.

## Per-shower measurements

For every eligible shower and every recurrent-EOM candidate, compute overlap, precision, recall, and F1 against the truth set. Candidate rank and membership are immutable parent outputs.

For each truth shower define:

- `best_budget_f1`: maximum F1 among candidates within the inherited panel budget;
- `best_all_f1`: maximum F1 among all recurrent-EOM candidates;
- `best_all_recall`: maximum recall among all candidates; ties are broken by higher precision, then lower parent rank, then family ID;
- `best_all_precision_at_recall`: precision of the candidate selected by that recall ordering.

The existing recovery convention is strict `F1 > 0.5`.

## Frozen mutually exclusive residual taxonomy

Each eligible truth shower is assigned exactly one category, in this order:

1. `RECOVERED` — `best_budget_f1 > 0.5`.
2. `RANKING_SELECTION_FAILURE` — not recovered, but `best_all_f1 > 0.5`. A recoverable recurrent-EOM family exists but lies below the fixed evaluation budget.
3. `MEMBERSHIP_CONTAMINATION` — neither above condition holds, but `best_all_recall > 0.5` and `best_all_precision_at_recall <= 0.5`. Recurrent-EOM contains a family capturing a majority of the shower, but background membership prevents recovery.
4. `CANDIDATE_GENERATION_FAILURE` — all remaining misses. No recurrent-EOM family both captures a majority of the shower and satisfies the recovery threshold.

No category threshold may be changed after the result is seen.

## Primary diagnostic outputs

For each panel report:

- eligible shower count;
- recovered count;
- counts and fractions of the three residual failure classes;
- median and interquartile range of best-budget F1 and best-all F1;
- for `MEMBERSHIP_CONTAMINATION`, median majority-capture candidate precision, recall, member count, and excess-background count;
- for `RANKING_SELECTION_FAILURE`, median first recoverable rank and its distance below the inherited budget.

Across all four panels report micro-summed category counts. Because the Sugar and HDBSCAN row universes overlap, this pooled total is a panel-level diagnostic, not a count of unique physical showers.

## Successor authorization gate

A single PhysCore-cleanup successor is scientifically motivated only if `MEMBERSHIP_CONTAMINATION` is nonzero in at least two of the four panels and accounts for at least 15% of all residual misses across the four panels.

If the gate fails, no recurrent-EOM+PhysCore successor is authorized from this diagnostic.

If the gate passes, one successor may be frozen using the already-fixed PhysCore v1 rule only:

- solar half-width 5 degrees;
- radiant half-width 4 degrees;
- speed scale 10%;
- radius 1 in the normalized physical embedding;
- maximal 3-core / support including self = 4;
- parent fallback if the refined core has fewer than 4 members;
- no candidate addition, splitting, rank change, parameter search, or post-result rescue.

The successor must preserve recurrent-EOM candidate selection and ranking exactly and alter membership only.

## Firewall

Protected `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY, DMS, and any pristine external endpoint remain inaccessible. SonotaCo is exposed development only.
