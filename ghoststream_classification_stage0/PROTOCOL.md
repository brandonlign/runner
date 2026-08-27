# GhostStream distinct-stream versus branch classification

Status: runner-only classification audit. This is not a new discovery-method claim. The existing GhostStream discovery, antihelion source-preserving null, current MDC duplicate screen, and external replication are unchanged.

## Scientific question

The remaining classification question is whether the late-April GhostStream candidate is:

1. a distinct uncatalogued stream;
2. a branch of the nearest known shower or a broader known complex; or
3. structured antihelion background.

The existing source-preserving antihelion audit already rejects explanation 3 under the frozen observational null. This stage therefore tests whether a calibrated dynamical branch comparison can distinguish explanations 1 and 2.

## Frozen source evidence

- exact canonical GhostStream package: runner artifact `8814798136`, ZIP SHA-256 `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`;
- exact real-shower data audit: runner artifact `8871850235`, ZIP SHA-256 `5f2501b3eee19b51a5dc81f8493dce67a810ef5c480045dac143de060369534d`;
- official GMN monthly trajectory summaries for May and June 2019–2026, fetched and checksum-locked during execution for Northern May Ophiuchids (`NOP`, IAU 149).

GhostStream is used only as the final pair to classify. It may not select controls, negative pairs, orbit estimators, integration horizons, scores, or thresholds.

## Frozen data gate

### Target pair

- GhostStream: all 101 exact deduplicated GMN members from the canonical package;
- NOP: all quality-screened IAU-149 events in official May–June GMN files for 2019–2026;
- the member-medoid orbital distance must reproduce the current official candidate–NOP distance within `0.08`.

### Established branch controls

The primary calibration pairs are complete MDC-group pairs whose two components are established or working-list showers and have large real GMN samples:

- Southern/Northern Taurids: `STA/NTA` (IAU 2/17);
- Northern/Southern delta-Cancrids: `NCC/SCC` (IAU 96/97);
- Northern/Southern chi-Orionids: `ORN/ORS` (IAU 256/257).

Two pairs containing a provisional component are retained only as sensitivity controls and cannot make the primary calibration pass:

- Northern/Southern October delta-Arietids: `NOA/SOA` (IAU 25/28);
- Northern/Southern delta-Piscids: `NPI/SPI` (IAU 215/216).

The June-Aquilid pair `NZC/SZC` is excluded prospectively because its GMN member medoids are not orbitally branch-like despite sharing an MDC group; keeping it would treat a catalogue-grouping conflict as dynamical truth.

### Matched distinct controls

For each primary branch pair, choose one pair from different MDC groups and without a shared normalized parent-body label. Matching uses only present-day quantities:

- orbital distance;
- activity-center separation;
- geocentric-speed difference.

A negative pair must match orbital distance within `0.08` and activity separation within `35°`. Selection is deterministic and occurs before any integration.

### Data-gate requirements

All must pass:

1. at least 95 complete GhostStream members;
2. at least 100 complete NOP members across at least four years;
3. all three primary branch pairs present with at least 200 events per shower across at least three years;
4. both provisional sensitivity pairs present;
5. three independently selected matched-distinct pairs;
6. every representative orbit crosses within `0.08 AU` of Earth at one node;
7. the recomputed GhostStream–NOP distance agrees with the locked official value within `0.08`.

Failure ends the dynamical classification route.

## Frozen dynamical test after a data pass

The dynamics stage may run only after the data gate passes. It will use real-member bootstrap orbit representatives, REBOUND/IAS15 with the same packaged outer-solar-system setup already validated in runner, and Earth-node-consistent mean anomalies.

The primary pair score is a sustained backward-convergence statistic, not a single-time minimum:

- integrate each paired bootstrap realization backward for 1,500 years;
- record orbital distance every 10 years;
- smooth each path with a 100-year rolling median;
- compare current distance with the minimum sustained historical distance;
- report the clone distribution of convergence magnitude and minimum sustained distance.

The classifier is valid only if all three established branch pairs beat their own matched-distinct controls and the three-versus-three pair AUROC is `1.0`. At least one of the two provisional sensitivity pairs must also exceed the median distinct-control score. These requirements are evaluated before GhostStream–NOP is interpreted.

If calibration fails, the verdict is `DYNAMICAL_CLASSIFIER_NOT_VALID`; no branch/distinct conclusion may be drawn from the integration. If calibration passes, GhostStream–NOP is classified only by its frozen empirical position relative to the controls. No post-result horizon, smoothing width, clone count, pair selection, or score change is permitted.

## Claim boundary

A successful classification stage could strengthen the statement that GhostStream is dynamically inconsistent with the nearest known branch hypothesis. It would not prove official distinct-stream status, identify a parent body, establish a first-ever method, or replace independent meteor-science review.
