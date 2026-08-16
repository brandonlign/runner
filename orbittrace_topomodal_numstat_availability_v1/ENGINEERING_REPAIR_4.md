# Engineering repair 4 — exact #1284 sparse-universe manifest

## Classification

**ENGINEERING SAMPLE-IDENTITY REPAIR ONLY. No availability or method threshold changes.**

The first run that reached all 24 monthly files (`31972478165`, job `95226924383`) stopped before emitting a station-count mapping or gate result because the initial availability implementation derived sparse IDs from every raw monthly row passing only the solar-longitude exclusion. This produced `5571` IDs in frozen `d=128,b=0` instead of #1284's immutable `5567`.

No partial `num_stat` mapping or histogram was emitted or inspected for method design.

A subsequent execution-free static source audit (`31972784984`, job `95227696077`) reconstructed the exact frozen #1284 scan parser without executing it. It proved the already-established scan universe is defined, before hashing, by:

- finite solar longitude, geocentric ecliptic longitude, geocentric ecliptic latitude, and geocentric speed;
- solar longitude in `[0,360]`;
- geocentric ecliptic longitude in `[0,360]`;
- geocentric ecliptic latitude in `[-90,90]`;
- geocentric speed in `[5,75]` km/s;
- inclusive OrbitTrace exclusion `[20,55]` on solar longitude;
- first occurrence of each trajectory ID across the monthly sequence.

These are not new selection criteria: they are the exact pre-existing #1284 event-universe criteria that the availability audit was required to reproduce from the start.

## Exact repair architecture

Split sample identity from station-support access:

### Stage A — immutable predecessor-universe reconstruction

Before `num_stat` is read, parse only:

- unique trajectory ID;
- solar longitude;
- `LAMgeo`;
- `BETgeo`;
- `Vgeo`.

Apply the exact frozen #1284 validity/exclusion/duplicate rules above. Apply the exact frozen SHA-256 thinning rule and require all eight already-frozen subset counts:

- d128: 5567, 5840, 5857, 5816;
- d1024: 677, 739, 736, 766.

Emit only event IDs/subset identities and source hashes. Do not emit geometry values or station counts.

### Stage B — original station-count availability audit

Re-read the same official monthly files using the availability audit's original allowed fields only:

- unique trajectory ID;
- solar longitude;
- `Num (stat)`.

Parse/convert `Num (stat)` **only for event IDs present in the Stage-A manifest**. Raw rows outside that immutable manifest cannot enter an emitted station-count mapping, histogram, completeness statistic, or conditional successor.

Thus station support remains downstream of and incapable of changing the scientific sample.

## Scientific invariants

Unchanged:

- exact #1284 sparse event universes and counts;
- same official GMN monthly source;
- same years 2022/2023;
- same inclusive target exclusion;
- same usable station-count definition: finite exact integer >=2;
- same 95% availability gates;
- same stricter 100% per-panel completeness prerequisite for the conditional structural successor;
- same station-weighted density formula and all pre-frozen structural/recovery protocols;
- no station identity/geography, shower label, target information, SonotaCo, ASFN/EFN, AMOS, MAARSY, or DMS access.

No partial station-count distribution from failed runs is used to choose any method parameter or repair.