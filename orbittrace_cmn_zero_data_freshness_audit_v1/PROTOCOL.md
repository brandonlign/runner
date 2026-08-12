# OrbitTrace Croatian Meteor Network zero-data freshness audit v1

## Status

Frozen before any Croatian Meteor Network (CMN) scientific record, catalogue row, orbit, radiant, velocity, shower label, or event identifier is accessed.

This is a repository-history and public-metadata eligibility audit only. It is not a detector experiment, method result, external validation, or authorization to use CMN scientific data.

## Motivation

The post-v60 successor audit has exhausted or scientifically closed the main nearby representation/normalization/weighting/graph/density/classifier lanes, while the current GMN 21D/71D ranking representations remain family-summary based. A genuinely different raw-member/set representation remains technically open, but choosing a high-capacity architecture only from exposed SonotaCo outcomes or repeatedly optimized GMN 2022/2023 would create unacceptable researcher degrees of freedom.

A fresh independent public multi-station orbit catalogue could provide a development/generalization environment before any new SonotaCo benchmark view. Published dataset surveys report that the Croatian Meteor Network orbit catalogues contain approximately 41,634 public multi-station meteor orbits. Before any CMN event-level access, repository history must establish whether CMN has already been scientifically consumed by this project.

## Frozen audit scope

The audit may inspect only the complete Git history and ref names of `brandonlign/runner`.

Search indicators are fixed to case-insensitive occurrences of:

- `Croatian Meteor Network`
- `CroatianMeteorNetwork`
- `CMN Orbit`
- `CMN_Orbit`
- `CMN-Orbit`
- `cmn.rgn.hr`

The audit must ignore its own audit directory/workflow so the preregistration text cannot self-trigger.

Positive controls:

- `FRIPON` must be detected somewhere in prior repository history;
- `UKMON` must be detected somewhere in prior repository history.

These positive controls demonstrate that the history scan is capable of recovering known spent external-survey work.

## Frozen gate

`PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT` requires:

1. no pre-existing branch/ref name matching the fixed CMN indicators outside this audit branch;
2. no historical content hit matching any fixed CMN indicator outside this audit directory/workflow;
3. both FRIPON and UKMON positive controls are found in historical content;
4. no network request to a CMN/IAU/IMO/data endpoint occurs in the workflow or audit script;
5. no scientific value, event identifier, row count obtained from CMN itself, shower label, detector score, or target information is accessed.

Any CMN history hit yields `FAIL_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT` and permanently prevents describing CMN as scientifically fresh for this successor-selection purpose without a separately justified provenance adjudication. No alternate CMN year/subset may be selected from the failure.

A PASS authorizes only a separately frozen **structure-only public-interface audit**. It does not authorize downloading or parsing CMN scientific records.

## Protected-data firewall

- OrbitTrace protected solar-longitude region 20°–55°: inaccessible.
- OrbitTrace target information/events: inaccessible.
- SonotaCo scientific values: not accessed.
- MAARSY scientific access: false.
- DMS scientific access: false.
- CMN scientific/event-level access: false.
- Scientific shower labels: false.
- External validation performed: false.
