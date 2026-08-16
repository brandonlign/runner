# Engineering repair 2 — stale conditional-protocol blob pin

## Classification

**ENGINEERING NO-RESULT REPAIR ONLY.**

Workflow run `31972337680`, job `95226567335`, successfully installed the exact historical reader `gmn-python-api==0.0.13` under CPython 3.10 but stopped immediately afterward during frozen-source hash assertions. `audit.py` never executed, so no GMN monthly file or project `Num (stat)` value was read.

The stale assertion expected conditional station-weighted protocol blob `d2101cc270e64fcc3ca3eceb84e5584e4a75b355`. The actual protocol that had already been committed before any station-count access is blob:

`ea5d862268fc2c69d37b8b4c10db187fe31cdd5a`

The protocol content/science is not modified. Repair only the workflow assertion to the actual pre-existing blob.

The already-preimplemented conditional structural runner is also pinned before the first availability outcome:

`orbittrace_station_weighted_topomodal_scale_v1/run_diagnostic.py`

blob `24b4970981dcff677d66fc230d5998e7e51ed5f2`.

No source endpoint, parsed field, event universe, completeness rule, station-weight formula, graph, density, support, subset, comparator, metric, gate, or firewall changes.