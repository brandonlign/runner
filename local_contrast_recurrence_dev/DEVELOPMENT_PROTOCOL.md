# Local-contrast hard recurrence: frozen development protocol

Status: development-only benchmark on the exact SonotaCo simulator and injections from ReplicaStream PR #8. It cannot authorize GhostStream application.

## Failure mechanism addressed

PR #8 showed that the hard third-strongest-year recurrence statistic rejected one-year artifacts but failed badly under a smooth spatial distortion shared across all years. PR #68 showed that worst-family calibration controls this null, but the resulting high threshold limits weak recurrence power.

A genuine compact meteor stream should produce a local peak above its surrounding annual radiant-speed field. The shared-structure stress null is deliberately broad and smooth. This candidate removes that broad local component before annual recurrence aggregation rather than recombining the same annual p-values.

## Frozen candidate

For every year, template width, and grid location:

1. compute the unchanged one-sided annual Poisson excess evidence `E = -log10(p)`;
2. estimate broad local evidence with a Gaussian kernel of fixed sigma `(3.0, 3.0, 2.0, 1.5)` grid bins in solar longitude, Sun-centered ecliptic longitude, latitude, and speed;
3. compute nonnegative local contrast `max(E - broad_background, 0)`;
4. use the third-strongest annual contrast as the recurrence score;
5. maximize over the unchanged four template widths.

The kernel is fixed prospectively: it is wider than the injected/template footprint and wider than the shared-distortion correlation scale used in the PR #8 null. No alternate kernel is screened in this branch.

## Calibration and evaluation

Every detector uses worst-family calibration from PR #68: estimate complete-search thresholds independently from ideal and shared-structure nulls, then use the larger threshold.

Development run:

- 20 calibration catalogs per family;
- 20 fresh null catalogs per family;
- 30 injections per strength;
- unchanged recurrent injections, one-year artifacts, pooled, pooled-confirmation, original hard recurrence, and soft-product comparators;
- unchanged catalog alpha 0.10.

## Development decision

The candidate merits a full frozen Stage-0 only if it:

- controls both null families at observed FWER <= 0.20 in this reduced screen;
- detects zero or at most 0.20 weak one-year artifacts;
- improves weak recurrence margin by at least 0.05 over the strongest valid comparator;
- loses no more than 0.05 strong recurrence.

This reduced run is only a kill screen. Passing does not validate the method; it authorizes a larger independently seeded frozen benchmark.
