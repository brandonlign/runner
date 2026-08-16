# OrbitTrace topomodal map-equation ranking v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is a genuinely distinct ranking/selection architecture built on the already-established fixed-scale topomodal candidate generator from PR #1284. It is designed after the closed intrinsic-prominence ranking successor, but it does not tune, blend, repair, or reuse that ranking.

The previous successor's exact frozen ranking is permanently closed. This protocol changes the **evidence principle** completely: candidate quality is defined by information compression of a random walk on the same fixed physical radius graph, not by ToMATo prominence, root status, density peak, density mean, support, recurrence, or any fitted combination of those quantities.

The scientific motivation is independent of the observed shower labels. The map equation of Rosvall & Bergstrom (PNAS 2008, doi:10.1073/pnas.0706851105) defines graph modules as structures that permit shorter descriptions of random-walk flow. A meteor-stream candidate should be a locally trapping module in the fixed physical-proximity graph; code-length gain therefore gives a parameter-free graph evidence score once the graph and candidate membership are fixed.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development data. Inclusive solar longitude `[20.0,55.0]` is removed before any geometry, graph, candidate construction, ranking, or truth evaluation.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any result-informed radius, density transform, hierarchy membership, map-equation variant, teleportation probability, edge weight, recurrence term, feature fusion, rank blend, threshold, sample subset, truth metric, or gate change.

No external benchmark is authorized by this sparse experiment.

## 2. Evaluation panels — unchanged

Reuse exactly the already-frozen `ORBITTRACE_SCALE_STRESS_V1` target-excluded GMN subsets:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Evaluate exactly eight pooled 2022+2023 subsets:

- coarse denominator `128`, buckets `0,1,2,3` (~5.8k pooled events each);
- fine denominator `1024`, buckets `0,1,2,3` (~0.7k pooled events each).

No new salt, denominator, bucket, replicate, bootstrap, or panel is authorized.

## 3. Candidate generator — exact PR #1284 architecture

Candidate generation is unchanged from `orbittrace_topomodal_hierarchy_scale_v1`:

- physical embedding:
  - `h_sol = 2 sin(5°/2)`;
  - `h_rad = 2 sin(4°/2)`;
  - `h_logv = ln(1.1)`;
  - `Z = (cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, ln(v_g)/h_logv)`;
- exact symmetric Euclidean radius graph at `r = 1.0`;
- the graph neighbor list includes self exactly as in #1284;
- density `rho_i = |N_i| / n`, including self;
- GUDHI `3.12.0` ToMATo with `graph_type='manual'`, `density_type='manual'`;
- complete leaf + internal merge-node + connected-component-root memberships;
- exact membership deduplication;
- minimum candidate support `4` applied only after hierarchy construction.

For every subset, before truth is opened, generated candidate memberships must match the authoritative #1284 structural artifact exactly: candidate count and the complete sorted set of `(family_hash, member_count, first_node, is_root)` rows. Any mismatch aborts before truth.

## 4. New evidence principle — binary map-equation compression gain

### 4.1 Canonical Markov chain

Use the exact symmetric radius-neighbor matrix already supplied to ToMATo, **including its diagonal self-neighbor**. Do not add, remove, reweight, or normalize individual edges before defining the walk.

Let

- `A_ij = 1` iff `j` is in the exact radius-neighbor list of `i` (including `A_ii=1`);
- `d_i = sum_j A_ij`;
- `D = sum_i d_i`;
- `P_ij = A_ij / d_i`;
- canonical stationary mass `pi_i = d_i / D`.

Because `A` is symmetric, `pi_i P_ij = 1/D` for every directed adjacency entry. The diagonal guarantees `d_i >= 1`. If the radius graph is disconnected, `pi` is still the explicitly frozen canonical stationary measure; no teleportation or component-specific renormalization is permitted.

### 4.2 Candidate partition

For each topomodal candidate `C`, evaluate exactly the two-module partition `{C, V\C}`. This is a scoring partition only; it does not alter candidate membership and it does not optimize over alternative partitions.

Define

- `pi_C = sum_{i in C} pi_i`;
- `q_C = sum_{i in C, j notin C} pi_i P_ij`;
- by symmetry `q_rest = q_C`;
- `q_total = q_C + q_rest = 2 q_C`;
- `p_circle_C = pi_C + q_C`;
- `p_circle_rest = (1-pi_C) + q_rest`.

The one-module code length is

`L1 = H(pi_1,...,pi_n)`

in bits.

For the two-module partition, use the standard two-level map equation:

`L2(C) = q_total H(Q) + p_circle_C H(P_C) + p_circle_rest H(P_rest)`.

`Q` is the normalized distribution of module exits `(q_C/q_total, q_rest/q_total)` when `q_total>0`; the index term is exactly zero when `q_total=0`.

`P_C` contains the normalized node-visit masses `{pi_i/p_circle_C : i in C}` plus exit mass `q_C/p_circle_C`; `P_rest` is defined analogously.

Use exact base-2 Shannon entropy with the convention `0 log2 0 = 0`.

### 4.3 Frozen score/order

Define

`compression_gain(C) = L1 - L2(C)`.

Rank **all** eligible topomodal candidates by:

1. decreasing `compression_gain`;
2. deterministic `family_hash` ascending as the sole tie-break.

No sign threshold is applied: candidates with non-positive gain remain in the complete ranked list. No prominence, root/finite indicator, density, support, year balance, recurrence, compactness, or prior rank is permitted as a secondary score or tie-break.

### 4.4 Zero-label implementation invariants

Before truth:

- verify the radius adjacency is symmetric and contains exactly one diagonal self-neighbor per event;
- verify every row-stochastic `P` sum is 1 within numerical tolerance;
- verify `sum(pi)=1` and detailed balance `pi_i P_ij = pi_j P_ji` on every adjacency entry within numerical tolerance;
- verify `L1 >= 0`, every `L2 >= 0`, and all compression gains finite;
- verify candidate/complement symmetry numerically by computing the same binary partition with candidate and complement labels swapped and requiring identical `L2` within `1e-12`;
- verify a synthetic disconnected two-block graph has positive compression gain for its exact block partition and zero gain for the one-module identity case.

These are engineering/source invariants only and may not change the scientific score.

## 5. Exact recurrent-EOM comparator — unchanged

On each identical subset reconstruct selected recurrent-EOM HDBSCAN v1 unchanged:

- exact GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- ordinary HDBSCAN condensed tree;
- exact annual-normalized recurrent-EOM contribution;
- exact FOSC/EOM extraction using recurrent stability.

Rank comparator candidates exactly as the selected parent:

1. decreasing recurrent stability;
2. decreasing ordinary stability;
3. decreasing member count;
4. deterministic family ID.

Its generated unordered memberships must match the authoritative #1284 structural artifact exactly before truth is opened.

## 6. Immutable prelabel boundary

For all eight subsets, persist before truth:

- exact event-universe hash;
- every topomodal candidate membership;
- `compression_gain`, `L1`, `L2`, `pi_C`, `q_C`, and final rank;
- every comparator membership and rank;
- exact candidate-summary matches to #1284;
- source/artifact hashes and firewall flags.

Write `TOPOMODAL_MAP_EQUATION_RANKING_V1_PRELABEL.json`, compute SHA-256, print it, and only then evaluate shower labels. Ranking may not be rerun or changed after truth.

## 7. Truth metric and candidate budget — unchanged from the prior sparse test

Use the selected recurrent-EOM parent's existing `metrics(...)` function unchanged, separately for 2022 and 2023 within every pooled subset.

For each subset:

- let `K` be the recurrent-EOM comparator candidate count;
- evaluate the comparator's complete ranked list of length `K`;
- evaluate exactly the first `K` map-equation-ranked topomodal candidates;
- evaluate the complete topomodal list only as a reporting diagnostic, never as a promotion gate.

Parent truth semantics stay unchanged:

- annual shower eligibility requires at least 4 events in that subset-year;
- positive candidate/shower match requires precision `>=0.5` and overlap `>=4`;
- report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, MRR, and median top-500 fragmentation.

## 8. Promotion gates — copied unchanged from topomodal sparse-recovery v1

There are 16 bucket-year panels. For each scale aggregate:

- `qualified_total = sum(qualified_matches)`;
- `mrr_mean = mean(MRR)`;
- `precision_mean = mean(top100_dominant_precision)`;
- `fragmentation_mean = mean(fragmentation_median_top500)`;
- count panelwise qualified-match wins/ties/losses.

Return

`PASS_TOPOMODAL_MAP_EQUATION_RANKING_V1`

iff **all ten** unchanged gates hold:

### Fine sparse scale (`d=1024`)

1. equal-budget successor `qualified_total` is strictly greater than recurrent-EOM;
2. successor has at least as many qualified matches as recurrent-EOM in at least `6/8` fine bucket-year panels;
3. `mrr_mean` is at least recurrent-EOM;
4. `precision_mean` is at least recurrent-EOM;
5. `fragmentation_mean` is no higher than recurrent-EOM.

### Coarse scale (`d=128`)

6. equal-budget successor `qualified_total` is at least recurrent-EOM;
7. successor has at least as many qualified matches as recurrent-EOM in at least `6/8` coarse bucket-year panels;
8. `mrr_mean` is at least recurrent-EOM;
9. `precision_mean` is at least recurrent-EOM;
10. `fragmentation_mean` is no higher than recurrent-EOM.

Otherwise return

`FAIL_TOPOMODAL_MAP_EQUATION_RANKING_V1`.

No gate is relaxed because of the previous result.

## 9. Interpretation / closure

A PASS means a new two-stage architecture has now demonstrated both sides required for the actual OrbitTrace goal in sparse GMN regimes:

- #1284's fixed-scale topomodal hierarchy gives sample-size-stable candidate construction;
- map-equation compression provides an independently motivated label-free ordering that beats recurrent-EOM under the same recovery/ranking gates.

Only a PASS authorizes engineering work on a scalable full-catalog implementation followed by a separately frozen full-GMN comparison.

A FAIL permanently closes this exact `fixed-scale topomodal candidate generator + binary map-equation compression-gain ranking` architecture. Do not alter self-loop treatment, teleportation, map-equation level, code-length definition, tie-break, candidate generator, radius, density, support, sample subsets, truth metrics, or gates after outcome.