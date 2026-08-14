# RFT v1 exact fast `pair_d` engineering substitution

Status: frozen before any fast-pair RFT output. Engineering identity refinement only; scientific method changes: **none**.

## Frozen function

RFT v1 source blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301` defines, for ordered event pair `(a,b)`:

1. `ua = unit(np.asarray([a['lon']]), np.asarray([a['lat']]))[0]`;
2. `ub = unit(np.asarray([b['lon']]), np.asarray([b['lat']]))[0]`;
3. `dot = np.dot(ua,ub)` and scalar clipping to `[-1,1]` inside `angle_deg`;
4. `theta = degrees(acos(clipped_dot))/3`;
5. `speed = abs(log(a['vg']/b['vg'])) / log(1.08)`;
6. `pair_d = float(hypot(theta,speed))`.

The ordered direction is scientifically/bitwise significant: no `(a,b)`/`(b,a)` symmetry cache is authorized. A direct development-data probe found small floating differences between the two directions, so the existing ordered cache remains ordered.

## Exact implementation substitution

For every event object participating in one atomization job:

- evaluate the **same frozen singleton** `unit(np.asarray([lon]), np.asarray([lat]))[0]` once and store that exact array by object identity;
- for every ordered `pair_d(a,b)` miss, retrieve those exact singleton arrays and call the same `np.dot`;
- replace scalar `float(np.clip(dot,-1.0,1.0))` only with the logically identical scalar branch:
  - if `dot < -1.0`, use `-1.0`;
  - else if `dot > 1.0`, use `1.0`;
  - else use the unchanged Python float `dot`;
- apply the exact same `math.acos`, `math.degrees`, `/3.0`, ordered `a['vg']/b['vg']`, `math.log`, `abs`, `/math.log(1.08)`, `math.hypot`, and `float` operations in the same expression order;
- retain the cache key as the exact ordered object-identity pair `(id(a),id(b))`.

No reverse-pair reuse, precomputed log-speed difference, vectorized pair distance, approximate angle, altered clipping tolerance, float downcast, or changed arithmetic order is allowed.

## Why this is exact

`unit()` is a deterministic pure function of the same two stored binary64 values. Computing its frozen singleton result once and reusing that exact array cannot alter later `np.dot` inputs. For a finite scalar `dot`, NumPy scalar clipping to `[-1,1]` has exactly the same three-value cases as the explicit branch above and introduces no additional scientific rule. Every remaining floating operation is unchanged and ordered identically.

Before use, the implementation must additionally enforce a zero-endpoint bitwise audit on deterministic exact GMN-2022 ordered pairs spanning all accessible atom bins: original frozen `pair_d(a,b) == fast_pair_d(a,b)` as Python floats. The audit is engineering-only and may not compute atoms, tubes, labels, recovery metrics, or candidate scores.

## Existing corroboration before freeze

A nonbinding implementation probe on 50,000 deterministic ordered pairs drawn from the exact prepared target-excluded 2022 events found zero float mismatches between frozen `pair_d` and this operation-preserving formulation. The reverse-direction shortcut was explicitly rejected because it did produce floating mismatches.

## Firewall

GMN 2022 target-excluded engineering input only. No GMN 2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY or DMS access. No scientific endpoint is authorized by this protocol.
