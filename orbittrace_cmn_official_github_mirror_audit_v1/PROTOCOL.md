# OrbitTrace official CMN GitHub mirror structure audit v1

## Status

Frozen before reading the committed CMN downloads-page HTML or any CMN catalogue data blob from the official `CroatianMeteorNetwork/CMN-codes` GitHub repository.

Prerequisites already preserved in the OrbitTrace lineage:

- `PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT`;
- binding IAU landing-route structure FAIL;
- documented `cmn.rgn.hr` route blocked before HTTP by repeated DNS failure on unchanged frozen executions.

The official CroatianMeteorNetwork GitHub organization was identified independently of those failures. Its public `CMN-codes` repository contains a committed mirror path `CMN website/downloads/downloads.html`. This audit pins the official repository to exact commit `2077285b66b6fd8df633ff0aec5ef0af0bf24ef6` (2018-01-15) and uses repository structure only.

## Frozen source access

Allowed source:

- repository: `CroatianMeteorNetwork/CMN-codes`;
- commit: `2077285b66b6fd8df633ff0aec5ef0af0bf24ef6`;
- HTML blob path: `CMN website/downloads/downloads.html`.

The audit may:

1. obtain the exact pinned Git commit/tree metadata;
2. read exactly the single downloads-page HTML blob;
3. inspect Git tree metadata (paths, object types, blob SHAs) at that same commit to determine whether links from the page resolve to committed repository objects.

The audit must not read any candidate catalogue/data blob contents.

## Independently fixed orbit-section cue

Published CMN-related literature cites the historical downloads page with fragment `#orbitcat`. Before the mirrored page is read, `orbitcat` is therefore fixed as the orbit-catalogue structural cue.

The page must contain an HTML element with `id="orbitcat"` or `name="orbitcat"` (case-insensitive). Candidate orbit links are hyperlinks encountered after that cue and before the next named/id anchor or heading at the same-or-higher HTML heading level, when such a boundary exists. In addition, a candidate hyperlink must contain the token `orbit` in either its visible link text or href path, case-insensitive. This dual condition prevents unrelated software downloads from being counted as orbit catalogues.

## Frozen candidate formats and repository resolution

Candidate file extensions are fixed before inspection to archival/tabular formats:

`zip`, `csv`, `txt`, `dat`, `xls`, `xlsx`, `rar`, `7z`, `gz`, `bz2`.

For each candidate link:

- query strings/fragments are discarded;
- only relative links or links whose hostname is `cmn.rgn.hr` are eligible;
- the historical site URL path is mapped to the mirror repository under prefix `CMN website`;
- repository existence is tested only from the pinned Git tree metadata;
- candidate blob content is never read.

The artifact may report only:

- downloads-page HTML blob SHA-256 and Git blob SHA;
- whether the `orbitcat` cue exists;
- total structural candidate-link count;
- extension-frequency counts;
- number resolving to committed blobs in the pinned official repository;
- for the deterministically selected resolved candidate: SHA-256 of the normalized repository path and its Git blob SHA only.

It must not emit raw HTML, link text, filenames, normalized paths, catalogue rows, event identifiers, shower labels, orbit/radiant/velocity values, or other scientific record values.

## Frozen deterministic selection

If one or more candidate links resolve to committed blobs, sort their normalized repository paths by UTF-8 byte order and select the first. The path itself must not be emitted. Only its SHA-256 and exact Git blob SHA are recorded. There is no post-result candidate choice.

## Frozen gate

`PASS_CMN_OFFICIAL_GITHUB_MIRROR_STRUCTURE_AUDIT` requires all of:

1. exact official repository and commit pins reproduce;
2. exact mirrored downloads-page blob is readable;
3. `orbitcat` structural cue is present;
4. at least one candidate orbit link satisfies the frozen link/extension rules;
5. at least one such candidate resolves to a committed Git blob at the pinned commit;
6. a deterministic selected-candidate path hash and blob SHA are produced;
7. no candidate catalogue/data blob content is read;
8. no CMN event-level scientific value is emitted or inspected.

Failure closes this exact official-GitHub-mirror structure route. No alternate path, commit, extension set, section cue, or link filter may be chosen from the result.

A PASS authorizes only a separately frozen minimal format/header compatibility audit of the exact deterministically selected blob. That later audit must freeze byte limits and permitted header/schema fields before reading any selected-blob bytes. PASS here is not scientific validation and not evidence of a better detector.

## Firewall

- CMN candidate catalogue blob contents read: false.
- CMN scientific/event-level access: false.
- OrbitTrace target information/events: inaccessible.
- protected 20°–55° events: inaccessible.
- SonotaCo scientific access: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- external validation performed: false.
