# OrbitTrace topomodal density excess-mass cut v1 — technical invalidity record

## Verdict

**TECHNICALLY_INVALID_BEFORE_TRUTH_TOPOMODAL_EXCESS_MASS_CUT_V1**

This frozen architecture never reached a valid Stage-1 structural result and never opened shower truth.

The proposed HDBSCAN-style density-level excess-mass selection assumes that each ToMATo hierarchy state has a monotone density interval with `upper(node) >= lower(node)`, where the child/state interval ends no earlier than the parent state's enclosing merge level. That assumption is false for the exact #1284 ToMATo hierarchy.

## Binding provenance

Frozen protocol blob:
- `e98d69db77045619b552237b96da91960d594514`

Frozen initial structural source blob:
- `4980e1dd54acb11a9a59aae308d63e0e2a5ac072`

Initial pretruth run:
- workflow run `31980204272`
- artifact `9272145810`
- stopped on d128 / bucket 0 before any structural selection result or truth access

Exact-saddle implementation repair source blob:
- `49dccfa9716ec568f682c92cdf1bc2bfb22b5d0d`

Exact-saddle repair run:
- workflow run `31980353545`
- artifact `9272181658`
- stopped on d128 / bucket 0 before any structural selection result or truth access

Conditional truth evaluator had already been frozen before the structural result:
- blob `1a6101cd8c0b4eb4c8512cedd3b93df4dce14b19`
- **never executed on shower truth**

## Exact failure

Both implementations hit the same node-level contradiction at node `3643`:

- enclosing/parent merge level: `0.0010777797736662474`
- node upper merge level: `0.0005388898868331237`

Therefore the frozen lifetime condition fails:

`0.0005388898868331237 < 0.0010777797736662474`.

The first implementation inferred node merge levels from the global GUDHI persistence multiset. Because that could in principle be a node-to-persistence assignment bug, one implementation-only repair was allowed.

The repair instead computed each internal merge level directly from the exact #1284 radius graph as the highest density superlevel connecting its two child memberships: the maximum `min(rho_u, rho_v)` over graph edges crossing the two children. The same non-monotone hierarchy-state interval remained. This rules out the original persistence-indexing explanation.

## Scientific interpretation

The exact #1284 ToMATo merge hierarchy is not a condensed density hierarchy with HDBSCAN-style monotone cluster lifetimes. A hierarchy node can be nested under a parent whose graph merge density is higher than the density assigned to that node's own child merge event. Consequently the preregistered excess-mass integral is not well-defined for all hierarchy states under its stated semantics.

This is a structural incompatibility between this ToMATo hierarchy and the proposed HDBSCAN-style EOM lifetime construction, not evidence about known-shower recovery.

## Firewall and access

- shower truth was never evaluated;
- the protected solar-longitude interval 20°–55° remained excluded;
- OrbitTrace target information/events remained inaccessible;
- SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS were not accessed scientifically.

## Closure

Close this exact EOM/excess-mass lane. Do not rescue it by clipping or reordering merge levels, rematching persistence values, redefining node lifetimes, changing the stability integral, using support×lifespan, normalizing by support, selecting descendants on ties, adding a threshold, suppressing roots, blending persistence/annual/station/orbit evidence, or otherwise creating a post-result substitute for the frozen lifetime semantics.
