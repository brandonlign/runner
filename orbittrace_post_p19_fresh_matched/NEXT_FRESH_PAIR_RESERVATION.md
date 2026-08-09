# OrbitTrace next fresh SonotaCo matched-pair reservation

This file reserves a **selection rule**, not a hand-picked year pair. It is committed before any new SonotaCo archive or event value is accessed and before the P19 development outcome is used to choose a benchmark panel.

## Candidate universe

The candidate years are the fixed inclusive range **2007–2022**. Years 2023–2025 are excluded a priori because they belong to already-used/recent SonotaCo lineages. No year outside 2007–2022 may be substituted under this reservation.

## Deterministic freshness rule

A later metadata-only audit will scan repository Git history, branch/PR-head history, and GitHub issue/PR/comment/review metadata strictly **before this reservation PR was created**. For each candidate year `Y`, it will look for SonotaCo-specific year tokens including, case-insensitively:

- `SonotaCo Y` / `SonotaCo-Y` / `SonotaCo_Y`;
- `sonotacoY` / `sonotaco-Y` / `sonotaco_Y`;
- annual archive token `0YYa.zip` and annual member-directory token `0YYa/`;
- annual member `_U2_Y0101_S.csv`;
- `SNMv3/0YY`.

A year is eligible only if **zero** pre-reservation hits are found on every audited surface. This intentionally treats even prior source-only/parser/audit discussion as contamination. It is stricter than an actual-data-access test and therefore cannot rehabilitate a previously discussed year by interpretation.

If at least two years are eligible, the reserved pair is the **two numerically most recent eligible years**. If fewer than two are eligible, the reservation fails closed and authorizes no scientific archive access. There is no manual replacement, tie-break, or outcome-dependent substitution.

The selected pair, exposure counts, searched surfaces, reservation PR number/time, and hashes of the metadata manifests must be serialized before any selected archive is opened.

## Archive-availability boundary

This reservation does not assume that a selected archive is available or schema-compatible. After the pair is selected and frozen, source-only parser/comparator/P19 transport must be preregistered for exactly those years. If an archive or frozen annual member is unavailable or incompatible, that is an integrity/transport failure for this reservation; another year is not silently substituted.

## Scientific boundary

The pair may be scientifically opened only after all of the following are true:

1. the zero-mention audit passes and freezes exactly two years;
2. the current successor has passed its own target-excluded development gate;
3. the exact successor transport and the already-frozen catalogue-HDBSCAN and Sugar comparator transports are source-audited before first archive access;
4. the pairwise literature-superiority gates and denominator rules are frozen unchanged;
5. the no-retuning external/generalization route is preregistered.

The reserved pair must never be used to tune a failed successor or choose a new successor architecture.

## Firewall

This reservation and its future exposure audit may inspect repository/GitHub metadata only. They may not download or open any SonotaCo meteor archive, event row, shower label, comparator cluster value, external validation dataset, OrbitTrace target information, target-region event, or target-containing result. The 20°–55° target region remains inaccessible.
