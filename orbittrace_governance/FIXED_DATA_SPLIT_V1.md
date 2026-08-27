# OrbitTrace permanent train / test / validation split — v1

## Status

This governance freeze supersedes the previous pattern of successor-specific fresh-year reservations. It does **not** alter any already-frozen scientific method. It fixes dataset roles before final-test scientific access.

## 1. Permanent development / training corpus

**GMN 2022 + 2023**, with solar longitude **20°–55°** removed before any label, reservoir, fold, score, endpoint, diagnostic, or method-selection step.

All architecture design, feature selection, threshold selection, ablations, debugging, failure analysis, and successor selection occur on this same target-excluded GMN development corpus. No development failure authorizes consumption of a new benchmark year.

## 2. Permanent final matched literature test

**SonotaCo 2013 + 2014** is the single final matched literature-test panel.

This panel is reserved for one frozen final candidate only. Until that candidate and all comparison gates are frozen, the 2013/2014 scientific archives, known-shower truth, comparator cluster values, and method-performance outputs remain unopened.

The final test compares the frozen OrbitTrace candidate independently against frozen Sugar and catalogue-HDBSCAN implementations on pairwise matched event-row universes under the frozen information-parity, catalogue-burden, one-to-one-scoring, sparse/broad-superiority, uncertainty, integrity, and target-firewall rules.

No replacement year is allowed after any 2013/2014 scientific performance value is opened.

## 3. Permanent external validation endpoint

The single scored no-retuning external-generalization endpoint is **MAARSY 2022**.

Because the frozen #839 URC proposal architecture requires two distinct annual scans, its candidate-specific transport is allowed one mechanically fixed **unlabeled recurrence-support scan: MAARSY 2021**. This does **not** create a second validation endpoint:

- the detector input pair is fixed as ordered annual scans `(2021, 2022)`;
- 2021 is used only as label-free recurrence support required by the frozen hard/P19/P20 proposal mechanism;
- no 2021 shower truth, known-shower mapping, performance endpoint, selection statistic, or success criterion may be opened or computed;
- only 2022 member IDs are scored against 2022 truth for external validation;
- no detector parameter, feature, threshold, ranking, membership, support rule, recurrence rule, or success gate may be tuned from MAARSY data;
- no other MAARSY year may replace 2021 support or 2022 scoring because of an unfavorable result.

The support year is fixed pre-result because it is the immediately preceding annual scan in the same public near-continuous MAARSY survey, not because of any event-level or performance inspection. Public survey metadata establishes coverage across 2016–2024; no MAARSY event-level scientific value was used to choose this mapping.

A metadata/schema-only preflight may verify archive availability, field semantics, units, deterministic quality-cut implementability, target-exclusion implementability, and exact observable compatibility. It may not inspect event values, labels, detector scores, candidate outputs, target-region contents, or any method-performance result.

If the required 2021 support archive, 2022 scored archive, or required observable cannot be reproduced faithfully, the outcome is architecture incompatibility rather than permission to invent a pseudo-year, proxy, or replacement panel.

## 4. Exposed historical panels

SonotaCo 2023/2025 and all other scientifically exposed historical SonotaCo panels are diagnostic/history only. They may reproduce historical results but cannot select numerical settings, promote a successor, or replace the permanent 2013/2014 test.

The P18 SonotaCo 2023/2025 loss remains a permanent scientific no-go. The invalidated 2014/2016 reservation remains provenance/history only.

## 5. Fixed progression

1. Develop/select only on target-excluded GMN 2022/2023.
2. Freeze one final deployable candidate and all transport/evaluation rules.
3. Execute the SonotaCo 2013/2014 matched literature test once.
4. If and only if the required literature-superiority criterion passes, execute the exact frozen MAARSY `(2021 support, 2022 scored)` transport once with no retuning and no 2021 truth/performance access.
5. If and only if the scored MAARSY 2022 external-generalization requirement passes, proceed to the separately frozen blind OrbitTrace search.

A development failure never consumes a new test dataset.

## 6. Final-test conservation rule

The permanent SonotaCo test is not used to decide whether a development architecture is promising. Candidate selection must be made from GMN development robustness, mechanistic justification, and preregistered internal stress tests. This keeps the final literature comparison genuinely one-shot.

## 7. Target firewall

OrbitTrace target information remains inaccessible. The solar-longitude interval **20°–55°** remains excluded throughout development, literature testing, and external validation until final blind-search authorization is earned.
