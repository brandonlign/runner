# EFN 2017/2018 preaccess source-pin correction

**Status: PREACCESS ENGINEERING CORRECTION ONLY. Scientific method unchanged. No EFN event row accessed before this correction.**

The initial frozen `PROTOCOL.md` contains a transcription error in one provenance line:

- malformed text in initial protocol: `30ac3fa3bc47910370df5282258e3d1429fbe00d67`
- authoritative promoted recurrent-EOM implementation blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

The authoritative value is independently fixed by the already-promoted recurrent-EOM lineage and the SonotaCo 4/4 superiority benchmark. This correction changes no code, method, representation, HDBSCAN parameter, recurrent-stability formula, ranking rule, evaluator, gate, year, EFN field mapping, or firewall rule.

This record is committed before any EFN event-level query or download. All subsequent EFN source audits and execution must require the authoritative blob:

`orbittrace_recurrent_eom_hdbscan_v1/recurrent_eom.py` -> Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

If the repository file does not match that exact blob at execution, the EFN run is a technical no-result.

The malformed protocol value is permanently preserved as a preaccess transcription mistake and must never be treated as an alternate implementation choice.
