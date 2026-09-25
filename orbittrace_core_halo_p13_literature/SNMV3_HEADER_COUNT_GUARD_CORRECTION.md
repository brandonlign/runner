# SNMv3 exact-orbit reader header-count guard correction

Status: **technical/pretruth schema compatibility correction only**. No P13 core/halo checkpoint, comparator cluster value, known-shower truth, external value, or target-region value existed when this correction was frozen.

In matched continuation workflow `31323952130`, the complete comparator ID-only manifest reproduced exactly, the corrected four panel/year split manifests froze, and both exact raw SNMv3 archive SHA256 checks passed. The first call to immutable reader `d8e58697812bbc93cbd204eb5ebbd6c98d0f3c0d:orbittrace_crossyear_two_view_membership_p2_literature/read_exact_orbits.py` then stopped immediately after reading the 2023 CSV header because `EXPECTED_HEADER_COUNTS[2023]=46` but the already-hash-pinned archive header has length 45. The reader had not yet iterated any requested orbit row.

The exact reader already contains stronger scientific/schema invariants independent of total header length:
- exact archive SHA256 per year;
- exact archive member path per year;
- exact requested event-ID/year/index mapping;
- exact normalized required field names at fixed indices for solar longitude, radiant, speed, q, e, peri, node, inclination and shower;
- exact q/e/peri/node/inclination numeric indices;
- finite/physical orbit checks;
- solar-longitude 20°–55° exclusion on every requested orbit row;
- exact requested-ID completeness/count equality.

Therefore the total-column-count equality is redundant metadata for these exact byte-pinned archives and can reject a schema that still preserves every field actually consumed by the frozen benchmark.

The sole permitted repair is:
1. materialize the original immutable reader and verify its Git blob is exactly `2accb52e550da95b9855038ed68304b05c747c92` before modification;
2. replace exactly once
   `require(len(header)==EXPECTED_HEADER_COUNTS[year],f'SNMv3 header count changed {year}: {len(header)}')`
   with
   `require(len(header)>max(EXPECTED_SHARED_INDICES.values()),f'SNMv3 header too short for required pinned fields {year}: {len(header)}')`;
3. leave every subsequent normalized field-name/index assertion and every orbit/event/firewall rule byte-for-byte unchanged;
4. perform no alternate column mapping, header-name search, fallback index, survey-specific reinterpretation, or scientific parameter change.

This correction is eligible only as a continuation of the already-frozen P13 matched experiment. If any required field-name/index assertion fails afterward, the benchmark remains technically incompatible and must stop rather than infer a new mapping.

No target information is authorized; solar longitude 20°–55° remains inaccessible.
