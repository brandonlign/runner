# Original v3-primary catalogue-v6 calibration-label dependence

## Status

**Original/repaired v6 is not eligible for promotion as the final target-free OrbitTrace detector.**

This conclusion is source-based and was established before any completed original-v6 scientific verdict.

## Exact finding

The frozen support parser applies the 20°–55° blind exclusion before reading a shower label, so the target interval itself remains protected during development. However, after that exclusion it normalizes the catalogue shower label and admits an event to the empirical-null reservoir only when:

```python
if label == "SPORADIC":
    calibration_by_year[year].append(dict(event, complex_key="SPORADIC"))
```

The scan copy of the same event is label-hidden (`iau=0`, `complex_key="HIDDEN"`), and labels do not enter proposal geometry directly. The dependence is specifically the **selection of null-calibration members from catalogue shower identity**.

The downstream `MondrianWindowFactory` does not need labels. It bins calibration events by solar longitude and samples 128-event local episodes using geometry-only event rows. Therefore the scientific dependence is removable without altering the scoring/ranking architecture.

## Consequence

Even if the exact original-v6 fanout execution passes its preregistered performance gates, that result may be retained as:

- an engineering-equivalence result;
- an upper-bound/diagnostic on the v3-primary architecture under a catalogue-labelled sporadic null;
- evidence about the proposal/rescore/family machinery.

It **must not** be used to claim that the complete detector is label-free or to authorize the final OrbitTrace target reveal.

It also must not trigger a literature-superiority claim as the final method, because the candidate method would have used catalogue truth information in calibration that a genuinely target-free discovery procedure would not possess.

## Frozen repair path

`v6-LF all-event Mondrian null` replaces only the label-selected calibration reservoir with every geometrically valid target-excluded scan event. The null sampler, score functions, empirical p-values, thresholds, proposal budget, exact rescoring, components, recurrence, rankings and memberships remain unchanged.

All-event contamination by real streams is accepted as a conservative power cost. No stream trimming, density masking, iterative cleaning or alternative null is authorized after seeing the v6-LF result.

Promotion sequence:

1. v6-LF target-excluded development;
2. exact-row matched Sugar/HDBSCAN evaluation on external SonotaCo without retuning;
3. only if the external benchmark meets the frozen superiority claim, adapt the already-separated exact-ID blind reveal firewall to the frozen winning method;
4. otherwise follow the already-frozen v8-core membership succession (P1, then P2 if its prerequisite is met), never original v6.

This limitation does not expose OrbitTrace coordinates, members, identity, or target-containing results.
