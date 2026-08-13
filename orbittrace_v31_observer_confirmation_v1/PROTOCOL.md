# OrbitTrace GMN v31 four-station observer-confirmation v1

## Status

Binding target-excluded GMN 2022+2023 successor protocol, frozen **before the station-count availability result and before any hard-family station-count distribution is inspected**.

This successor is dormant unless the first technically valid `PASS_GMN_V31_STATION_COUNT_AVAILABILITY_V1` artifact exists and is pinned exactly. If availability fails, this successor is not executed.

No SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY, or DMS is authorized by this GMN development protocol.

## Scientific motivation fixed independently of OrbitTrace outcomes

The Global Meteor Network methodology paper reports median radiant precision of about 0.47 degrees over all trajectories and about 0.32 degrees for the roughly 20% of meteors observed from **four or more stations**. Four-station participation is therefore fixed here as a physically motivated high-confirmation observation class before project station-count values are queried.

The final SonotaCo 2013/2014 label-free normalizer independently exposes native `ncam` and already requires `ncam >= 2`, so the same four-or-more camera definition is portable if this GMN method later passes its frozen gate. No SonotaCo outcome is used to define the feature.

## Immutable parent

Exact GMN v31-principle parent:
`orbittrace_gmn_v31_principle_local_geometry_oof_v1/run_development.py`, Git blob `b4e2d72e532e47aa95ed335f690748423d11ea59`.

Required parent controls:
- 226 immutable P19 hard families;
- 23D parent feature matrix;
- recovery@25/50/100 = `23/41/66`;
- top-100 dominant precision `0.7229521515453452`;
- MRR `0.050244164168646674`;
- qualified matches `95`;
- five exact strict whole-shower OOF folds;
- ordinary fold-training z-score;
- Euclidean k=1 local geometry;
- margin `d_nonpositive-d_positive`;
- diversity lambda `0.8`, scale `1.0`;
- equal rank-sum with the immutable P19 hard order.

No candidate generation, membership, truth definition, fold, model, distance, k, parent feature, diversity, fusion, threshold, or evaluation rule changes.

## Sole new feature

For each immutable family `i` and year `y in {2022,2023}`:

`c_i,y = (# immutable member meteors in year y with observer_count >= 4) / (# immutable member meteors in year y)`.

The sole appended coordinate is

`observer_confirmation_i = min(c_i,2022, c_i,2023)`.

Thus the candidate feature matrix is exactly the immutable 23D parent matrix plus this one 24th scalar coordinate.

Rationale for the fixed annual minimum: a recurrent family is required to be supported in both years, so the weaker annual high-confirmation share is the conservative recurrence-level observation-quality summary. This rule is frozen before any family-specific observer-count value is seen.

For GMN, `observer_count` is the exact count of rows in the official `participating_station` table for that immutable event ID. For a later separately frozen SonotaCo compatibility run, the same quantity is native `ncam`. No station identity, geography, fit-error, uncertainty, convergence-angle, or other quality field enters this successor.

## Explicit no-search boundary

Exactly one threshold and one statistic exist:
- threshold: observer count >= **4**;
- per-year statistic: member fraction satisfying that threshold;
- cross-year combiner: **minimum**.

No >=3/>=5 threshold, raw mean/median/min/max observer count, count clipping, continuous count transform, station identity/diversity/geography, mean/geometric/harmonic cross-year combination, event weighting, interaction with parent features, feature rescaling outside parent OOF z-scoring, or companion quality feature may be tested after this outcome.

## Execution and evaluation

1. Reproduce all exact parent feature/order/metric controls first.
2. Require the first valid station-count availability artifact to PASS and pin its immutable event-count mapping digest.
3. Build the 226-value feature completely before accessing parent truth labels for candidate evaluation.
4. Append exactly one coordinate and run the exact parent strict-OOF margin, nominal parent centroid diversity, hard-order fusion, and evaluator unchanged.
5. Hash the feature vector, 24D matrix, raw margin, local order, and fused order before emitting metrics.

## Binding promotion gate

PASS requires all:
- recovery@25 >= **23**;
- recovery@50 >= **41**;
- recovery@100 > **66**;
- top-100 dominant precision >= **0.7229521515453452**;
- MRR >= **0.050244164168646674**;
- qualified matches = **95**;
- provenance/firewall pass.

PASS verdict: `PASS_GMN_V31_FOUR_STATION_CONFIRMATION_V1`.
FAIL verdict: `FAIL_GMN_V31_FOUR_STATION_CONFIRMATION_V1`.

A FAIL permanently closes this exact observer-confirmation family and all nearby result-motivated variants listed above. No SonotaCo benchmark follows a FAIL. A PASS authorizes only a separately frozen one-shot SonotaCo compatibility/generalization test of this exact rule; SonotaCo remains exposed development only, never external validation.