# EDMOND 2009/2010 — repository-history freshness audit v2

## Status

Frozen before any EDMOND 2009 or 2010 event-level scientific value is requested or opened by this branch.

This is a **metadata/provenance audit only**. It may inspect Git repository history plus GitHub Actions run/artifact metadata for `brandonlign/runner`. It must not request an EDMOND archive, event catalogue, scientific table, mirror payload, or any other external meteor-event data.

The protected OrbitTrace interval `[20.0,55.0]`, OrbitTrace target information/events, SonotaCo scientific values, AMOS scientific values, EFN scientific values, MAARSY, and DMS are outside this audit.

## Question

Were EDMOND calendar years 2009 and/or 2010 already scientifically exposed anywhere in the OrbitTrace repository lineage, such that they cannot now serve as genuinely untouched external-validation years for promoted recurrent-EOM HDBSCAN v1?

## Binding definition of prior scientific exposure

A year counts as **scientifically exposed** only if repository/GitHub evidence establishes that an earlier OrbitTrace execution actually obtained or interpreted event-level scientific content from that exact EDMOND year. Examples include:

- an immutable result/provenance record stating that 2009 or 2010 event rows were downloaded/opened/parsed;
- a successful GitHub Actions run/artifact explicitly recording a scientific EDMOND 2009/2010 execution rather than only a route, source, format, freshness, or transport audit;
- persisted event counts, candidate counts, scientific metrics, hashes of opened 2009/2010 event tables, or other values that could only have resulted from opening those event rows;
- a preserved code/result combination unambiguously documenting that a scientific 2009/2010 endpoint completed.

The following **do not by themselves count as exposure**:

- mentioning EDMOND, 2009, or 2010 in a protocol, comment, source URL, citation, or planned-year list;
- constructing an unrequested URL/path for one of those years;
- metadata-only HTTP status/header/size checks that never open scientific table content;
- a format/schema audit using documentation or another already-exposed year;
- a failed/technical workflow that stops before event-row access;
- source code capable of accessing the year when no evidence establishes that the access actually completed.

If evidence is ambiguous, the audit must return **AMBIGUOUS / DO NOT ACCESS**, not infer freshness.

## Evidence universe

The audit must inventory, without contacting EDMOND:

1. every reachable Git branch/ref and commit available from the repository remote;
2. file paths, patches, and file contents containing `EDMOND` together with `2009` or `2010`, including deleted/renamed historical files reachable from refs;
3. GitHub Actions run metadata whose workflow name or head branch contains `edmond`;
4. artifact metadata for those EDMOND-related workflow runs;
5. the known failed metadata-only freshness run `31205646997` as a specific control.

The audit may use the GitHub API only for repository/Actions metadata. It must not download historical scientific artifacts automatically; if artifact metadata suggests a potentially scientific exact-year execution, the result must flag that run for separate adjudication before any artifact contents are opened.

## Output boundary

The first audit produces an **evidence inventory**, not an automatic freshness claim. It must record:

- matching Git refs/commits/files/snippets;
- matching Actions run IDs, names, branches, conclusions, dates;
- artifact IDs/names for matching runs;
- exact-year exposure candidates requiring adjudication;
- confirmation that no EDMOND external scientific URL was contacted.

Allowed inventory verdicts:

- `PASS_EDMOND_2009_2010_FRESHNESS_INVENTORY_NO_EXPOSURE_CANDIDATE` — no evidence even potentially indicates completed exact-year scientific access;
- `REVIEW_EDMOND_2009_2010_FRESHNESS_EXPOSURE_CANDIDATES` — one or more exact-year records need human/source adjudication;
- `FAIL_EDMOND_2009_2010_FRESHNESS_AUDIT_TECHNICAL` — audit could not cover the required repository/Actions metadata universe.

Even a PASS inventory **does not authorize EDMOND event access**. A separate evidence adjudication/result must freeze the final freshness status before any external archive route is contacted.

## Scientific firewall

Every output must assert:

- `event_level_edmond_access=false`;
- `external_edmond_request_made=false`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `sonotaco_scientific_access=false`;
- `amos_scientific_access=false`;
- `efn_scientific_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`.
