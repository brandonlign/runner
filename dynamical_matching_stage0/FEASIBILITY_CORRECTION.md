# Labeled data-gate correction

The original runner data gate completed successfully as workflow `30849390889` and produced verdict `KILL_DYNAMICAL_COHERENCE_DATA_GATE`. That result is preserved and is not overwritten.

Before any propagation or dynamical score was computed, inspection exposed two internal protocol/implementation contradictions.

## 1. State-reconstruction denominator

The protocol required the **selected benchmark rows** to reconstruct nominal states. The extraction implementation instead divided state-reconstructable rows by every raw row carrying a target IAU label, including rows intentionally excluded before benchmark selection because their nominal state was incomplete, hyperbolic/unbound under the frozen bound-orbit screen, or failed another quality condition.

The saved benchmark pool contains only `quality_ok` events, and `quality_ok` already requires a complete nominal state. Therefore the original 95% denominator did not test the stated benchmark-pool requirement. Raw-label state fractions remain important diagnostics and are retained, but they are not a fatal feasibility gate once every frozen year/control stratum contains the required absolute number of valid states.

This is a semantic implementation correction, not a relaxed performance threshold.

## 2. Disjoint-subgroup count

The protocol simultaneously specified:

- eight disjoint 20-event subgroups per control;
- five events from each of four frozen years in every subgroup; and
- a data gate of only 20 valid events per control-year.

Eight disjoint subgroups would require 40 events per year, so the specification was impossible for a control that exactly passed the written gate. The corrected Stage-0 design uses **four** disjoint 20-event subgroups, requiring exactly the prespecified 20 events per year.

This correction was made from arithmetic and event-count feasibility only. No static-matching result, orbit propagation, clone result, AUROC, or GhostStream result had been computed.

## Consequence of the corrected gate

Four controls satisfy the written 20-per-year requirement across 2019, 2021, 2023, and 2025:

- IAU 4 / GEM;
- IAU 6 / LYR;
- IAU 7 / PER;
- IAU 13 / LEO.

IAU 10 / QUA is retained as a predefined control but is technically unusable for the frozen four-year design because 2019 supplies only eight quality-screened events. It is not removed because of a dynamical outcome.

The candidate now advances only to a **static matched-null feasibility gate**. It still has no positive methodological result.
