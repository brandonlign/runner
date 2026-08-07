# OrbitTrace UKMON 2022 live interface development

## Status
Frozen before the first UKMON meteor-data API call. This stage may access **2022 only**. UKMON 2024 and 2025 remain scientifically reserved and may not be queried.

## Why this date
Use exactly the date `2022-08-14`, because it is the example date published by UKMON in its public API documentation. The date was therefore not selected after inspecting meteor data. Its seasonal location is outside the blinded OrbitTrace solar-longitude interval 20°–55°.

## Prerequisites
- UKMON 2024/2025 full-history freshness audit passed (run `31213731631`, artifact `9007677623`).
- Documentation-only interface adjudication passed (run `31214115843`, artifact `9007813875`).
- Documented matched-trajectory fields are frozen as:
  - trajectory identifier: `orbname`;
  - solar longitude: `_sol`;
  - geocentric radiant: `_ra_t`, `_dc_t`;
  - candidate speed field: `_vg`;
  - orbit: `_q`, `_e`, `_incl`, `_peri`, `_node`.

## Allowed API access
Exactly one UKMON matched-summary request:
`https://api.ukmeteors.co.uk/?reqtyp=summary&year=2022&month=08&day=14`

No 2024/2025 request, no arbitrary date search, no full-trajectory pickle, and no OrbitTrace target information.

## Frozen interface gates
The response must:
1. be valid JSON and contain at least 5 matched trajectories;
2. expose all frozen keys above on at least 95% of returned rows;
3. have unique nonempty `orbname` values;
4. have finite `_sol`, `_ra_t`, `_dc_t`, `_vg` on at least 95% of rows;
5. have `0<=_sol<360`, `0<=_ra_t<360`, `-90<=_dc_t<=90`;
6. have `_vg` numerically consistent with km/s meteor speeds: at least 95% of finite values in 5–75;
7. have finite orbital fields `_q`, `_e`, `_incl`, `_peri`, `_node` on at least 80% of rows;
8. have orbital values in broad physical/interface ranges: `_q>0`, `_e>=0`, `0<=_incl<=180`, and finite angular `_peri/_node`;
9. contain zero row with `20<=_sol<=55`; if such a row appears unexpectedly, the interface stage fails before its radiant, speed, or orbital fields are inspected.

This stage is interface development only. It does not evaluate v6, tune any scientific parameter, compare methods, or authorize target reveal.
