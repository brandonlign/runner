# OrbitTrace support-cut × bifiltration bridge v1 — binding zero-label result

## Verdict
`FAIL_SUPPORT_CUT_BIFILTRATION_BRIDGE_V1_STRUCTURAL` — closed before truth.

Binding workflow run: `32041289389`
Binding job: `95420936672`
Binding artifact: `9292005125`
Artifact digest: `sha256:5c93de5c9b42f66d727414454c6cfa80c50f5b2375a0b1da147812d8a8f21304`
Execution commit: `1349e3d54a253a462e7c3a80c1c338336130f869`
Support-cut prelabel SHA-256: `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6`
Bifiltration prelabel SHA-256: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`

No shower truth, OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS were accessed.

## Exact-membership overlap

| subset | support-cut candidates | exact bifiltration matches | recurrent budget K |
|---|---:|---:|---:|
| d=128,b=0 | 69 | 19 | 29 |
| d=128,b=1 | 80 | 18 | 35 |
| d=128,b=2 | 79 | 18 | 38 |
| d=128,b=3 | 70 | 11 | 33 |
| d=1024,b=0 | 9 | 0 | 8 |
| d=1024,b=1 | 6 | 1 | 5 |
| d=1024,b=2 | 6 | 2 | 6 |
| d=1024,b=3 | 9 | 5 | 9 |

Exact-match capacity fails in every panel. Fine d=1024,b=0 has zero exact matches.

Cross-scale mean best-Jaccard is `0.21875` for the bridge versus `0.6183584075451847` for recurrent-EOM, with `0/4` buckets nonlower.

The pairwise-disjoint property is retained, but the exact bridge is far too sparse to constitute a catalogue.

## Closure
Do not rescue this architecture with approximate Jaccard/overlap matching, nearest-neighbor matching, containment substitution, modal-contrast fallback, score blending, quotas, or relaxed gates. A distinct successor may use the two-density bifiltration as an integrated evidence field evaluated directly on the already-frozen support-resolved candidate memberships, without cross-generator candidate matching.