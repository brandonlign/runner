# Predictability-normalized dynamics: static matched-null gate

Status: frozen before matched-group construction. GhostStream is excluded.

## Purpose

A dynamical comparison is meaningless if known shower groups cannot be paired with chance groups that are already similar **today**. This gate tests whether the four usable controls can be matched to IAU `-1` meteors on observing year, activity month, orbit regime, uncertainty quality, and present-day `D_SH` compactness.

No propagation occurs in this gate.

## Fixed controls and subgroups

Usable controls are IAU 4/GEM, 6/LYR, 7/PER, and 13/LEO. Frozen years are 2019, 2021, 2023, and 2025.

For each control and year:

1. rank quality-screened events lexicographically by the sum of log element uncertainties, fit error, negative `Qc`, negative station count, and trajectory identifier;
2. retain the first 20;
3. assign them round-robin to four subgroups, giving every subgroup exactly five events from each year.

The 16 resulting 20-event shower subgroups are disjoint within each control.

## Transformed features

Orbit-regime vector:

- `log(a)`;
- `e`;
- `i` in degrees;
- `q`;
- Tisserand parameter with respect to Jupiter, using the supplied value or a fixed formula with `a_J = 5.2044 au`.

Uncertainty vector:

- `log10(max(sigma_a, 1e-12))`;
- `log10(max(sigma_e, 1e-12))`;
- `log10(max(sigma_i, 1e-9 deg))`;
- `log10(max(sigma_omega, 1e-9 deg))`;
- `log10(max(sigma_Omega, 1e-9 deg))`;
- `log10(max(sigma_anomaly, 1e-9 deg))`.

For each control month, both vectors are standardized using the median and `IQR / 1.349` of the frozen sporadic reservoir. Any scale below `1e-6` is replaced by `1e-6`.

## Candidate chance groups

For every shower subgroup:

1. use only IAU `-1` events from the same control month and the same four years;
2. select up to 300 deterministic seed events nearest the shower subgroup's median standardized orbit vector;
3. around each seed and within each year, rank sporadic events by standardized orbit distance to the seed plus `0.25` times standardized uncertainty distance to the shower subgroup median;
4. construct exact five-per-year groups using frozen neighborhood sizes `K = 5, 8, 12, 20, 32, 50`;
5. for each `K`, use the nearest five and two deterministic fixed-seed samples of five from the nearest `K` events.

No candidate is generated from a shower label or from GhostStream.

## Match requirements

A candidate is eligible only if all hold:

- exactly 20 distinct events and exactly five from each frozen year;
- standardized distance between group median orbit vectors no greater than `0.50`;
- standardized distance between group median uncertainty vectors no greater than `0.50`;
- median pairwise `D_SH` differs from the shower subgroup by no more than `max(0.002, 10%)`;
- 90th-percentile pairwise `D_SH` differs by no more than `max(0.003, 15%)`.

Eligible groups are ordered by the sum of normalized match discrepancies. Groups are greedily retained subject to:

- no duplicate event set;
- Jaccard overlap no greater than `0.25` with another retained group for the same shower subgroup;
- each sporadic event used no more than four times across all retained groups for one control.

At most 24 groups are retained per shower subgroup.

## Frozen continuation gate

The candidate advances to orbital propagation only if **every one of the 16 shower subgroups** obtains at least 12 eligible matched sporadic groups.

Additional diagnostics, not substitute gates:

- median and worst orbit-vector match distance;
- median and worst uncertainty-vector match distance;
- median relative errors in pairwise-`D_SH` median and 90th percentile;
- event-reuse distribution;
- candidate count before overlap/reuse filtering.

## Kill rules

A failure kills this benchmark formulation. Do not rescue it by:

- increasing orbit or uncertainty tolerances;
- widening `D_SH` tolerances;
- dropping a poor subgroup or control;
- changing the frozen years;
- using shower-labeled meteors as nulls;
- generating synthetic null groups after seeing the failure;
- applying the method to GhostStream.

A pass authorizes only the frozen short-horizon propagation benchmark. It is not evidence that the dynamical method works.
