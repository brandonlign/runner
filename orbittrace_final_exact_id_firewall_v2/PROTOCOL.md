# OrbitTrace final exact-ID blind reveal firewall v2

## Purpose

Freeze the target-reveal semantics **before** any candidate method is authorized for final OrbitTrace application.

This firewall is detector-agnostic. A winning method must first produce and durably hash-freeze a ranked family catalogue on the target-containing discovery corpus without access to the withheld OrbitTrace reference. Only then may a separate reveal stage read the withheld reference, and only exact stable event IDs may be used to determine recovery.

No OrbitTrace coordinates, radiants, velocities, orbital elements, activity profile, canonical name/identity, previously observed detector rank, or nearest-neighbor target search may enter Stage A.

## Discovery corpus

The final Stage-A corpus is fixed to **GMN 2022 and 2023**.

Reason for this choice is architectural, not target-based:

- the current development/fallback method family is built around a frozen two-year recurrence architecture;
- 2022/2023 are the exact development years outside the withheld 20°–55° target interval, so opening that interval after complete method selection is a geographic/activity-region holdout rather than a year-selection optimization;
- fixing the same two years avoids choosing a supposedly favorable target year after reveal.

Stage A uses the complete geometrically valid 2022/2023 corpus, including the previously inaccessible 20°–55° interval. The winning detector must not use catalogue shower labels or the withheld OrbitTrace reference while generating or ranking families.

## Stage A: independent discovery

The selected and externally validated method is run exactly once on the full 2022/2023 discovery corpus.

Before any withheld target-reference access, Stage A must serialize and SHA-256 freeze:

- the exact winning method/source identity and its prerequisite PASS artifacts;
- the exact discovery input identities;
- the complete primary ranked family order;
- every primary family's stable event-ID set;
- every primary family's per-year stable event-ID sets;
- family rank and recurrence years;
- any method-specific score fields needed to prove the ranking was produced by the frozen method;
- a statement that the withheld target reference was unavailable to the process.

The primary ranking is the only ranking eligible for the final claim. Rescue/diagnostic channels may be serialized but cannot independently satisfy recovery.

No known-shower truth evaluation is required for Stage A. No target-reference artifact may be downloaded, mounted, queried, hashed, or named in the Stage-A job.

## Stage B: exact-ID reveal only

Stage B starts only from the immutable Stage-A artifact.

It may access a withheld OrbitTrace reference containing only:

- exact stable event IDs;
- the year associated with each exact ID;
- provenance/hash information required to verify the withheld artifact.

Stage B must reject any target-reference payload containing coordinates, radiants, velocities, orbital elements, activity bounds, model parameters, detector scores, or a suggested family/rank.

For each frozen Stage-A primary family, Stage B computes exact set intersection between the family's event IDs and the withheld target event IDs. Zero fuzzy matching is allowed.

No D-criterion, radiant distance, orbital distance, time/activity proximity, nearest-neighbor search, clustering, family merging, member expansion, or reranking may occur after the target reference becomes visible.

## Frozen recovery criteria

The thresholds below are derived from the detector architecture and its already-used top-K discovery scale, not from target counts.

The two-year recurrent catalogue requires at least four-event same-year component support. Therefore a family must contain at least **4 exact withheld target IDs in each of 2022 and 2023** to count as an OrbitTrace recovery. This automatically requires at least 8 exact target IDs total.

### Full blind recovery

`FULL_BLIND_RECOVERY` iff at least one frozen primary family satisfies all of:

- rank <= 25;
- recurrence years exactly include both 2022 and 2023;
- exact withheld-target overlap in 2022 >= 4 IDs;
- exact withheld-target overlap in 2023 >= 4 IDs;
- total exact withheld-target overlap >= 8 IDs.

### Partial blind recovery

If no family satisfies full recovery, `PARTIAL_BLIND_RECOVERY` iff at least one frozen primary family satisfies all of:

- rank <= 100;
- recurrence years exactly include both 2022 and 2023;
- exact withheld-target overlap in 2022 >= 4 IDs;
- exact withheld-target overlap in 2023 >= 4 IDs;
- total exact withheld-target overlap >= 8 IDs.

### No recovery

Otherwise the verdict is `NO_BLIND_RECOVERY`.

If multiple families satisfy a criterion, the reported family is the lowest-rank qualifying family. All qualifying families and exact overlap counts must still be serialized for audit.

## Authorization gate

Stage A cannot execute until the promoted method has passed, without retuning, **all** of the following:

1. its frozen target-excluded development gate;
2. a frozen exact-row pairwise matched literature comparison whose final classification is `BROAD_CATALOGUE_SUPERIORITY` or `SPARSE_STREAM_SUPERIORITY` against the required Sugar/HDBSCAN panels;
3. a separately frozen prospective or external generalization gate whose event-level scientific values were not used to tune the promoted method.

For v6-LF specifically, item 3 is the pristine MAARSY 2018/2019 cross-survey validation frozen in PR #589 and requires exact verdict `PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION`. Either MAARSY power-inconclusive verdict or a scientific/integrity FAIL does not authorize Stage A even if development and literature pass.

The earlier proposed GMN 2024/2025 prospective holdout is explicitly invalid as an authorization source. Repository history showed that target-excluded 2024/2025 scientific values, known-shower labels and F1 endpoints were already consumed in PR #453 / run `31235104333`. It may be cited only as historical transfer/development evidence, never as the independent generalization gate.

For a later successor, its separately preregistered external/generalization gate may substitute for item 3 only if that gate was frozen before its result and the corresponding data remained scientifically unexposed to method tuning. A matched literature panel cannot silently double-count as the independent generalization gate unless that dual role was explicitly preregistered before either result.

Because pristine external panels are scarce, the active method chain owns an external panel only after it passes its literature gate. If an earlier method fails before external activation, the unopened panel remains available to the next preregistered successor; an inactive predecessor need not consume it merely to satisfy routing paperwork.

Any Stage-A execution wrapper must verify the exact prerequisite artifacts and method identity before the first target-region discovery row is accessed; marker text alone is insufficient authorization.

## Claim boundary

A full/partial verdict establishes that a frozen target-free method independently placed a family containing substantial exact withheld OrbitTrace membership within its top-25/top-100 primary discoveries.

It does not prove that every canonical target member belongs to the discovered family, nor that the target is dynamically distinct from every known stream. Those are separate scientific interpretation questions.

The firewall itself must never be modified in response to a Stage-A rank, Stage-B overlap, or target identity.
