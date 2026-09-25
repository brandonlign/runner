# OrbitTrace P13 dual-output immutable-core / cross-year-halo contingency

Status: **ineligible unless exact P12 is a genuine scientific development no-go.** This reservation was frozen while P12 workflow `31302353678` was still running and before any P12 scientific result was inspected. The complete architecture was preregistered in PR #669 comment `5230471622`.

No comparator outcome, external scientific value, target-region event, OrbitTrace target information, or P12 endpoint may change this architecture.

## Scientific motivation

The current single-output family object serves two different roles: the promoted v8 seed/core events generate and rank a blind recurrent family, while later membership architectures add a characterization halo. Writing halo events back into the same `event_ids` field used for family-identity precision means a contaminated halo can erase a correctly detected/ranked core family. P13 separates those tasks without changing any proposal, assignment, threshold, or rank.

P13 is not allowed to relabel a failed P12 as successful merely because v8 cores are preserved. Halo membership retains independent quality gates; if the exact P12 halo fails macro-F1 or large-shower recall/precision, P13 fails too.

## Exact architecture if eligible

1. Reuse exact P12 scientific computation byte-for-byte through complete pretruth membership freeze. No proposal, classifier, drift model, density veto, responsibility, assignment, family, seed or rank changes.
2. Emit `core_event_ids` per family as the exact promoted-v8 family `event_ids`, byte/identity unchanged.
3. Emit `halo_event_ids` per family as the exact P12 final expanded membership (`core ∪ assigned_nonseed`), unchanged.
4. Freeze/hash all core and halo IDs before any known-shower label value is indexed. The halo hash must equal the inherited exact P12 membership hash.
5. Primary **discovery/identity** endpoints use cores only because those are the objects that generated the target-free catalogue and rank: qualified known-shower matches, recovery@100/@500, MRR, and top-100 dominant precision. They must reproduce exact v8 values: qualified 95; recovery@100 58; recovery@500 95; MRR `0.045531138942766655`; top100 precision `0.6884631112636006`.
6. **Membership-characterization** endpoints use halos only: macro membership F1 and the frozen large-shower recall/precision/F1. Required halo gates remain macro-F1 >= v8+0.08, large-shower recall >=1.5x v8, large-shower precision >=0.85.
7. Report halo single-layer qualified/recovery/top100 precision transparently as secondary diagnostics, but they do not redefine the primary core discovery object.
8. Do not collapse core and halo into one score. Claims must explicitly say cores discover/rank families and halos characterize additional members.
9. No new membership threshold, pruning, confidence cutoff, family exception, rescue, ranking feature, model, parameter search or numeric constant is introduced.
10. All P12 non-scientific integrity/nonvacuity/firewall gates must pass. P13 can only replace the six single-output P12 scientific gates with its prespecified core-discovery and halo-membership endpoint split.

## No-recompute adjudication

Because P13 changes no detector output, **it must not rerun the meteor catalogue or re-query known-shower truth after P12**. The preregistered `finalize_from_p12.py` is the authoritative P13 development adjudicator if P13 becomes eligible:
- input 1 is the immutable authoritative P12 result JSON from a genuine `FAIL_DRIFT_CONDITIONED_TWO_VIEW_MEMBERSHIP_P12_NO_GO` artifact;
- input 2 is the exact target-excluded 226-family structural core artifact already used throughout the lineage;
- it requires every P12 non-scientific integrity/nonvacuity/firewall gate to be true;
- it hashes exact core family/event identities independently;
- it takes halo membership only from P12's already-frozen `membership_pretruth_sha256` and P12 halo metrics;
- it performs **no catalogue fetch, no hidden-label read, no model fit, no proposal/assignment computation and no new truth query**;
- its PASS/FAIL is the deterministic conjunction of exact-v8 core discovery identity and the three frozen halo membership-quality gates.

Any future P13 workflow may only wrap that no-recompute finalizer and pin the exact P12 artifact/digest. A workflow that reruns P12/P13 science is ineligible even if it gives the same result.

## Comparator claim boundary

If P13 becomes promoted, matched Sugar/HDBSCAN comparison semantics must be frozen before any comparator outcome is opened. Primary sparse/broad discovery superiority uses P13 **cores** against comparator catalogue clusters under a matched discovery evaluator. Halo membership is a separate secondary characterization endpoint and cannot be mixed into primary superiority or used to inflate rank/identity.

The companion `MATCHED_BENCHMARK_PROTOCOL.md`, frozen before P12 truth, fixes the pairwise no-denominator-mixing rule, exact blind-safe comparator assignment identities/counts, inherited broad/sparse superiority bars, and the prohibition on choosing core versus halo after truth.

Mandatory downstream hierarchy remains: sparse-stream superiority separately against both Sugar and catalogue HDBSCAN in both SonotaCo 2023 and 2025; then no-retuning external validation; only then final target-containing blind search and sealed exact-ID reveal.

Solar longitude 20°–55° remains inaccessible throughout P13 development and all pre-comparator work.