# Structure-audit correction — do not assume `.csv` member extension

The first SAAMER structure-only Actions run `31206393270` downloaded the official 2020 archive and failed before reading any member contents because the audit required a ZIP member whose name ended in `.csv`; the archive contains no such member.

This is a container-format assumption only. The corrected structure audit may:

1. enumerate non-directory ZIP members and their structural metadata;
2. require exactly one regular tabular member per annual archive regardless of filename extension;
3. read only the first record as the header, detect its delimiter, and scan later records only for row count/column-count consistency;
4. compare normalized header names against the MDC-documented required fields `LS`, `RA`, `DEC`, `Vg`, and `Sh`.

It may not inspect, convert, retain, compare, print, or use any post-header field value. No scientific score, shower-label value, target-region value, or OrbitTrace information may be accessed.
