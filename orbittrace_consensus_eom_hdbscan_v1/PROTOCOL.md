# OrbitTrace consensus-EOM HDBSCAN v1 — frozen protocol

## Status

Frozen before the first technically valid scientific outcome of consensus-EOM HDBSCAN v1.

This successor is developed from the already-promoted recurrent-EOM HDBSCAN v1 lineage. It does **not** use EFN, AMOS, SonotaCo, OrbitTrace target information, MAARSY, or DMS for architecture selection. The branch is rooted at recurrent-EOM's binding GMN result commit `e3ad80dd4d685b32917af9e2e6d76cb2b76857d4`, before the later EFN work existed on this branch history.

Scientific firewall remains binding:

- protected solar longitude `[20 deg,55 deg]` is inaccessible;
- no OrbitTrace target information/events;
- no MAARSY or DMS scientific access;
- no SonotaCo 2013/2014 access during this development test;
- development data are the permanent target-excluded GMN 2022+2023 pool only;
- every candidate membership and rank must be frozen before shower truth is evaluated;
- the first technically valid result is binding;
- no post-result variant, weighting, threshold, tie rule, feature, parameter, ranking, or aggregation rescue is allowed.

## 1. Parent method

The scientific parent is the exact recurrent-EOM HDBSCAN v1 that passed target-excluded GMN development in binding run `31827903547`.

Pinned source:

- recurrent-EOM implementation Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- promoted recurrent-EOM GMN runner Git blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- recurrent-EOM binding result record Git blob: `3d689ad900da9dd30eb9dc32c389cb508897bc05`.

Binding recurrent-EOM GMN result:

- run `31827903547`;
- artifact `9229646556`;
- artifact digest `sha256:a0b1ba017696b32cf2e19b3542430adac7bfd13fa2fb78494b6d42742aa35f6d`;
- result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`;
- pre-label SHA-256 `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`.

Exact parent configuration remains:

- GEO6 = `(cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72)`;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- HDBSCAN EOM condensed hierarchy;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=False`;
- `prediction_data=False`;
- pooled target-excluded GMN 2022+2023 hierarchy;
- annual EOM contributions normalized by accessible event count in each year;
- recurrent scalar stability `E_rec(C)=min(E_2022(C),E_2023(C))`;
- parent extraction = standard HDBSCAN EOM using `E_rec` as the scalar stability objective;
- parent ranking = descending `E_rec`, descending ordinary HDBSCAN stability, descending member count, ascending deterministic family ID.

No parent byte or scientific rule is changed.

## 2. Motivation independent of external data

Standard EOM reduces a hierarchy to flat clusters by comparing one parent stability against the summed effective stability of its child solution. Recurrent-EOM v1 first collapses two annual stability values into the scalar minimum and then applies that one-dimensional EOM comparison.

For repeated-observation physical streams there is a distinct, parameter-free alternative: retain the annual stability vector through the EOM decision itself. A simplification from children to their parent should be accepted only when the parent is not worse than the child solution in **either** observing year.

This tests a multi-objective temporal-consensus modification of HDBSCAN's EOM optimization rather than another fitted scalar combiner. It is motivated solely by the two-year recurrence structure already present in the GMN development design.

## 3. Sole new mechanism: componentwise consensus EOM

Use the exact same pooled HDBSCAN condensed tree and the exact same annual normalized stability values already defined by recurrent-EOM v1:

`V(C) = (E_2022(C), E_2023(C))`.

Let the condensed cluster tree contain only cluster-child rows (`child_size > 1`). Process non-root cluster nodes bottom-up in the same descending-node topological order used by the exact HDBSCAN EOM mirror.

For each node C, maintain an effective two-component stability vector `F(C)` and a selected/not-selected state.

### Leaf / no-cluster-child case

The summed effective child vector is `(0,0)`.

### Internal node case

Let

`S(C) = sum_{D in immediate cluster children of C} F(D)`

componentwise.

C is eligible to replace its descendants only when its annual stability is **strictly positive in both years**:

`E_2022(C) > 0 and E_2023(C) > 0`.

This is a zero/nonzero recurrence requirement, not a fitted threshold.

If eligible and

`E_2022(C) >= S_2022(C)` **and** `E_2023(C) >= S_2023(C)`,

then:

- select C;
- deselect every selected descendant of C;
- set `F(C)=V(C)`.

Otherwise:

- do not select C;
- retain the child solution;
- set `F(C)=S(C)`.

Ties are resolved toward the parent in a component exactly as standard HDBSCAN EOM resolves a scalar tie toward the parent; no epsilon or tolerance is used.

The root remains excluded exactly as `allow_single_cluster=False` excludes it in the parent.

This componentwise dynamic program is the **only scientific change** relative to recurrent-EOM v1.

No weighted sum, product, harmonic/geometric mean, balance coefficient, year weight, annual support count threshold, persistence cutoff, diversity rule, or post-filter is authorized.

## 4. Label assignment

The selected consensus nodes form an antichain in the same condensed hierarchy.

Each original event receives the compact label of the first selected cluster ancestor encountered while following its unique condensed-tree parent chain upward; if no selected ancestor exists before the root, it is noise (`-1`). Compact labels are assigned in ascending selected-node order.

This is not a scientific degree of freedom. Before scientific truth evaluation, a zero-truth engineering audit must establish that this custom ancestor labeller reproduces HDBSCAN's canonical partition exactly when supplied the node set selected by standard scalar EOM:

1. ordinary HDBSCAN stability -> `selected_eom_nodes` -> custom ancestor labeller must equal ordinary `eom_labels` partition;
2. recurrent scalar stability -> `selected_eom_nodes` -> custom ancestor labeller must equal recurrent-EOM `eom_labels` partition;
3. these equivalences must pass on synthetic trees before any binding GMN outcome;
4. the binding GMN runner must re-check recurrent-parent partition identity before persisting candidates.

Any mismatch is an engineering no-result; it does not authorize changing the scientific consensus rule.

## 5. Candidate ranking

The successor changes **selection only**. Ranking deliberately remains the recurrent-EOM parent ranking so a positive result cannot be attributed to a second new mechanism.

For every selected consensus node:

- candidate membership = exact sorted member IDs from the custom labels;
- minimum cluster support remains inherited `10`;
- ordinary HDBSCAN stability is recorded unchanged;
- recurrent scalar stability remains `min(E_2022,E_2023)` and is used only as the inherited ranking score.

Deterministic consensus candidate ID prefix: `CEOM1`.

Successor rank order:

1. descending recurrent scalar stability;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. ascending deterministic family ID.

The recurrent-EOM parent retains its exact existing ranking rule and `REOM1` IDs.

No new score, probability, outlier measure, trim, reranker, fusion, v31 feature, or learned model is permitted.

## 6. Development evaluation

Use exactly the recurrent-EOM v1 target-excluded GMN 2022+2023 loader and truth convention:

- same 315,024 accessible 2022 events;
- same 423,658 accessible 2023 events;
- same pooled 738,682 event set;
- eligible known shower = at least 4 labeled events in the evaluated year;
- qualified match = dominant shower precision >=0.5 and overlap >=4;
- evaluate each year by restricting each pooled candidate's members to that year without changing pooled rank;
- report recovered known showers @25/@50/@100/@500, full-catalogue qualified matches, top-100 dominant precision, MRR, and median top-500 fragmentation.

Candidate memberships, selected-node sets, inherited ranking scores, and complete pooled order for both parent and successor must be persisted before the sealed shower truth object is opened.

## 7. Binding gate versus recurrent-EOM parent

The first technically valid GMN outcome is binding. Consensus-EOM v1 passes only if **all** of the following hold relative to exact recurrent-EOM v1 in the same run:

1. recovered@100 is strictly higher in at least one year and not lower in the other;
2. recovered@50 is not lower in either year;
3. top-100 dominant precision is not lower in either year;
4. MRR is not lower in either year;
5. median top-500 fragmentation is not higher in either year;
6. the consensus selected-node set differs from recurrent-EOM's selected-node set, proving the mechanism is active.

Recovered@25, recovered@500, and full-catalogue qualified matches are reported but are not gates, matching the recurrent-EOM development convention.

PASS token:

`PASS_CONSENSUS_EOM_HDBSCAN_V1_GMN_DEVELOPMENT`

FAIL token:

`FAIL_CONSENSUS_EOM_HDBSCAN_V1_GMN_DEVELOPMENT`

If any gate fails, consensus-EOM v1 is permanently rejected. No strict-vs-nonstrict positivity variant, annual threshold, tie-rule change, scalar/vector blend, ranking change, feature change, HDBSCAN parameter change, or alternate selection rescue is permitted.

A PASS authorizes only a separately frozen next-stage exposed SonotaCo comparator protocol. It does not authorize EFN as pristine validation; EFN is excluded from this successor's scientific validation lineage.

## 8. Novelty statement if supported

If the frozen experiment passes, the methodological claim is **consensus-EOM hierarchical density clustering**: HDBSCAN is the explicit parent, while the flat-cluster optimization is changed from scalar EOM to a componentwise multi-observation stability decision that accepts hierarchy simplification only under annual consensus.

HDBSCAN and its EOM lineage must be cited. The contribution is the multi-objective repeated-observation selection mechanism, not a claim that the detector was developed independently of HDBSCAN.
