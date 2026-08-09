# C1-LF matched Sugar/HDBSCAN protocol

## Status and activation

This protocol is frozen before any C1-LF scientific development result and before any C1-LF matched-literature result. It is dormant unless the exact frozen C1-LF successor first becomes legitimately active and returns `PASS_V6_LF_CORE_PROBABILISTIC_MEMBERSHIP_C1_DEVELOPMENT` under the development protocol already frozen on this branch.

C1-LF itself is eligible only after an exact v6-LF development PASS followed by `NO_LITERATURE_SUPERIORITY` under the already-frozen v6-LF matched comparison. Those predecessor results do not authorize changing this protocol, the C1-LF membership model, or any benchmark threshold.

## Comparator panels and exact-row universes

Use the same independently frozen SonotaCo 2023/2025 pairwise comparator universes already fixed for the v6-LF comparison. HDBSCAN and Sugar remain separate pairwise panels and may not share or pool denominators.

The exact event-row denominators are fixed to:

- HDBSCAN 2023: 26,460 rows;
- HDBSCAN 2025: 19,658 rows;
- Sugar 2023: 30,414 rows;
- Sugar 2025: 23,200 rows.

No row may be added, removed, remapped, or selected based on C1-LF performance. The 20°–55° target interval remains excluded exactly as in the existing matched panels.

## Information boundary

C1-LF receives only the exact scientific rows/IDs of each pairwise panel before truth. It must not receive HDBSCAN cluster values, Sugar retained labels, known-shower truth, native shower/background membership, or any OrbitTrace target information before its own complete pretruth payload is frozen.

For each panel independently:

1. reconstruct the exact v6-LF all-event-null scan/calibration semantics on that panel's immutable event-ID universe;
2. build the exact v6-LF primary recurrent family universe and primary rank with the comparator assignments and known-shower truth physically unavailable;
3. apply the exact frozen C1-LF membership engine to **primary families only** using the two panel years jointly, preserving every seed and the exact v6-LF primary order;
4. fixed4 rescue families may remain diagnostic but cannot seed or alter C1-LF membership;
5. freeze SHA-256 commitments to the exact row universe, v6-LF primary families/rank, candidate/shell/model diagnostics, conflict responsibilities, and final C1-LF memberships;
6. only after those hashes are durable may the panel-specific comparator assignments and known-shower truth be exposed for evaluation.

No SonotaCo-specific threshold, covariance rule, shell, responsibility cutoff, ranking rule, event filter, or parameter search is permitted.

## Frozen C1-LF membership architecture

The benchmark must use the exact development-frozen C1-LF architecture without refit or retuning:

- seed-only OAS covariance;
- 99% candidate ellipsoid;
- 99%–99.99% local-background shell;
- one-sided 95% Garwood background bound;
- joint conflict responsibility threshold strictly greater than 0.5;
- immutable original seeds;
- no member may seed recursive growth;
- no family reranking after membership expansion;
- fixed4 rescue cannot seed membership.

## Evaluation

Within each pairwise panel and each year, evaluate C1-LF and the frozen comparator on the exact same event rows and common known-shower truth mapping. Use the same per-shower F1 and size-bin endpoints already frozen for the predecessor v6-LF/P1/P2 comparisons. No cross-panel denominator comparison and no invented comparator ranking are allowed.

The superiority bars are deliberately inherited unchanged rather than chosen for C1-LF:

### Broad catalogue superiority against one comparator

The pairwise broad gate passes only if **all** of the following hold in both 2023 and 2025:

- C1-LF macro F1 >= comparator macro F1 + 0.05;
- no nonempty frozen size bin has mean-F1 regression > 0.05;
- at least two nonempty frozen size bins improve by >= 0.10 absolute mean F1;
- the number of common known showers recovered with F1 > 0.5 is not lower than the comparator.

### Sparse-stream superiority against one comparator

The pairwise sparse gate passes only if **all** of the following hold in both 2023 and 2025:

- mean F1 in the frozen 4–9-member bin >= comparator + 0.10;
- mean F1 over the combined frozen 4–24-member sparse range >= comparator + 0.10;
- macro F1 is no more than 0.10 below the comparator;
- at least 80% of the comparator's F1 > 0.5 shower count is retained.

Empty size bins are excluded only under the already-frozen comparator convention; their emptiness cannot be manufactured by filtering rows or labels.

## Overall classification

`BROAD_CATALOGUE_SUPERIORITY` requires the broad pairwise gate against **both** HDBSCAN and Sugar.

If broad superiority fails, `SPARSE_STREAM_SUPERIORITY` requires the sparse pairwise gate against **both** HDBSCAN and Sugar.

Otherwise the classification is `NO_LITERATURE_SUPERIORITY`.

A mixed HDBSCAN/Sugar outcome cannot be advertised as overall superiority. Panel-specific improvements may be reported descriptively but cannot advance the method.

## Succession after result

- Broad or sparse superiority makes C1-LF eligible for a separately frozen prospective/generalization gate; it does **not** authorize final target-region access by itself.
- `NO_LITERATURE_SUPERIORITY` permanently rejects C1-LF for the project's superiority objective and routes only to an already-preregistered later successor.
- Technical/integrity failure is no scientific result and permits only an equivalence-preserving infrastructure repair.

No target-containing search, final Stage A, Stage B reveal, or use of OrbitTrace coordinates/members/identity is authorized by this protocol.
