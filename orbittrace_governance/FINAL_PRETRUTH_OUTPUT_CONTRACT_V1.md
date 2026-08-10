# OrbitTrace final literature-test pretruth output contract — v1

## Purpose

Freeze the exact information boundary between final candidate/comparator execution and known-shower evaluation before SonotaCo 2013/2014 scientific access.

This contract does not alter M0, Sugar, HDBSCAN, candidate budgets, one-to-one scoring, or superiority gates. It ensures that known-shower truth cannot influence family generation, membership, ranking, suppression, candidate budgeting, or output selection.

## Stage 1 — shared retained-row manifests

For each final-test year and each pairwise comparator universe, construct the exact pretruth retained-row manifest under the frozen SonotaCo shared parser and pairwise structural eligibility rules.

Every manifest record contains only stable event ID plus allowed raw observables. It contains no shower label, native shower/background designation, target identity, comparator assignment, method score, or post-output truth field.

The manifest is canonicalized in stable event-ID order and SHA-256 hashed before any detector executes.

## Stage 2 — independent frozen outputs

M0, Sugar, and catalogue HDBSCAN execute independently from the appropriate pretruth manifest. Each method must produce one canonical primary output JSON containing:

- `method_id`;
- `year_pair` or single-year scope where appropriate;
- input manifest SHA-256;
- scientific source/configuration SHA-256 values;
- ordered primary families;
- for every family: stable `family_id`, exact sorted member event IDs, and final primary rank;
- method-native score(s) needed only to reproduce that frozen order;
- explicit `truth_accessed=false` and `target_information_accessed=false` integrity fields.

For M0 the family source class (`hard`, `p19`, `p20`) is also recorded. Original generator membership is the only final membership.

For Sugar/HDBSCAN, family IDs are deterministic implementation-generated identifiers and membership is the exact primary clustering output before truth.

No output may include a known-shower label, best-match label, shower-code mapping, truth-derived quality statistic, post-truth family filter, or manually selected family subset.

## Stage 3 — canonical output freeze

Before truth is opened:

1. sort all member IDs within every family;
2. preserve family order exactly as emitted by the frozen method;
3. serialize JSON with sorted object keys, UTF-8, no NaN/Infinity, compact separators `(',', ':')`, and a final newline;
4. compute SHA-256 of the exact bytes;
5. preserve the complete output, not merely the budget-truncated subset;
6. write a separate pretruth provenance record containing input/source/output hashes and environment identifiers.

The candidate budget `B` for each comparator/year is derived only from these frozen outputs under the already-frozen final literature policy. No truth is needed to compute `B`.

## Truth-release gate

Known-shower truth may be loaded by the final evaluator only after all required pretruth hashes exist for BOTH 2013 and 2014 for:

- M0-vs-Sugar pairwise manifests and both method outputs;
- M0-vs-HDBSCAN pairwise manifests and both method outputs.

The evaluator must verify all hashes before loading truth. A missing/mismatched hash returns `INVALID_FINAL_LITERATURE_TEST_INTEGRITY` and cannot trigger a scientific rerun with altered method output.

## Immutability after truth release

After truth is opened, none of the following may change:

- retained event rows;
- pairwise structural eligibility;
- family generation;
- family membership;
- family ranking;
- family suppression/merging;
- candidate budget;
- method source/configuration;
- output serialization or hash.

Only the frozen evaluator may map output member IDs to known-shower truth and compute the preregistered assignment/metrics/bootstrap.

## Target firewall

Solar longitude 20°–55° is removed upstream by the frozen shared normalizer before any non-solar scientific field is decoded. No target-specific coordinate, identity, member set, historical recovery, or exception may enter any pretruth output stage.

## Activation boundary

This contract is infrastructure only. It does not authorize SonotaCo 2013/2014 access. Final-test access requires the exact M0 generator/ranker transport, exact comparator adapters, and the integrated candidate/comparator execution source to be source-audited and explicitly declared `FINAL_FOR_LITERATURE_TEST` first.
