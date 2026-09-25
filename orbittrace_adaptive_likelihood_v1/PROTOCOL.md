# OrbitTrace adaptive recurrent likelihood development — v1

## Isolation and preservation

This work is a new OrbitTrace method-development branch. It does not edit, replace, reinterpret, or erase any frozen predecessor:

- fixed-4° coverage-normalized anchored four-clique detector;
- Brown-family sparse-episode wavelet comparator;
- promoted wavelet-ranking + minimum-fixed4-rescue dual channel;
- Sugar et al. deterministic and uncertainty-aware transfers;
- Peña-Asensio–Ferrari HDBSCAN transfer;
- prior hybrid, sparse-tail, catalogue-ranking, and blind-recovery outcomes.

All predecessor sources and results remain authoritative for the experiments that produced them.

## Goal

Develop a new OrbitTrace-owned primary ranking statistic that can plausibly exceed the Brown-family wavelet in general weak-stream discrimination without sacrificing fixed4's sparse-stream advantage.

The long-term architecture is **adaptive recurrent likelihood**:

1. uncertainty-aware local likelihood at the episode/candidate level;
2. multiscale search with the scale maximum calibrated as part of the statistic;
3. cross-year recurrence evidence at catalogue level;
4. fixed4 retained only as an independent extreme-sparse rescue channel.

This v1 branch implements and tests only stage 1–2. Recurrence is deliberately not claimed until a separate catalogue layer exists.

## Development corpus

The first development execution uses the already exposed SonotaCo 2025 frozen 128-event episode benchmark. It is development evidence only.

No OrbitTrace coordinates, canonical members, target interval, blind-recovery output, or target-specific exception may enter scoring or parameter choice.

If v1 survives development, its source is frozen before transfer. Final prospective evidence must come from a separately reserved corpus/survey not used to choose the v1 architecture.

## Frozen v1 score

For each event used as a possible local center and each fixed scale pair:

- angular/speed scale bank:
  - 2° / 5%;
  - 3° / 7.5%;
  - 4° / 10%;
  - 6° / 15%;
- angular separation is spherical;
- speed separation uses log geocentric speed;
- pair distances are broadened by the event-pair measurement uncertainties;
- RA/Dec marginal errors are mapped to a small-angle scalar angular uncertainty using `sqrt((sigma_RA cos(dec))^2 + sigma_Dec^2)`;
- the compact core is `r < sqrt(3)`;
- the local background shell is `sqrt(3) <= r <= 4`;
- at least three non-anchor core events are required;
- the expected core background count is estimated from shell density with a fixed Jeffreys-style `+0.5` pseudocount;
- one-sided Poisson count log-likelihood evidence is computed for a core excess;
- positive within-core concentration evidence is added relative to a uniform core;
- the episode score is the maximum local score over all event centers and all four scales.

The external frozen Mondrian benchmark performs bin-wise empirical calibration. Therefore the scale maximization and anchor maximization are included inside the calibrated statistic; no uncorrected post-hoc scale selection is allowed.

## Development gates

The first v1 development result is classified as a pass only if all of the following hold on SonotaCo 2025:

- weak-stream AUROC strictly exceeds the frozen Brown-family wavelet;
- alpha=.05 k=4 recall is at least the frozen fixed4 recall;
- alpha=.05 recall at k=6, 8, and 12 is no more than 0.03 below the wavelet at each k;
- pooled alpha=.05 FPR is <= 0.055;
- worst reporting-sector alpha=.05 FPR is <= 0.08;
- every predecessor reproduction/integrity gate in the frozen benchmark still passes.

A scientific development failure is preserved as a result and does not authorize silent tuning on the same output. A materially revised v2 must be separately named and preserve v1.

## Prohibited claims at this stage

- v1 is the best meteor-stream method;
- v1 discovered or recovered OrbitTrace;
- v1 has catalogue-scale recurrence capability;
- v1 replaces fixed4, the wavelet, Sugar, or HDBSCAN;
- a development pass is prospective validation.
