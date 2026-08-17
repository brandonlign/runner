# Paired GMN loader repair — technical no-result only

## Triggering failure

First paired-GMN activation run `31997173314` stopped in pretruth loading before either HDBSCAN fit began. The immutable label-free snapshot stores the already-normalized event schema produced by the frozen snapshot exporter:

`id, year, sol, lon, lat, vg`

The paired runner mistakenly passed those normalized rows back through the historical raw-row `normalize_event()` function, which expects aliases such as `sun_lon` / `ecl_lat`. It therefore raised before constructing GEO6 or GEO4.

The failed run downloaded no sealed truth artifact, froze no candidate hierarchy, and produced no scientific metric. It is a technical no-result.

## Allowed repair

Keep the frozen scientific runner `run_paired_development.py` byte-identical. Execute it through a compatibility wrapper that replaces only `load_label_free_snapshot()` with a loader for the snapshot's documented normalized schema.

The repaired loader must:

- verify the exact bound manifest and row hashes through the frozen runner's existing checks;
- require exactly the normalized fields `id, year, sol, lon, lat, vg`;
- require matching year, finite coordinates, positive speed, unique IDs, and protected `[20°,55°]` exclusion;
- preserve row order and values exactly;
- perform no coordinate transformation, HDBSCAN operation, label access, ranking, or metric calculation.

After loading, the unchanged frozen scientific runner constructs the same GEO6 and GEO4 matrices, density-synchronous objectives, candidates, metrics, and gates defined before the failure.

## Governance

This repair changes no scientific hypothesis, representation, HDBSCAN setting, recurrence objective, rank rule, evaluator, promotion gate, snapshot input, or dormant SonotaCo contingency. A clean retry is allowed only after a zero-data compatibility audit passes and a repair execution freeze is committed.
