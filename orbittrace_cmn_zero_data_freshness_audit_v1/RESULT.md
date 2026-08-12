# OrbitTrace CMN zero-data freshness audit v1 — binding result

## Verdict

`PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT`

This is a repository-history eligibility PASS only. It is not a detector result, scientific validation, or authorization to access CMN event-level data.

## Binding provenance

- protocol freeze commit: `0f67a5caf20efe1a7dc42b5eeb08fb3262c96241`
- implementation freeze commit: `c0b093880af16e4dcf188aa6877b268d891333c3`
- workflow registration commit: `952e3701ebbe74065c972b6b254661e13e575067`
- first technically valid run: `31636537011`
- job: `94248148214`
- artifact ID: `9157162439`
- artifact digest: `sha256:c18a950dd58fb32b0883ea238e822da284ab25daf33efc3294810eda50722b04`

## Binding findings

Fixed CMN history indicators all returned zero hits outside this audit:

- `Croatian Meteor Network`: 0
- `CroatianMeteorNetwork`: 0
- `CMN Orbit`: 0
- `CMN_Orbit`: 0
- `CMN-Orbit`: 0
- `cmn.rgn.hr`: 0
- CMN ref-name hits: 0

Both required spent-survey positive controls were recovered extensively:

- FRIPON history: detected
- UKMON history: detected

Therefore the absence of CMN hits is not explained by a nonfunctional history scan.

## Scientific interpretation boundary

CMN appears unconsumed by the OrbitTrace repository under the frozen indicators and may proceed only to a separately frozen structure-only public-interface audit. No CMN orbit, radiant, velocity, event identifier, shower label, or catalogue scientific record was accessed in this run.

A later interface PASS would still not make CMN a validation set. Dataset suitability, field compatibility, temporal structure, sample support, and target-firewall feasibility must each be established before any scientific use is authorized.

## Firewall

- CMN scientific/event-level access: false
- OrbitTrace target information/events: false
- protected 20°–55° region: inaccessible
- SonotaCo scientific access: false
- MAARSY scientific access: false
- DMS scientific access: false
