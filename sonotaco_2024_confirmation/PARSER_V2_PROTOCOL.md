# SonotaCo 2024 confirmation feasibility: frozen parser-v2 protocol

Status: frozen before parser-v2 reads the official 2024 annual archive.

## Separation from parser v1

PR #62 remains killed as `KILL_SONOTACO_2024_CONFIRMATION_PARSER_V1`. Its data-only audit established, without inspecting any data-column value or shower token, two deterministic interface differences in the official 2024 CSV:

1. the header has one final blank field while every nonempty record has exactly one fewer field;
2. required geometry columns use unit-bearing normalized names (`soldeg`, `radeg`, `dedeg`, `vgkms`).

Parser v2 changes exactly those two structural rules. It does not reinterpret parser v1 as a pass.

## Frozen source

- URL: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/024a.zip`;
- required member basename: `_U2_20240101_S.csv`;
- encoding candidates, delimiter candidates, archive safety checks, CRC check, and record-count range 30,000–50,000 remain unchanged;
- no data-column value, shower token, token frequency, feature distribution, support count, score, comparator, or scientific endpoint may be retained or summarized.

## Exact parser-v2 changes

1. After reading the header and all nonempty rows, remove the final header field only when:
   - the final header cell is blank;
   - every nonempty data row has exactly `len(header) - 1` fields.
   No other width correction, row padding, truncation, or malformed-row exception is allowed.
2. Required semantic fields are accepted only through the exact normalized aliases:
   - solar longitude: existing aliases plus `soldeg`;
   - radiant right ascension: existing aliases plus `radeg`;
   - radiant declination: existing aliases plus `dedeg`;
   - geocentric speed: existing aliases plus `vgkms`.

## Frozen gates

Every gate must pass:

1. nonempty archive;
2. safe member paths and no CRC failure;
3. exactly one required annual member;
4. 30,000–50,000 records;
5. frozen encoding and delimiter;
6. parser-v2 trailing-header rule applied exactly once;
7. at least 40 unique nonempty effective header fields;
8. zero malformed rows after the single allowed header correction;
9. required geometry and shower headers present through the fixed alias sets;
10. reported uncertainty header present.

A pass authorizes only a separately frozen aggregate-only survey-native label-token audit for SonotaCo 2025 development and a later exact 2024 confirmation gate. It does not authorize score computation, GhostStream use, or a catalogue scan.

Any failure kills parser v2 without changing the URL, member, width rule, aliases, record limits, encoding, delimiter, or gates.
