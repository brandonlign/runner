# OrbitTrace bilateral core/halo v3 — frozen 2024–2025 transfer protocol

## Motivation

The exact v1 cross-year expansion showed that frozen v8 cores omit large amounts of true stream membership, but a one-sided halo can admit enough background to dilute the discovery object. v2 correctly separated discovery core from characterization halo and reproduced the large membership gain on 2020–2021, but missed its preregistered both-year all-shower F1 gate by 0.001983 in 2020.

No v1/v2 radius or gate is relaxed. v3 changes the *support topology*, not any threshold: a non-core event must be supported by the frozen family core in **both** years rather than only by the opposite year.

## Frozen architecture

The discovery output is unchanged v8:

- exact label-free fixed4 proposals;
- exact v8 connected recurrent families;
- exact pooled family-year centroids;
- exact 128-event v3/Brown/multiplicity scoring;
- exact multiplicity ranking;
- original family event IDs are the immutable **core**.

The characterization halo is one deterministic post-ranking layer:

1. For target year `y`, let `C_y` be the family's original v8 core events in year `y` and `C_o` its original core events in the other year.
2. A non-core target-year event is halo-eligible only if:
   - its minimum exact inherited v8 distance to `C_y` is `<= 1.5`, **and**
   - its minimum exact inherited v8 distance to `C_o` is `<= 1.5`.
3. Both radii are exactly the existing v8 family-link radius. No new scale is introduced.
4. If more than one family is eligible, assign exclusively by the smallest `max(d_same, d_other)`, then smallest `d_same + d_other`, then stable family ID.
5. Original core events are never reassigned.
6. Halo events are never reused as support, never update centroids, never update scores, and never affect recurrence, ranking, or discovery qualification.

The computational solar-longitude prefilter may use the mathematically necessary 6° bound implied by the inherited distance <=1.5, but exact full distances make every scientific decision.

## Transfer panel and blindness

Use GMN 2024 and 2025 only.

This is a method-specific transfer panel for the newly defined bilateral halo. These years have appeared in earlier OrbitTrace catalogue-ranking work, so this is not claimed as globally pristine external validation. The bilateral rule itself is frozen before its 2024–2025 membership result is opened and was derived from the v1/v2 structural failure mode, not from 2024–2025 performance.

Solar longitude 20°–55° is removed before label normalization or method operations. No OrbitTrace coordinate, member, identity, prior target family/rank, target-region event, Stage A/B output, or reveal may be accessed.

All core families, core ranking, bilateral halo assignments, and a SHA-256 over both memberships are frozen before known-shower labels are consulted.

## Evaluation

Discovery performance is evaluated only on the core. Halo performance is characterization-only.

Report core and halo:

- global macro F1 under the unchanged multiplicity order;
- top-100 dominant precision;
- annual best-family mean precision/recall/F1;
- annual mean F1 in bins `4–9`, `10–24`, `25–49`, `50–99`, `100+`, and `all`;
- halo growth/conflict counts.

## Gates

The exact v2 gates are retained without relaxation.

### Core gates

- >=100 recurrent families;
- >=72 qualified known showers;
- persistence recovery@100 >=55;
- multiplicity recovery@100 >= Brown recovery@100 +1;
- multiplicity recovery@100 >= ceil(0.90 × persistence recovery@100);
- multiplicity recovery@100 >=54;
- core top-100 dominant precision >=0.50;
- >=24 scannable bins each year;
- exact 128-event episodes and Brown equivalence;
- zero label-dependent proposal threshold.

### Halo gates

- halo global macro F1 >= core macro F1 +0.05;
- annual all-shower mean F1 gain >=0.10 in both years;
- annual 4–9-member mean F1 delta >=-0.02 in both years;
- at least one of `10–24`, `25–49`, `50–99`, or `100+` improves by >=0.10 in both years where present;
- halo top-100 dominant precision >=0.50.

The +0.10 material-difference standard remains inherited from the frozen literature-comparison protocol.

## Decision

Pass only if every integrity, core, and halo gate passes. A pass promotes the dual-output **v8 core + bilateral halo** architecture for separate validation/benchmarking; it does not alter the frozen v8 Stage A/B firewall or authorize target access.

Failure is binding for this exact bilateral rule and does not authorize radius or gate tuning on 2024–2025.
