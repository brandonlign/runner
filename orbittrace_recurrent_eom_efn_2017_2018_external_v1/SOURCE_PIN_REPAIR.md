# EFN recurrent-EOM protocol source-pin repair record

**Classification: engineering-only preaccess correction; no scientific result and no EFN event-row access.**

The original EFN 2017/2018 protocol was frozen at commit `fb2f3bd14149f0fdccb128d406d87b89bf336dcd` before any EFN event-level query.

A subsequent source review, still before any EFN event row was queried or opened, found one transcription error in the protocol's promoted recurrent-EOM implementation Git-blob identity:

- incorrectly transcribed in original protocol: `30ac3fa3bc47910370df5282258e3d1429fbe00d67`
- authoritative promoted method blob from PR #1243 / the recurrent-EOM source: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

The two strings are not alternative methods. The first does not identify the promoted recurrent-EOM source and arose from accidental mixing with the unrelated AMOS adapter transform blob. The scientific method definition, constants, representation, recurrent-stability rule, ranking, evaluator, panel, years, native EFN field mapping, firewall, and validation gate are unchanged.

Authorized correction: replace only that malformed method-blob string in `PROTOCOL.md` with the authoritative promoted method blob above. No other protocol text or scientific commitment is authorized to change in the repair.

At the time this repair was recorded:

- `efn_event_rows_accessed=false`
- `efn_geometry_accessed=false`
- `efn_shower_labels_accessed=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `orbittrace_target_access=false`
