# MAARSY 2016/2017 geometry-power archive physical-order correction

Frozen after run `31233625448` and **before any corrected execution, component construction, family construction, ranking, or N power verdict**.

## What the failed run exposed

Run `31233625448` passed all source, v8, author-semantic, Stage-0E provenance, HDF5-field, target, and Zenodo-link guards. It then began the first scientific-value read under the frozen 2016/2017 panel.

The run processed exactly two selected members before stopping:

- `data/2016/03/kep_collect.h5`: 9,518 rows, 0 rows in the frozen 20°–55° blind interval, 9,517 geometry-eligible rows after the blind-first read order;
- `data/2016/06/kep_collect.h5`: 4,849 rows, 0 rows in the frozen 20°–55° blind interval, 4,846 geometry-eligible rows.

The next selected tar header was `data/2016/02/kep_collect.h5`. The runner then stopped on the preregistered procedural assertion that selected year-month members appear in monotonically increasing physical tar order:

`RuntimeError: non-monotonic selected month order in 2016: 2`

No 2016/02 payload was opened. No within-year fixed4 scan, component construction, cross-year family construction, v8 pooled-centroid repair, local episode scoring, multiplicity/Brown/v3/persistence ranking, orbit read, Q count, external pass/fail verdict, OrbitTrace target access, or final GMN Stage A/Stage B execution occurred.

## Why a narrow correction is allowed

The scientific panel was frozen as **all** `data/2016/MM/kep_collect.h5` and `data/2017/MM/kep_collect.h5` members, stopping at the first `data/2018/` member. Physical tar header order was never intended to select or exclude a scientific month; the monotonic-order assertion was an ingestion-integrity assumption.

The archive has now demonstrated that its physical tar order is not chronological. Requiring chronological physical order would turn a packaging convention into an accidental scientific exclusion, despite the selected member set already being fixed independently of values.

This amendment is triggered solely by the observed member-name/header order. The two exposed month-level scientific counts above are recorded and may not be used to change the panel, field mapping, density cap, method, or gates.

## Exact correction

Starting from the exact intermediate runtime source produced by the already-frozen Zenodo-link schema correction (SHA-256 `90d431819212e97adbc272acfa3c34595dac411f2bfe7c14a1a53535d789a01d`), remove exactly the physical-order assertion:

```python
if selected_months[year]:
    require(month > selected_months[year][-1], f"non-monotonic selected month order in {year}: {month}")
```

Keep unchanged:

- exact years `[2016, 2017]`;
- exact selected member-name regex `data/(2016|2017)/MM/kep_collect.h5`;
- duplicate year-month rejection;
- stop at first `data/2018/` header;
- every encountered selected 2016/2017 member is still used exactly once;
- event IDs still include the full archive member path and zero-based row index;
- blind-first HDF5 read order;
- geometry validity;
- 10,000/bin SHA-256-identity-only cap;
- fixed4/v6/v8 construction and rankings;
- N>=100 and Q>=30 floors;
- no-orbit/no-label/no-target boundary.

The physical processing order cannot enter final science because retained events are selected within each fixed 10° bin by stable SHA-256 event identity and the per-year event lists are subsequently sorted by stable event ID before v8 scanning.

The corrected run must additionally prove on a synthetic pre-data test that the identity-capped event set is invariant to input permutation.

This is a transparent ingestion/packaging correction after partial row-level access and before any method-level scientific outcome. It is not a claim that the MAARSY panel remained wholly untouched.