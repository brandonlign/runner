# Descriptive cross-year synthesis of the immutable fixed-4° SonotaCo evidence

Status: post-confirmation evidence synthesis. This analysis is explicitly **not** a confirmation-gate adjudication, model revision, threshold change, or route to a catalogue/GhostStream application.

## Immutable inputs

- SonotaCo 2025 fixed-scale development artifact from workflow `30912903515` / artifact `8893846191`;
- SonotaCo 2024 one-shot confirmation artifact from workflow `30918254066` / artifact `8895979919`.

The workflow must hash-verify the exact result JSON and positive/negative event-record files before computing anything. It reruns no detector, calibration, parser, or episode generator.

## Frozen summaries

Using exact event-record p-values, report for each year and descriptively pooled across years:

- integer detection counts and rates for k=4,6,8,12 at alpha 0.05 and 0.01;
- exact Clopper-Pearson 95% intervals;
- integer false-positive counts and rates;
- Fisher exact tests for year-to-year heterogeneity in each recall endpoint;
- the two year-specific fixed-4° weak AUROCs.

The synthesis must preserve the formal 2024 verdict `FAIL_SONOTACO_2024_FIXED4_CONFIRMATION`. Pooled development-plus-confirmation values may describe consistency but may never replace or rescue that verdict.

## Source identity repair

The first workflow attempt stopped before downloading either evidence artifact because the pre-upload SHA-256 did not match GitHub's committed text representation. The already committed source is authoritative and unchanged. Its exact Git blob identity is `509c2513d169270876e3db20890a7182c1cbdfc3`; the workflow verifies that blob identity with `git hash-object` and compiles the file before any artifact access.
