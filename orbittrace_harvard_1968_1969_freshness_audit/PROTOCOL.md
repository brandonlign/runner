# OrbitTrace v8 external validation — zero-data catalogue screen and Harvard 1968/1969 freshness audit

## Status
Frozen before any Harvard Radar Meteor Project / Steel Meteoroid Orbits scientific record is opened.

UKMON 2020/2021 remains scientifically unexposed but is unusable under both independently pre-frozen interface/transport rules. Preserve:
- first structure run `31225678351`, artifact `9012001791`: daily response shape incompatible before scientific-value access;
- transport-correction run `31225913104`, artifact `9012076689`: pre-existing daily→`0-6`,`6-12`,`12-18`,`18-24` fallback failed at the first 2020 period before scientific-value access.

No further UKMON 2020/2021 parser adaptation is allowed from target-year payloads.

## Zero-data catalogue screen
The external power gates remain unchanged: at least 100 recurrent families (`N >= 100`) and at least 30 orbitally corroborated families (`Q >= 30`). No lower floor is considered.

Candidate eligibility is evaluated from public catalogue metadata only, without downloading or opening scientific event tables:
1. individual meteor events/orbits rather than a shower-level aggregate;
2. at least two separable observing years;
3. event-level time/solar-longitude information plus radiant, speed, and orbital elements sufficient for the frozen discovery and post-ranking corroboration interfaces;
4. machine-readable public access suitable for deterministic GitHub Actions execution;
5. not already scientifically used/exposed in the OrbitTrace project;
6. one coherent survey/instrument panel, avoiding arbitrary mixtures of heterogeneous catalogues.

### Screened catalogue classes
- **CMOR:** scientifically attractive by scale (millions of measured individual orbits exist), but the public NASA/PDS stream-survey product exposes the detected shower catalogue/aggregate orbital parameters rather than the underlying individual event-orbit corpus. It therefore fails public event-level access for this one-shot validation.
- **Current IAU MDC high-volume catalogues:** GMN, CAMS, SonotaCo, EDMOND, SAAMER, and AMOR are already used/exposed or otherwise unavailable under the project history and are ineligible as a fresh panel.
- **DMS, Hissar, FRIPON, and current photographic collections:** public individual-orbit products exist but are materially smaller than the strongest remaining coherent two-year historical radar panel. They are not opened or cycled through here.
- **Steel / NASA PDS historical survey archive:** contains several coherent individual-orbit surveys with common fields. The strongest single natural two-year panel in the public metadata is the Harvard Radar Meteor Project 1968–1969 file `har6869.tab`, with 19,818 individual orbits from that survey.

## Single next candidate
Reserve **Harvard Radar Meteor Project 1968–1969 (`har6869.tab`)** as the one next external candidate.

Selection is metadata-only and fixed before any `har6869.tab` access. Do not switch to a different Steel sub-survey after seeing Harvard scientific values or detector performance. If Harvard is fresh, first perform a structure/interface audit that does not interpret radiant, speed, or orbital values; then freeze the full v8 scientific protocol before first scientific conversion.

## Full-history freshness audit
Search every remote branch ref in `brandonlign/runner` for evidence of prior Harvard/Steel candidate use using the fixed marker set:
- `har6869` / `har6869.tab`;
- `Harvard Radar Meteor Project`;
- `Harvard 1968-1969` / `Harvard 1968–1969`;
- `EAR-A-VARGBDET-5-METORB-V1.0`;
- `meteoroid.steel.orbits`;
- `Steel Meteoroid Orbits`;
- `Meteoroid Orbits V1.0`.

Exclude only this audit directory and its workflow from exposure evidence. Do not exclude generic project history.

Positive controls must prove that the same remote-history scan reaches known spent external-work branches for AMOR and UKMON.

## Freshness decision
- PASS only if there are zero prior Harvard/Steel candidate-use hits outside this audit and both positive controls are detected.
- FAIL on any candidate-use hit. Preserve all hit text/ref/path/line evidence.

This audit is repository-history-only. It must not contact NASA PDS, SBN, IAU MDC, Harvard data endpoints, or any meteor catalogue; it must not inspect scientific event values, source labels, or OrbitTrace target information.
