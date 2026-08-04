# Majority-conditioned recurrence: frozen no-score source audit

Status: frozen before any candidate score, null catalog, injection, threshold, recovery value, or continuation decision is computed.

## Scientific motivation

The independently seeded local-contrast method in PR #82 improved weak recurrent recovery and recurrence margin but failed because smooth structure shared across all observing years still produced catalog-level false detections. Spatial high-pass filtering reduced broad structure within each year, but it did not exploit the defining difference between the nuisance and a recurrent stream:

- the stress nuisance is present in all fifteen years;
- the frozen recurrent injection is present in only five years.

This candidate changes the annual spatial evidence itself rather than recombining the same annual p-values or retuning a killed filter.

## Frozen candidate derivation

Starting from the exact worst-family recurrence source SHA-256 `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac`, for each template width and grid cell:

1. compute the unchanged annual one-sided Poisson excess evidence maps;
2. compute the pointwise median annual evidence across all fifteen years;
3. subtract that common annual median from every year's evidence and truncate below zero;
4. take the third-strongest adjusted annual evidence;
5. maximize over the unchanged four template widths.

The median is fixed prospectively and has no tunable prevalence parameter. Because the injected stream is active in five of fifteen years, it cannot control the median under the frozen injection model; a nuisance shared across all years should be removed as common mode.

No alternate quantile, trimmed mean, leave-one-year rule, subtraction coefficient, truncation, recurrence order, template width, grid, null family, injection design, or comparator is screened in this branch.

## Allowed source-audit operations

- reconstruct and hash-verify the exact worst-family source;
- apply the committed deterministic derivation script;
- compile the derived source;
- record the derived source SHA-256, byte count, functions, constants, CLI arguments, and exact source;
- verify statically that one new score map and method key were added and that the existing simulator, null families, injections, and comparators remain present.

## Forbidden operations

This branch may not install scientific dependencies, download the observed subset, import or execute the derived detector, generate a histogram, sample a null, inject a stream, compute a score, set a threshold, or inspect an endpoint.

A successful source audit authorizes only a separately frozen reduced kill screen with a new seed and predeclared trial counts and gates. It does not authorize a real-shower benchmark, catalogue scan, or GhostStream application.