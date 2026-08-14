# CMN freshness reconciliation for recurrent-EOM external validation

**Classification: NEUTRAL — pristine-survey claim compromised; main catalogue remains unopened under current CMN routes.**

This adjudication corrects the claim boundary of the earlier CMN zero-data freshness audit before any new CMN catalogue access for recurrent-EOM HDBSCAN v1.

## 1. Earlier zero-data audit

PR #1224 reported `PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT` from binding run `31636537011`, artifact `9157162439`, digest `sha256:c18a950dd58fb32b0883ea238e822da284ab25daf33efc3294810eda50722b04`.

Its audit implementation searched repository history for the following fixed indicators:

- `Croatian Meteor Network`
- `CroatianMeteorNetwork`
- `CMN Orbit`
- `CMN_Orbit`
- `CMN-Orbit`
- `cmn.rgn.hr`

and required FRIPON/UKMON history as positive controls.

That audit did **not** search the generic source identifier `CMN` used by the IAU MDC shower lookup tables. Consequently, its PASS establishes only that the fixed long-form CMN indicators were absent from the scanned history; it does not establish that no CMN-sourced meteor value had ever been scientifically processed.

## 2. Binding prior CMN scientific exposure

Earlier NOP solution-004 provenance/orbit work used exact IAU MDC lookup artifact:

- source artifact `8874489453`, `nop-solution004-provenance-audit`;
- source artifact digest `sha256:85ab59ef342afc2723ad1642426433d2dedf020abe17caf36815c096b098c6be`;
- source workflow run `30861480131`;
- selected lookup file `0149NOP_004.csv`;
- 567 total NOP solution-004 meteor rows.

The preserved CSV source column (`Sode`, normalized by the reconstruction source to `source`) contains:

- CAMS: 382 rows
- EDMOND: 75 rows
- SonotaCo: 60 rows
- GMN: 35 rows
- **CMN: 15 rows**

The 15 CMN rows contain scientific event values including observation timestamp, radiant coordinates, geocentric velocity `Vg`, and solar longitude. They are dated in May–June 2016.

These rows were not merely downloaded incidentally. PRs #24 and #25 scientifically processed them in source-specific diagnostics and orbit reconstruction. PR #25 explicitly reports the CMN subgroup in the frozen timestamp-reconciliation summary (`CMN: n=15`). Therefore `CMN scientific/event-level access=false` is not globally true for the complete historical OrbitTrace project.

## 3. Dataset-level interpretation

The NOP lookup is a shower-specific IAU MDC lookup assembled from multiple source databases. The evidence above proves **CMN-sourced event exposure**, but it does not by itself prove that the complete historical CMN orbit-catalogue object intended by PRs #1224–#1227 was downloaded or exhaustively inspected.

Conversely, without an independently frozen identifier-level disjointness proof, it is not scientifically defensible to claim that a future CMN catalogue is a wholly pristine survey relative to OrbitTrace. The exposed 15 rows could be members of the same underlying CMN catalogue family. Proving overlap/non-overlap by opening a candidate catalogue after this discovery would itself consume scientific event-level information and cannot retroactively restore a pristine-survey claim.

Thus the corrected distinction is:

- **complete CMN catalogue access under PRs #1224–#1227:** not achieved;
- **any CMN scientific/event-level exposure anywhere in OrbitTrace history:** yes, at least 15 rows;
- **wholly pristine CMN survey claim:** not supported.

## 4. Current CMN access routes remain closed/blockaded

The later CMN interface audits did not read a candidate catalogue blob:

1. PR #1225 — `FAIL_CMN_PUBLIC_INTERFACE_STRUCTURE_AUDIT`: official IAU landing returned an empty page under the frozen one-request route; no links/forms/scientific values were followed.
2. PR #1226 — `BLOCKED_CMN_DOCUMENTED_INTERFACE_DNS_UNRESOLVED`: independently documented `cmn.rgn.hr` host failed DNS before HTTP on two frozen attempts; no object was downloaded.
3. PR #1227 — `FAIL_CMN_OFFICIAL_GITHUB_MIRROR_STRUCTURE_AUDIT`: official `CroatianMeteorNetwork/CMN-codes` mirror exposed the historical `orbitcat` section cue but zero qualifying committed catalogue objects under the frozen candidate rule; no candidate blob content was read.

Those exact routes remain closed. Do not rescue them by URL guessing, crawling neighboring paths, broadening extension filters, changing the mirror section cue, or manually choosing a file based on the failed outcomes.

## 5. Binding consequence for recurrent-EOM

Verdict:

`DEFER_CMN_RECURRENT_EOM_PRISTINE_VALIDATION_FRESHNESS_COMPROMISED_AND_ACCESS_UNAVAILABLE`

CMN is **not authorized as a pristine external-validation panel** for recurrent-EOM v1.

This is scientifically neutral with respect to recurrent-EOM performance: no new CMN catalogue was run through the detector and no detector result was obtained.

A future CMN use could only be described under a weaker, explicitly exposed/partially exposed role unless a genuinely independent dataset version with pre-established disjoint provenance becomes available. Such a route would require a new protocol frozen before scientific contact; it cannot rehabilitate the current CMN archive as pristine validation.

## 6. Corrected status of PR #1224

Do not erase or rewrite the historical PASS. Preserve it as an accurate outcome of its **specified fixed-pattern audit**, but narrow its interpretation:

`PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT` means the preregistered long-form indicators were absent and the audit itself made zero CMN data contact. It does **not** prove zero historical exposure to rows carrying the abbreviated source code `CMN`.

## Firewall

No new CMN catalogue event row was contacted in this reconciliation.

- `new_cmn_catalogue_access=false`
- `new_cmn_scientific_value_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- protected solar longitude `[20°,55°]` remains inaccessible.
