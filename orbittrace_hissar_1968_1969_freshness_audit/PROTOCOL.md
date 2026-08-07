# OrbitTrace v8 external validation — Hissar 1968/1969 zero-data freshness audit

## Status
Frozen before any Hissar meteor row is requested, downloaded, rendered, or inspected.

## Why this is the single next candidate
The external power floors remain unchanged: at least 100 recurrent families (`N >= 100`) and at least 30 orbitally corroborated families (`Q >= 30`). No lower floor is admissible.

The previous deliberate fallback, Harvard Radar Meteor Project 1968–1969, passed repository freshness but failed the frozen-v8 interface adjudication before its event table was opened: run `31227365630`, artifact `9012563055`, verdict `FAIL_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY`. Its official interface contains observed B1950 radiant/VINF rather than the exact geocentric radiant/Vg required by v8.

The current IAU Meteor Data Center Version 2026 metadata identifies a coherent Hissar/Hisar radio-meteor sample of 8,916 individual orbits spanning 1968-12-12.73530 through 1969-12-24.18900. Its radio-catalog interface exposes solar longitude (`LS`), geocentric radiant coordinates (`RA`,`DEC`), geocentric velocity (`Vg`), and orbital elements (`q`,`e`,`i`,`arg`,`nod`). These are natively compatible in kind with the frozen v8 discovery/post-ranking interfaces, unlike Harvard.

The span is strongly imbalanced: 1968 contributes only its final ~19 days, so the possible cross-year recurrence support is prospectively narrow. That is a known power risk, not grounds to lower `N >= 100` or `Q >= 30` after access.

CAMS cannot supply a fresh adjacent pair: repository history already establishes 2016 scientific exposure, while CAMSv3 ends at 2016. SAAMER/AMOR are spent; GMN/SonotaCo/EDMOND are used/exposed; DMS and the full photographic collection are materially smaller. Hissar is therefore frozen as the final serious architecture-compatible external candidate rather than cycling through many small panels.

## Zero-data full-history audit
Search every remote branch ref in `brandonlign/runner` for evidence of prior Hissar/Hisar/Dushanbe scientific use using this fixed marker set:
- `Hissar` / `HISSAR` / `Hisar`;
- `Dushanbe`;
- `Tajikistan` when appearing in meteor/radio-catalog context;
- `Narziev`;
- `8916 radio-meteor` / `8,916 radio-meteor`;
- `1968-1969 sample of HISSAR`;
- `1968-1969 sample of Hissar`.

Exclude only this audit directory and its workflow. Do not exclude generic project history.

Positive controls must prove the same remote-history scan reaches known prior external work for AMOR, UKMON, and Harvard.

## Freshness decision
- `PASS_HISSAR_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT`: zero candidate-use hits and all positive controls detected.
- `FAIL_HISSAR_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT`: any candidate-use hit, or a missing positive control.

Preserve every hit with ref/path/line/text. A FAIL is terminal for Hissar as an independent panel.

## Hard boundary
This audit is repository-history-only. It must not contact the IAU MDC, submit the radio-catalog form, download/render Hissar rows, inspect scientific values or source labels, run v8, access the excluded 20°–55° contents, or access OrbitTrace target information.

A PASS authorizes only a separately frozen pre-scientific structure/interface audit.
