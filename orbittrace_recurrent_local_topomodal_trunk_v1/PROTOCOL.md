# OrbitTrace recurrent-locked local TopoModal trunk v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION, BEFORE ANY ZERO-LABEL STRUCTURAL OUTCOME FOR THIS SUCCESSOR, AND BEFORE ANY SHOWER-TRUTH OUTCOME.**

This protocol defines one full target-excluded GMN membership-representation successor to the current density-synchronous recurrent-EOM development champion. It is motivated by the already-sealed evidence that recurrent-EOM supplies unusually strong early catalogue slot order while fixed-scale TopoModal repeatedly supplies cleaner sparse modal structure.

The scientific question is deliberately narrow:

> If the full-GMN recurrent catalogue order is held exactly fixed, can the membership occupying a parent slot be made cleaner by removing only the final low-density/topologically separate attachment around that parent's dominant local mode?

This is a membership experiment, not a global reranker and not a new global candidate generator.

## 1. Immutable parent and firewall

The parent is density-synchronous recurrent-EOM HDBSCAN v1:

- frozen protocol commit `12006b7e06280fb5b39619f92719915ce2f96b64`;
- protocol blob `1187cbba37372c834bdbbf7eb05b1f7c31f8dcf9`;
- scientific runner blob `157813ca331165180a6d20aa71bfc78d5984396f`;
- synchronous kernel blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- binding valid run `31852836840`;
- binding artifact `9238142199`, digest `sha256:918992863d019baf3bbb5eadd83ecaa32cabea3d9bd7d9d43735b26474e8ed60`;
- binding prelabel SHA-256 `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`;
- binding result SHA-256 `ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711`.

The successor must reconstruct exactly the same target-excluded GMN 2022+2023 event universe and the exact density-synchronous recurrent-EOM parent candidate memberships and order before local refinement.

Inclusive solar longitude `[20.0,55.0]` is removed before any geometry, topology, representation choice, prelabel output, or truth evaluation.

Forbidden throughout this experiment:

- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- orbital information, station metadata, uncertainty metadata, or shower labels during representation construction;
- any result-informed radius, support threshold, hierarchy choice, parent subset, rank rule, fallback rule, metric, or gate change.

## 2. Why this is a distinct mechanism

This successor is not a rescue or threshold tweak of a closed lane.

- `recurrent-topomodal-support-mask-v1` intersected a Recurrent parent with the union of **globally generated sparse TopoModal children**. This successor fits topology independently *inside each already-frozen full-GMN parent* and never uses the closed support-mask construction.
- `recurrent-topomodal-component-union-v1` expanded a parent by unioning corroborating children. This successor can only remove events; it never adds or unions membership.
- `recurrent-core-local-envelope-v4` expanded frozen v8 component seeds using centroid envelopes. This successor performs no centroid envelope, event expansion, nearest-family assignment, or v8 membership operation.
- historical v8/P12 membership-switch work searched development-truth outcomes over a threshold grid. This successor contains no grid, learned selector, truth-trained switch, or fitted threshold.
- the closed annual-confirmation, lineage, support-cut, representative-share, overlap-consensus, and Pareto-prominence sparse ranking lanes globally reordered TopoModal candidates. This successor preserves the full-GMN Recurrent slot order exactly.

The new rationale is local topological erosion: within a parent already supported by density-synchronous cross-year recurrence, remove only the smallest topological amount required to isolate the dominant density-mode trunk from the parent's final merge/extra connected structure.

## 3. Frozen local physical topology

For every density-synchronous Recurrent parent independently, use only that parent's frozen event IDs and the exact normalized target-excluded GMN event rows.

Sort parent events by exact event ID before topology.

Use the same physical embedding frozen by the positive fixed-scale TopoModal hierarchy work:

- `h_sol = 2 sin(5 deg / 2)`;
- `h_rad = 2 sin(4 deg / 2)`;
- `h_logv = ln(1.1)`;
- `Z = (cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, ln(v_g)/h_logv)`.

Within that parent only:

1. construct the exact symmetric Euclidean radius graph at `r=1.0`, including self in each neighborhood;
2. define `rho_i = |N_i| / n_parent`;
3. run GUDHI `3.12.0` ToMATo with `graph_type='manual'`, `density_type='manual'`, exact neighbor lists and `rho_i` weights;
4. reconstruct every leaf, internal merge-node, and connected-component-root membership bottom-up from `leaf_labels_` and `children_`;
5. do not request a flat cluster count or persistence threshold.

The division by parent size is a common monotone density rescaling inside one fit and introduces no fitted parameter.

No global TopoModal graph is built. No event outside the current Recurrent parent can enter its local topology.

## 4. Sole representation rule — largest strict dominant-mode trunk

For a parent P:

1. Find the event with maximum local `rho_i`; exact event ID ascending breaks a density tie. Call it the **anchor event**.
2. Find the ToMATo leaf containing the anchor event.
3. Follow that leaf's unique parent chain through the complete local hierarchy to its connected-component root.
4. Consider every membership on that anchor chain, including the connected-component root, that is a **strict subset** of the original Recurrent parent P.
5. A strict-subset membership is **recurrently reportable** only if it contains at least 4 events from 2022 **and** at least 4 events from 2023.
6. If one or more recurrently reportable strict subsets exist, choose the one with the **largest member count**. Because the anchor chain is nested, this is the unique least-aggressive erosion on the dominant-mode chain. If member count is tied by exact duplicate hierarchy membership, exact membership deduplication makes the representation identical.
7. If no recurrently reportable strict subset exists, retain the original Recurrent parent membership unchanged.

Thus a connected parent normally loses only the final merge branch outside the anchor trunk; a parent spanning multiple radius-1 connected components can first reduce to the dominant component if that is the largest reportable strict anchor-chain state.

There is no Jaccard/overlap threshold, prominence threshold, density threshold, quantile, retained-fraction threshold, component quota, learned rule, or hand-weighted score.

## 5. Catalogue invariants

The successor catalogue must have exactly the same number of slots and exactly the same slot order as density-synchronous recurrent-EOM.

For parent rank r:

- successor rank is exactly r;
- successor membership is either the exact parent membership or the one frozen local-trunk subset selected above;
- successor membership must be a subset of the parent membership;
- no parent may produce more than one catalogue slot;
- no event may move from one parent to another;
- no new event may enter any slot;
- parent family identity/rank provenance must remain serialized even when displayed membership is locally eroded.

Because the parent flat catalogue is event-disjoint and each successor is a parent subset, successor memberships must remain pairwise event-disjoint.

## 6. Immutable prelabel boundary

Before shower truth is opened, serialize and SHA-256 seal `RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_PRELABEL.json` containing:

- exact parent event-universe hashes and firewall fields;
- exact parent candidate count, order and ordered-membership hash;
- for every parent: parent rank/ID, original event IDs, local topology summary, anchor event, anchor-chain node memberships/hashes, annual counts for each chain state, replacement/fallback decision, and final successor event IDs;
- complete successor ordered-membership hash;
- count of changed slots;
- confirmation that every successor is a subset of exactly its same-rank parent;
- confirmation that successor slots remain pairwise event-disjoint;
- confirmation that no truth or forbidden source was accepted by representation construction.

Truth evaluation may consume only this frozen prelabel representation plus the already-sealed GMN labels. It may not import the local-topology constructor or alter a membership after labels are visible.

If parent reproduction, topology integrity, catalogue invariants, or firewall assertions fail before the prelabel is sealed, the run is a technical no-result. A technical repair may only restore the exact frozen rule above.

## 7. Truth semantics and MRR audit

Use the exact density-synchronous parent truth semantics unchanged:

- annual shower eligibility: at least 4 events in that year;
- positive candidate/shower match: precision `>=0.5` and overlap `>=4`;
- same annual 2022 and 2023 panels;
- same full ranked catalogue length and fixed rank positions.

Report for parent and successor in each year:

- eligible shower count;
- qualified/recovered shower count over the full catalogue;
- recovered@25, @50, @100, @500;
- mean top-100 dominant precision;
- median top-500 fragmentation;
- historical recovered-only conditional MRR;
- reciprocal-rank mass `sum_q RR(q)`;
- **zero-filled eligible-query MRR** `MRR_zero = sum_q RR(q) / number_of_eligible_showers`, with RR=0 for an eligible unrecovered shower.

The historical conditional MRR is diagnostic only and is not a promotion gate.

## 8. Binding promotion contract

The first technically valid truth execution is binding.

For **each** of 2022 and 2023, all seven preservation gates must pass:

1. full-catalogue qualified/recovered showers are not lower than density-synchronous recurrent-EOM;
2. recovered@25 is not lower;
3. recovered@50 is not lower;
4. recovered@100 is not lower;
5. zero-filled eligible-query MRR is not lower;
6. mean top-100 dominant precision is not lower;
7. median top-500 fragmentation is not higher.

In addition, both global gates must pass:

8. the representation mechanism is active: at least one catalogue slot is changed by the frozen local-trunk rule;
9. zero-filled eligible-query MRR is **strictly greater in at least one of the two years**.

All 16 gates (7 x 2 annual preservation gates + 2 global gates) are mandatory.

Return exactly one binding verdict:

- `PASS_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1`, or
- `FAIL_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1`.

A PASS means local topology improved first-hit retrieval at fixed Recurrent rank without sacrificing recovery, precision, or fragmentation under the frozen annual gates. It authorizes only separately frozen transfer/validation work.

## 9. Permanent closure

A valid FAIL permanently closes this exact largest-strict-dominant-mode-trunk rule.

Do not rescue it after outcome by:

- taking a smaller/deeper anchor-chain node;
- selecting by prominence, Jaccard, density, retained fraction, precision proxy, year balance beyond the fixed support-4 floor, or a learned selector;
- changing the anchor definition;
- using a different radius, physical scale, graph, density estimator, or ToMATo cut;
- allowing more than one child per parent;
- round-robin/interleaving siblings;
- adding parent candidates beside cores;
- unioning or expanding cores;
- changing Recurrent rank order;
- changing match thresholds, candidate budget, or the zero-filled MRR definition;
- tuning by year, rank, parent size, or result.

Any later successor must be scientifically distinct and separately frozen before truth.
