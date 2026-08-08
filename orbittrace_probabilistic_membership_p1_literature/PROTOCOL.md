# OrbitTrace P1 — frozen matched Sugar/HDBSCAN literature adjudication

## Status

Protocol-only preregistration. This branch executes no P1 science, opens no SonotaCo archive, accesses no comparator assignment, reads no known-shower truth value, and accesses no OrbitTrace target information or event from the excluded solar-longitude interval 20°–55°.

This protocol is frozen before any scientific P1 development result exists. It may activate only after the exact frozen P1 development implementation returns `PASS_PROBABILISTIC_MEMBERSHIP_P1_DEVELOPMENT` under its already-frozen GMN 2022/2023 gates. A P1 development failure leaves this protocol permanently dormant.

The purpose is to prevent a successful P1 development result from being followed by a post-hoc choice of comparator universe, transfer semantics, endpoint, or superiority threshold.

## Scientific object being compared

P1 is a post-core membership architecture. It does not replace the promoted-v8 target-free recurrent-core detector or multiplicity rank. Therefore, on every matched literature panel, the comparison object is constructed in two immutable stages:

1. run the exact promoted-v8 detector/core/family/ranking architecture, without retuning, on that panel's exact paired-year event universe;
2. apply the exact frozen P1 membership architecture to those panel-specific immutable v8 recurrent cores, leaving the v8 family order unchanged.

The panel-specific family identities are outputs of the exact v8 architecture on that panel. The GMN development family IDs are not transported as targets or templates into SonotaCo.

P1 may change only final family membership. Added members never seed growth, refit a centroid/covariance/background estimate, create a family, change recurrence, or change the exact v8 multiplicity order.

## Frozen P1 architecture under transfer

For each recurrent v8 family produced on a matched panel, apply the same P1 rule frozen before GMN development:

- reconstruct pooled same-year centroids from immutable v8 seed-event unions using the promoted-v8 circular/robust conventions;
- express seeds/events in the inherited four-dimensional v8 observation geometry;
- estimate one pooled seed-only OAS covariance after within-year centering;
- use the 99% four-dimensional chi-square ellipsoid as the stream candidate region;
- use the 99%–99.99% chi-square annulus as the local-background shell;
- estimate conservative local background with the one-sided 95% Garwood Poisson upper mean;
- estimate stream amplitude from immutable current-year seeds plus only positive nonseed excess over the conservative expected inner-region background, divided by 0.99 containment;
- compute all compatible Gaussian family intensities and conservative local background jointly;
- assign a nonseed event only to the maximum-intensity family when normalized posterior responsibility is strictly greater than 0.5;
- never move original seeds;
- never allow an added member to seed/refit/grow another assignment;
- preserve the exact panel-specific promoted-v8 family rank.

No probability, shell, covariance, confidence level, background rule, responsibility cutoff, tie rule, or fallback may change on SonotaCo.

## Matched comparator universes

The literature comparison reuses the exact already-frozen SonotaCo matched-data panels from the v6 literature adjudication. HDBSCAN and Sugar have different exact-row universes and therefore remain separate pairwise experiments.

### HDBSCAN panel

Exact event rows after the already-frozen transport/quality/blind rules:

- SonotaCo 2023: 26,460 rows;
- SonotaCo 2025: 19,658 rows.

The exact HDBSCAN assignment artifacts, archive identities, parser identities, IAU mapping, and event-ID manifest are the same SHA-pinned objects used by the frozen v6 matched-literature harness. They may not be regenerated from a different catalogue revision or filtered differently for P1.

### Sugar panel

Exact event rows after the already-frozen transport/quality/blind rules:

- SonotaCo 2023: 30,414 rows;
- SonotaCo 2025: 23,200 rows.

The exact Sugar uncertainty-transfer assignment artifacts, archive identities, parser identities, IAU mapping, and event-ID manifest are the same SHA-pinned objects used by the frozen v6 matched-literature harness. They may not be regenerated from a different catalogue revision or filtered differently for P1.

### No denominator mixing

Every P1-vs-HDBSCAN result is evaluated only on the HDBSCAN exact-row universe. Every P1-vs-Sugar result is evaluated only on the Sugar exact-row universe. No absolute F1, recovery, support count, or shower count may be compared across the two different denominator universes.

A literature-superiority claim requires the relevant pairwise condition independently against both comparators in both years.

## Blind/pre-truth execution order

For each comparator panel:

1. materialize only the already-frozen exact-row ID/geometry universe and target-excluded calibration/background representation;
2. keep known-shower truth and competitor cluster labels inaccessible;
3. run the exact promoted-v8 target-free detector on the paired 2023/2025 panel;
4. freeze the complete recurrent v8 family universe and exact multiplicity order;
5. apply exact frozen P1 membership without truth/comparator access;
6. serialize and SHA-256 freeze the complete P1 family membership payload and unchanged v8 order;
7. only after those hashes exist, open the frozen known-shower mapping and comparator assignments;
8. evaluate P1 and its paired comparator on exactly the same events/eligible labels.

Comparator assignments may be used only after P1 rankings/memberships are frozen. They may not influence candidate generation, v8 family construction, P1 covariance/background estimation, conflict resolution, membership, rank, or any threshold.

## Evaluation definitions

Use the same frozen known-shower eligibility, dominant-label matching, per-shower precision/recall/F1, macro F1, and size-stratum definitions already used by the matched v6 literature adjudication.

For each comparator and year report at minimum:

- exact event-row count;
- eligible known-shower count;
- P1 recurrent-family count and unchanged v8 rank identity;
- qualified known-shower matches;
- macro F1;
- per-shower F1 distribution;
- mean F1 in size strata 4–9, 10–24, 25–49, 50–99, and 100+ where nonempty;
- number of eligible showers with F1 > 0.5;
- comparator values for the exact same endpoints;
- paired differences P1 minus comparator;
- P1 membership count, number of families gaining members, and conflicted-candidate diagnostic;
- integrity/pre-truth hashes.

Because P1 inherits v8 ranking unchanged, ranking endpoints may be reported diagnostically but cannot be represented as evidence that P1 itself improved core discovery ranking.

## Frozen superiority bars

These bars are intentionally identical to the already-frozen v6 literature claim bars. P1 receives no easier standard.

### `BROAD_CATALOGUE_SUPERIORITY`

P1 establishes broad catalogue superiority only if, independently against HDBSCAN and independently against Sugar, in both 2023 and 2025:

1. P1 macro F1 is at least comparator macro F1 + 0.05;
2. no nonempty size stratum has P1 mean F1 more than 0.05 below the comparator;
3. P1 exceeds the comparator by at least 0.10 mean F1 in at least two nonempty size strata in that year;
4. P1's number of eligible showers with F1 > 0.5 is not lower than the comparator's;
5. every common-universe, source/provenance, target-exclusion, and pre-truth integrity gate passes.

### `SPARSE_STREAM_SUPERIORITY`

If broad superiority is not met, P1 establishes sparse-stream superiority only if, independently against both comparators in both years:

1. mean F1 for 4–9-event showers is at least comparator + 0.10;
2. combined mean F1 over 4–24-event showers is at least comparator + 0.10;
3. P1 macro F1 is no more than 0.10 below that comparator;
4. P1 retains at least 80% of that comparator's count of eligible showers with F1 > 0.5;
5. every common-universe, source/provenance, target-exclusion, and pre-truth integrity gate passes.

### `NO_LITERATURE_SUPERIORITY`

Any result satisfying neither complete condition is classified `NO_LITERATURE_SUPERIORITY`. A strong single-year result, a win against only one comparator, a large gain in one hand-selected size bin, or a development-panel gain does not qualify as literature superiority.

No threshold may be relaxed after seeing P1 or comparator outcomes.

## Internal v8 non-regression report

On each exact-row comparator panel, P1 must also be evaluated against the exact panel-specific promoted-v8 membership baseline from which it starts. Report the change in macro F1, qualified matches, dominant precision, per-size F1, and membership count.

This is an architecture diagnostic, not a substitute for the Sugar/HDBSCAN superiority bars. If P1 materially damages its own v8 core interpretation on a transfer panel, that result must be reported even if some pairwise comparator endpoint is favorable.

## Failure and next-stage semantics

- P1 development failure: this literature protocol remains dormant; execute no P1 SonotaCo comparison.
- P1 development pass + `BROAD_CATALOGUE_SUPERIORITY`: P1 may proceed to separately frozen no-retuning generalization/validation.
- P1 development pass + `SPARSE_STREAM_SUPERIORITY`: P1 may proceed to separately frozen no-retuning generalization/validation with its claim restricted to sparse/weak-stream superiority.
- P1 development pass + `NO_LITERATURE_SUPERIORITY`: P1 does not satisfy the project superiority goal and may not be rescued by retuning this architecture on the matched outcomes. The already-frozen P2 successor may then be considered only according to its own succession rule.

No matched-literature outcome alone authorizes an OrbitTrace target-containing search.

## Target firewall

Solar longitude 20°–55° remains excluded before label normalization/storage, proposal/core construction, P1 model construction, membership assignment, and evaluation input preparation.

Forbidden throughout this comparison:

- OrbitTrace target coordinates or identity;
- OrbitTrace canonical members;
- any prior target rank or target-containing result;
- any event from the excluded 20°–55° interval;
- use of comparator labels before P1 memberships/rank hashes are frozen;
- any P1 retuning, model selection, threshold search, or alternative transfer variant.

This protocol is comparison-only. A final blind target deployment requires a separately frozen authorization, target success threshold, complete-ranking output, reveal procedure, and claim boundary after the selected method has satisfied the required no-retuning generalization evidence.
