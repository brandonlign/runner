# Four-observer confirmation v1 — binding result

🔴 `FAIL_GMN_V31_FOUR_OBSERVER_CONFIRMATION_V1`.

First technically valid scientific run: `31756447460`, job `94633079955`, head `844d60a21ca1729247e398df10ed4dfbd7abc757`.
Artifact: `9202904848`, digest `sha256:0071f2011b64dbedf421019353ab3e5b4c8b0fbf384d2702dcb961de4e11fcf0`.
`RESULT.json` SHA-256: `0fba4eea58859de202430fb914a33b30588cdc2b177e876fb746dfcf501f5190`.

The protocol and sole feature were frozen before any observer-count distribution was inspected: annual fraction of immutable members with native observer count >=4, combined by the weaker-year minimum, appended as one 24th coordinate to exact v31. All 8,794 member counts were present; 47,240 protected-region raw rows were discarded before observer count access; no SonotaCo/target/MAARSY/DMS access occurred.

Exact parent reproduced:
- @25 23
- @50 41
- @100 66
- precision 0.7229521515453452
- MRR 0.050244164168646674
- qualified 95

Binding candidate:
- @25 **23** (gate pass)
- @50 **41** (gate pass)
- @100 **60** (gate fail; -6)
- top-100 precision **0.6813724373998415** (gate fail)
- MRR **0.049881257151102254** (gate fail)
- qualified **95** (gate pass)

Candidate hashes:
- feature `340825c481251a62ad8519ae122b731f1dc5f53b60bbb2b987b92da620cd79e2`
- X24 `47be7965f5c34f23a30d34f567a27b1abfcbfc8d6fdaca8199b0da1cec34ac43`
- margin `81c94f7c8f200e01c1009cd331a4ac20961d83b22617860148255bb67338b52c`
- local order `42147021556e36e680a318e998b0190086482a7d316c47defb22b76629ba430d`
- fused order `602fdc4fa566706f9c6f252f05970690727966cff04616e3e8b19181dec15df3`

Per the frozen protocol, the exact observer-confirmation lane and nearby result-motivated variants are closed: no >=3/>=5 threshold, continuous/raw count statistic, alternate annual summary/cross-year combiner, station identity/geography, interaction, quality companion, feature weight/scaling, diversity/fusion change, or SonotaCo benchmark.