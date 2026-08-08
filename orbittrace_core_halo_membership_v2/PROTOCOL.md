# OrbitTrace core/halo membership v2 — frozen independent-year transfer protocol

## Rationale

Cross-year seed-support expansion v1 was a binding no-go as a single-membership architecture: it materially improved membership F1 but diluted the high-purity family core when the expanded set was also used for discovery qualification. The result separates two scientific roles that v1 incorrectly forced into one object:

- **core:** the exact frozen v8 recurrent family used for detection, ranking, recurrence evidence, and discovery qualification;
- **halo:** a non-recursive cross-year support expansion used only to estimate additional stream members after the core and rank are frozen.

v2 tests that role separation without changing the expansion radius or any v8 detector rule.

## Frozen method

1. Run the exact label-free v8 architecture on a two-year target-excluded panel.
2. Freeze family graph, pooled centroids, v3/Brown/multiplicity scores, and multiplicity rank.
3. Preserve the original v8 `event_ids` as the immutable **core membership**.
4. Construct a **halo membership** with the exact v1 expansion rule:
   - other-year original core events are the only support points;
   - exact inherited v8 radiant-speed distance;
   - radius exactly 1.5;
   - one-pass, non-recursive expansion;
   - overlapping eligible events go to the nearest family, stable-family-ID tie break;
   - original core events cannot be reassigned.
5. Halo events never change family centroids, scores, recurrence, rank, or core qualification.

No threshold, radius, support-count, covariance, orbital, fusion, or variant search is allowed.

## Transfer panel

Use GMN 2020 and 2021 only. This pair is not claimed to be globally pristine: other OrbitTrace episode-level work has used historical years. It is, however, independent of the 2022–2023 v1 membership-expansion development result, and the earlier sparse-support multiplicity-v5 holdout stopped on a pre-data source-year guard before loading the 2020–2021 catalogues.

Solar longitude 20°–55° is excluded before label normalization. No OrbitTrace target coordinate, member, identity, target family, target-region event, Stage A/B output, or reveal may be accessed.

## Label boundary

All core families, core ranking, halo assignments, and a SHA-256 over both memberships must be frozen before known-shower labels are consulted for this architecture.

## Evaluation roles

Discovery performance is measured **only on the core**, because only the core generated and ranked the candidate.

Characterization performance is measured on the halo and compared with the same core families on the same annual labels. Report annual precision/recall/F1 in the bins `4–9`, `10–24`, `25–49`, `50–99`, `100+`, and `all`.

The halo may never rescue a failed core discovery gate.

## Frozen gates

### Core integrity/scientific gates

Use the inherited v8 development floors without relaxation:

- at least 100 recurrent families;
- at least 72 qualified known showers;
- persistence recovery@100 >=55;
- multiplicity recovery@100 >= Brown recovery@100 +1;
- multiplicity recovery@100 >= ceil(0.90 × persistence recovery@100);
- multiplicity recovery@100 >=54;
- core top-100 dominant precision >=0.50;
- exact 128-event episodes and Brown equivalence;
- no label-dependent proposal threshold.

### Halo characterization gates

- halo global macro F1 >= core macro F1 +0.05;
- annual all-shower mean F1 gain >=0.10 in both 2020 and 2021;
- 4–9-member mean F1 delta >=-0.02 in both years;
- at least one of `10–24`, `25–49`, `50–99`, or `100+` improves by >=0.10 in both years where present;
- halo top-100 dominant precision >=0.50.

The +0.10 material-difference rule is inherited from the frozen literature-comparison standard, not selected from this transfer result.

## Decision

Pass only if every core gate and every halo gate passes. A pass promotes the **dual-output core/halo architecture**, not v1's single-membership formulation. It still does not authorize OrbitTrace target Stage A/B and does not establish literature superiority; a separately frozen matched benchmark is required.

Failure is preserved and does not authorize radius tuning on this panel.
