# OrbitTrace v8 literature-method benchmark — frozen scientific conclusion

**Status:** final for this comparison track under the frozen v8 method.  No v8 parameter was changed in response to any comparator result.  No final OrbitTrace target reveal was performed, and no OrbitTrace coordinate, member, identity, target-region content, or excluded-interval content was accessed.

## Executive conclusion

The promoted v8 pooled-year-centroid multiplicity method **does not support a defensible claim of state-of-the-art sparse meteor-stream discovery** on the benchmarks completed here.

The strongest clean result is the exact-event-row comparison against the full Sugar uncertainty-aware pipeline.  On identical SonotaCo event rows and identical common post-hoc labels, v8 fails both preregistered sparse-win gates.  Its mean annual F1 is only slightly higher than Sugar in the 4–9 bin (+0.019 in 2023 and +0.006 in 2025), far below the preregistered +0.10 material-advantage threshold, while Sugar is substantially stronger in 10–24 and in overall catalogue recognition in both years.

Against catalogue HDBSCAN, v8 also fails the preregistered sparse-win gates on the blind-safe matched-survey panel.  V8 is materially stronger for mid-sized 25–99-member showers in both years, but not for the preregistered 4–9 regime and not across 4–24 in both years; HDBSCAN remains stronger for 100+ member showers.  A stricter exact-event-row HDBSCAN comparison cannot be completed with the frozen full v8 scoring stage because HDBSCAN's published quality-filtered catalogue leaves at least one recurrent v8 family with only 64 local events, while promoted v8 requires exactly 128.  Shrinking, padding, or changing that episode would alter v8 and is therefore prohibited.

Accordingly, the correct scientific positioning is **method-specific and limited**: v8 is a computationally efficient label-free recurrent-family detector/ranker with evidence of improved mid-sized-stream recovery relative to the faithful catalogue HDBSCAN transfer on this target-excluded SonotaCo benchmark.  It is not demonstrated to outperform full Sugar in the sparse regime, it does not pass the preregistered sparse superiority gates against HDBSCAN, and it cannot be generalized to CMOR radar wavelets or to all published meteor-stream discovery methods.

## Audit of published comparators

### Full Sugar uncertainty-aware pipeline — scientifically valid primary comparator

The repository contains faithful survey transfers for SonotaCo 2023 and 2025 using the published six-dimensional Sun-centered GEO representation, DBSCAN `min_samples=5`, frozen epsilon `0.028705145052265017`, 1,000 Gaussian clone catalogues, 50% overlap merging, retained recurrence >=100/1000, and strong recurrence >=500/1000.

The implementation is a faithful published-stage **survey transfer**, not an exact ASGARD covariance/software reproduction, because SonotaCo supplies marginal uncertainties rather than the original full covariance interface.  The target exclusion is applied before label access in both benchmark years.

Frozen full-Sugar runs:

- 2023: workflow `31076789635`, 30,414 events, 64 retained clusters, runtime 321.36 s.
- 2025: workflow `31075178517`, 23,200 events, 49 retained clusters, runtime 184.84 s.

The exact-row v8-vs-Sugar comparison completed successfully in workflow `31227437130`, artifact `9012618631`, with all integrity gates passing.

### Catalogue HDBSCAN — scientifically valid with a 2023 comparison-only blindness repair

The faithful catalogue transfer uses the published unstandardized GEO six-vector, `hdbscan==0.8.44`, Euclidean distance, `min_cluster_size=100`, package-default `min_samples`, and `eom` cluster selection.

The original 2025 transfer is blind-safe.  A source-only audit found that the original 2023 transfer parsed the raw archive directly and did not apply the comparison track's 20°–55° exclusion.  That original 2023 result remains preserved as a literature reproduction but is ineligible for the final blind-safe matched comparison.

A comparison-only 2023 rerun inserted exactly one pre-label exclusion immediately after solar longitude parsing and changed no HDBSCAN parameter or quality cut.  Workflow `31226945294` produced a blind-safe full-catalogue assignment with 26,460 rows; independent workflow `31227148081` verified that every assignment ID resolves and that zero assignment rows lie in the excluded interval without reading labels.  This blind-safe rerun is the canonical HDBSCAN-2023 input for the conclusions below.

### Southworth-Hawkins D_SH — valid but not a catalogue-discovery peer

The repository contains the exact Southworth-Hawkins distance implementation and the Rudawska-style single-link episode comparator.  Those are valid targeted/episode association comparators.  They are not a like-for-like ranked recurrent catalogue discovery procedure, and this track did not manufacture a new all-pairs catalogue algorithm from them.  D_SH therefore cannot support a broad win/loss claim for v8 catalogue discovery.

### CMOR-style wavelet — scientifically deferred, not scored as a loss

The seven-year SonotaCo feasibility audit found 199 of 324 local solar-longitude bins meeting the published 300-radiant support floor, or 61.4%, below the preregistered 80% requirement.  The CMOR-style wavelet comparator is therefore **deferred for input incompatibility**.  This is not evidence that the wavelet method performs poorly and cannot be counted as a v8 win.

## Preregistered decision rules

Before the new matched executions, a size-bin advantage was defined as material only when

`delta = v8 mean F1 - comparator mean F1 >= 0.10`.

V8 could be said to beat a comparator in the 4–9 sparse regime only if that material advantage occurred in both 2023 and 2025.  It could be said to beat a comparator across the broader 4–24 sparse regime only if both the 4–9 and 10–24 bins passed in both years.  All larger bins were mandatory in the report.

Those thresholds were not changed after seeing any result.

## V8 versus full Sugar: exact event rows and common labels

Workflow `31227437130` used exactly the frozen Sugar assignment-row universe in each year, ran the exact promoted v8 family and multiplicity machinery on those rows, froze the v8 ranking, and only then loaded the common shower labels.  All v8 local episodes were exactly 128 events and all integrity gates passed.

| Year | Annual-size bin | Showers | v8 mean F1 | Sugar mean F1 | v8 - Sugar |
|---:|:---|---:|---:|---:|---:|
| 2023 | 4–9 | 13 | 0.0769 | 0.0577 | +0.0192 |
| 2023 | 10–24 | 17 | 0.0479 | 0.3791 | -0.3312 |
| 2023 | 25–49 | 7 | 0.0571 | 0.1534 | -0.0963 |
| 2023 | 50–99 | 5 | 0.0260 | 0.6159 | -0.5900 |
| 2023 | 100+ | 14 | 0.1424 | 0.7397 | -0.5973 |
| 2023 | all eligible | 56 | 0.0774 | 0.3876 | -0.3101 |
| 2025 | 4–9 | 13 | 0.0699 | 0.0641 | +0.0058 |
| 2025 | 10–24 | 14 | 0.0497 | 0.2399 | -0.1902 |
| 2025 | 25–49 | 9 | 0.0490 | 0.2557 | -0.2067 |
| 2025 | 50–99 | 4 | 0.1306 | 0.4164 | -0.2858 |
| 2025 | 100+ | 12 | 0.1509 | 0.7753 | -0.6245 |
| 2025 | all eligible | 52 | 0.0842 | 0.3358 | -0.2516 |

**Frozen decision:**

- 4–9 sparse-win gate: **FAIL**.
- 4–24 broader sparse-win gate: **FAIL**.
- Overall catalogue recognition: **Sugar clearly wins** on this exact-row endpoint in both years.
- V8 does **not** beat full Sugar in the sparse regime.

The exact-row v8 family catalogue contained 43 recurrent families.  Its scaled top-K was 20; top-K dominant-label precision was 0.890.  That is a genuine v8 ranking strength, but it does not compensate for the low annual recovery/recall on the same rows.  Sugar returned 64 retained clusters in 2023 and 49 in 2025; the fraction of returned Sugar clusters with dominant mapped-known-shower precision >=0.5 was 0.953 and 0.959 respectively, versus 0.767 over v8 recurrent families.  These burden statistics are reported descriptively because the returned objects are not identical algorithmic constructs.

Compute is a real v8 advantage in these recorded runs: the v8 exact-Sugar pairwise execution took 56.3 s for both years, whereas the 1,000-clone Sugar runs took 321.4 s in 2023 and 184.8 s in 2025.  Wall-clock comparisons remain implementation- and runner-dependent, so this is evidence of lower compute burden rather than a universal speed ratio.

## V8 versus catalogue HDBSCAN: blind-safe matched-survey endpoint

The strongest fully executable common-survey comparison keeps each method's faithful published quality interface but uses the same SonotaCo years, the same target exclusion, and the same mapped-label evaluation framework.  V8's target-excluded SonotaCo run used its own frozen scan input; HDBSCAN used its published quality cuts.  Therefore these numbers are **matched survey/year/label results, not identical-event-row results**.

| Year | Annual-size bin | v8 mean F1 | HDBSCAN mean F1 | v8 - HDBSCAN |
|---:|:---|---:|---:|---:|---:|
| 2023 | 4–9 | 0.0667 | 0.0000 | +0.0667 |
| 2023 | 10–24 | 0.1592 | 0.0036 | +0.1556 |
| 2023 | 25–49 | 0.3360 | 0.0000 | +0.3360 |
| 2023 | 50–99 | 0.4611 | 0.1590 | +0.3021 |
| 2023 | 100+ | 0.5857 | 0.5990 | -0.0133 |
| 2025 | 4–9 | 0.0000 | 0.0000 | 0.0000 |
| 2025 | 10–24 | 0.0250 | 0.0000 | +0.0250 |
| 2025 | 25–49 | 0.1450 | 0.0308 | +0.1142 |
| 2025 | 50–99 | 0.3677 | 0.2677 | +0.1000 |
| 2025 | 100+ | 0.6129 | 0.7074 | -0.0945 |

**Frozen decision:**

- 4–9 sparse-win gate: **FAIL** because the +0.10 material threshold is not met in either year.
- 4–24 broader sparse-win gate: **FAIL** because the required 4–9 gate fails and the 10–24 advantage is not material in 2025.
- Mid-sized 25–99 showers: **v8 is materially stronger in both years** on this matched-survey endpoint.
- Large 100+ showers: **HDBSCAN is stronger in both years**, modestly in 2023 and more clearly in 2025.

### Exact-row HDBSCAN limitation

The stricter exact-row benchmark used the verified blind-safe HDBSCAN assignment universe: 26,460 rows in 2023 and 19,658 in 2025.  The frozen v8 scanner successfully produced 2,410/1,859 passing quartets and 413/327 components, then built 38 recurrent families.  During the unmodified v8 multiplicity scoring stage, one 2025 family had only 64 events in its local window.  Promoted v8 requires an exact 128-event local episode, so the workflow stopped before a valid full-v8 ranking could be produced.

This is a genuine **method-interface limitation**.  It is not counted as either a v8 win or an HDBSCAN win.  Reducing, padding, or otherwise changing the 128-event requirement would modify v8 after comparator exposure and was not done.

## Where each method wins and loses

### V8

Strengths supported here:

- label-free cross-year recurrent-family construction;
- materially better 25–99-member recovery than catalogue HDBSCAN on both target-excluded SonotaCo benchmark years;
- useful multiplicity ranking precision among the families it does find;
- substantially lower recorded compute burden than the full 1,000-clone Sugar pipeline;
- explicit recurrence requirement rather than independent annual clustering.

Weaknesses supported here:

- no preregistered superiority in the 4–9 bin against either primary comparator;
- no preregistered 4–24 superiority against HDBSCAN;
- much lower 10–24 and overall exact-row recovery than full Sugar;
- weak large-shower recall relative to both catalogue methods;
- sensitivity to upstream event-row filtering: the exact HDBSCAN row universe violates the frozen 128-event local-scoring precondition;
- the broad target-excluded SonotaCo ranking produced a substantial false-positive/candidate burden despite stronger development precision.

### Full Sugar

Strengths supported here:

- strongest overall catalogue recognition among the methods compared under exact common rows;
- very strong 10–24 performance relative to v8 in both years;
- strong 50+ and especially 100+ shower recovery;
- high dominant-known-shower precision among retained clusters;
- uncertainty propagation materially improves over the deterministic core in the existing frozen work.

Weaknesses/limits:

- 4–9 recovery remains weak in absolute terms; its exact-row mean F1 is only 0.058 in 2023 and 0.064 in 2025;
- much higher computational cost because of 1,000 clone catalogues;
- SonotaCo transfer uses marginal uncertainties rather than the original full ASGARD covariance interface.

### Catalogue HDBSCAN

Strengths supported here:

- strong recovery for 100+ member showers;
- simple, fast catalogue clustering with a faithful published implementation;
- robust large-cluster behavior across both benchmark years.

Weaknesses supported here:

- the published `min_cluster_size=100` configuration is intrinsically poorly suited to direct recovery of 4–24-member reference showers;
- substantially weaker than v8 for 25–99-member showers on the blind-safe matched-survey endpoint;
- its quality-filtered exact-row universe is too locally sparse for the frozen full v8 scoring interface, preventing a strict identical-row full-method ranking comparison.

## State-of-the-art claim boundary

The following claims are **not supported** and should not appear in the paper or project summary:

- "v8 is state of the art for sparse meteor-stream discovery";
- "v8 beats Sugar for sparse streams";
- "v8 beats HDBSCAN for sparse streams" without a narrower size/survey qualifier;
- "v8 beats CMOR wavelets";
- "v8 beats all published meteor-stream discovery methods."

A defensible positive statement is narrower:

> On target-excluded SonotaCo 2023/2025 benchmarks, the frozen label-free recurrent v8 method recovered mid-sized 25–99-member reference showers more strongly than a faithful catalogue-HDBSCAN transfer, while requiring substantially less computation than a full 1,000-clone Sugar uncertainty pipeline.  It did not demonstrate superiority to Sugar in the sparse 4–24 regime or overall catalogue recovery.

Even that statement should be accompanied by the exact-row HDBSCAN incompatibility and the CMOR input-incompatibility caveat.

## Preserved negative and inconclusive results

- v9 support-overlap recurrence remains a frozen no-go: it produced more families but reduced multiplicity recovery from the v8 development level to 36/100.
- The AMOR external v8 test remains integrity-clean but power-inconclusive because only 19 recurrent families were generated.
- CMOR wavelet remains deferred for input incompatibility, not scored negatively.
- The first 2025 parser transport failure is preserved as a pre-scoring implementation failure.
- The original HDBSCAN-2023 transfer's missing blind exclusion is preserved as an integrity finding; the comparison-only blind-safe rerun is used instead.
- The exact-row HDBSCAN-v8 full-method comparison remains technically incomplete because of the frozen 128-event v8 local-episode precondition.
- The exact-row Sugar result is negative for v8 and is preserved without any v8 retuning.

## Final answers

**Does v8 beat HDBSCAN for sparse-stream discovery?**  **No under the preregistered definition.**  It does beat HDBSCAN for the narrower 25–99-member mid-sized regime on both matched-survey years, but it fails the 4–9 and 4–24 sparse superiority gates.

**Does v8 beat full Sugar in the sparse regime?**  **No.**  On exact identical rows it has only a negligible advantage in 4–9 and is decisively worse in 10–24 and overall recovery.

**Where does each method win?**  V8's strongest niche here is recurrent mid-sized candidate recovery plus lower compute; Sugar is strongest overall and particularly from 10 members upward; catalogue HDBSCAN is strongest for large 100+ showers and is computationally simple.

**Can OrbitTrace legitimately claim state-of-the-art sparse meteor-stream discovery from v8?**  **No.**  The benchmark evidence supports a narrower contribution claim about a distinct label-free recurrent detector with mid-sized-stream sensitivity and favorable compute, not a state-of-the-art sparse-discovery claim.

This conclusion is frozen for the current promoted v8.  Changing v8 in response to these results would constitute a new method-development cycle and is outside this comparison track.
