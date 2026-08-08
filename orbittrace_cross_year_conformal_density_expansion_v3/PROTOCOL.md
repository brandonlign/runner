# OrbitTrace cross-year conformal-density expansion v3 — frozen development protocol

## Purpose

The v1 and v2 cross-year membership experiments established two facts on the exact target-excluded v8 development universe:

1. v8 recurrent families are high-value seeds whose membership is severely incomplete: both expansion experiments produced very large gains in annual and matched-family F1, especially for large showers;
2. an absolute radius/witness rule is structurally wrong for final membership. v1 added 174,594 events, and v2 still added 168,808 even after requiring two witnesses. In v2 the median accepted event had 62 supporting other-year seeds in 2022 and 100 in 2023, proving that absolute support count is dominated by family seed density/size rather than membership specificity.

v3 therefore tests one density-normalized successor. It keeps the exact v8 discovery/ranking stage and exact v2 two-witness geometry, but evaluates the candidate's second-nearest other-year seed distance relative to the **source family's own leave-one-out second-neighbor spacing distribution** using a finite-sample conformal p-value.

## Frozen base and prerequisites

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- Reproduce exactly the 226 v8 recurrent families, pooled-year centroids, 128-event scores, multiplicity order, and all passed-v8 pre-expansion metrics.
- v1 run `31233617751` / artifact `9014893340` and v2 run `31234638558` / artifact `9015207416` remain immutable no-go records.
- The exact v2 artifact must be SHA-256 verified before any v3 scientific-value access and must reproduce the observed absolute-witness failure mechanism.
- v8 proposal generation, components, family graph, radius 1.5, centroids, scores, and ranking remain unchanged.

## Frozen conformal membership rule

For each recurrent family and each target year independently:

1. use only the family's **original v8 seed events from the other year** as the source sample;
2. require at least four source seeds (inherited fixed4 component support makes this a structural expectation, not a selected threshold);
3. for every source seed, compute its exact frozen-metric distance to its **second-nearest other source seed** after excluding itself; these leave-one-out `d2` values form the family-specific calibration sample;
4. for every non-seed target-year event, compute `d1` and `d2`, its exact distances to the nearest and second-nearest source seeds;
5. retain the exact inherited hard ceiling `d2 <= 1.5`; this is the v2 two-witness condition and is not retuned;
6. compute the conservative conformal membership p-value
   `p = (1 + #{source leave-one-out d2 >= target d2}) / (n_source + 1)`;
7. accept the family-event pair only when `p > 0.05`;
8. if one event is accepted by multiple families, preserve v1/v2 exclusive assignment: choose the family with smallest exact `d1`, ties by stable family ID;
9. newly assigned events never become support; original v8 seeds are never removed.

The conformal level `0.05` is fixed before execution as the conventional finite-sample rejection level. No alternative alpha is evaluated. The second-neighbor order is inherited directly from the failed v2 two-witness formulation and is not searched.

## Why this is a distinct scientific successor

v3 does not make the radius smaller. A fixed radius was already shown to be density-confounded. Instead, each family supplies its own label-free reference scale through leave-one-out seed spacing. A candidate must be at least as locally supported as the non-extreme 95% of that family's own observed source seeds. This directly attacks v2's measured failure: large families no longer gain membership solely because many seeds happen to fall inside the same absolute ball.

## Prohibited alternatives

This one-shot experiment does not authorize:

- alpha values other than 0.05;
- first-, third-, fourth-, or searched neighbor order;
- any radius other than the inherited hard ceiling 1.5;
- family-size weights, manual caps, expansion-ratio caps, score thresholds, or label-conditioned pruning;
- same-year support, recursive growth, reranking, orbital/D_SH membership, or trajectory fitting;
- post-hoc rescue of families that fail the conformal gate.

A failure closes this exact other-year nearest-neighbor conformal formulation. It does not authorize alpha or k tuning from the result.

## Development panel and blindness

- Exact target-excluded GMN 2022 + 2023 development corpus inherited from v8.
- Solar longitude 20°–55° is removed before proposals, labels, scoring, or evaluation by the frozen parser.
- The entire expanded membership payload and v8 ranking are SHA-256 frozen before known-shower labels are evaluated.
- No OrbitTrace coordinates, identity, members, target-region events, Stage A/B output, or reveal may be accessed.
- The already-seen SonotaCo literature benchmark is not used to choose alpha, neighbor order, or any v3 parameter.

## Scientific gates

Use the exact v1/v2 promotion standard without relaxation:

1. multiplicity recovery@100 after expansion `>= 58`;
2. qualified matches after expansion `>= 95`;
3. top-100 dominant precision after expansion `>= 0.65`;
4. expanded macro F1 `>= v8 macro F1 + 0.05`;
5. all-shower annual mean-F1 gain `>= +0.10` in both 2022 and 2023;
6. 4–9 annual mean-F1 delta `>= -0.02` in both years;
7. at least one moderate/large bin (10–24, 25–49, 50–99, 100+) has mean-F1 gain `>= +0.10` in both years.

Every v8 reproduction, blindness, exact-128-episode, Brown-equivalence, fixed-radius, other-year-only, no-recursion, exclusive-assignment, exact conformal formula, alpha=0.05, k=2, and pre-label-hash integrity gate must pass.

## Decision rule

Promote v3 only if every integrity and scientific gate passes in this one execution. Otherwise preserve it as a no-go. A pass authorizes only a separately frozen prospective validation and later matched literature benchmark; it does not authorize OrbitTrace reveal by itself.
