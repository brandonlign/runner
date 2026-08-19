# NCA OrbitTrace characterization v1

## Status and claim boundary

This is **post-reveal characterization of an already discovered parent**, not a new blind discovery, validation endpoint, or method-selection experiment.

The discovery object is frozen upstream: promoted support-pruned TopoModal + M2D replay pretruth from run `32287958931`, gzip SHA-256 `b1beb3dac03579b2ca2a0f85a2e65213e3a4826dfe0d8f038856f6b227319765`, inner SHA-256 `75dec41919072681a423d3c37d4565ca5ee19dccf86900b3b39ef5d30153ca0b`. That replay contains 8,884 target-free ranked candidates. Its later reveal established rank 82 as the 1,708-member OrbitTrace-containing parent with 18/18 exact 2022-2023 canonical members.

The purpose here is narrower: apply the already-frozen Nested Core Atlas (NCA) machinery to that unchanged parent and ask, only after the nested structure is sealed, how the canonical 18 members distribute across the frozen inner branches.

## Frozen parent

Stage 1 loads the exact sealed replay pretruth but **does not open the canonical member bundle**. It selects the already-published rank-82 row from that sealed ranking. No coordinates, target interval, canonical IDs, overlap score, or target-derived parameter are used to construct nested structure.

The parent itself is never changed, reranked, reclustered, or replaced. Its membership remains the 1,708-event promoted discovery envelope.

## Exact full-universe witness geometry

NCA's annual-density witnesses are defined on the **full 2022+2023 graph**, not on a graph recomputed only inside the parent. Restricting the graph to the parent would be scientifically wrong because an apparent inner component may in fact be connected to active outside vertices.

Stage 1 therefore reconstructs the exact support-pruned replay universe and radius graph using the frozen #1378 scanner plus the promoted support-pruned replay implementation. It computes the same per-event annual degrees as the frozen annual-density bifiltration.

For the selected parent, a specialized candidate-contained bifiltration enumerator is used. At every annual-density threshold cell it:

1. activates parent vertices under the exact global annual degrees;
2. unions active parent-parent radius edges;
3. marks a parent component invalid if any active parent-outside boundary edge exists;
4. records only support >= 4 components that remain unmarked.

This is exactly the set of full-universe bifiltration components that are wholly contained in the parent. Threshold ranges with identical candidate state may be algebraically compressed; their cell widths are summed exactly, so persistence area is unchanged.

Before live characterization, this specialized contained-component implementation must pass a synthetic equivalence audit against the frozen full-universe `bifiltration_candidates` routine: for each audited parent, membership keys and persistence areas of all globally generated witnesses contained in that parent must match exactly within floating-point tolerance.

The live parent graph must also reproduce the previously observed exact M2D transport diagnostics for this frozen parent: 1,708 vertices, 28,994 internal positive annual-density edges, and 69 positive cross-boundary edges. These are provenance checks, not fitted criteria.

## Frozen BWM -> CMR -> NCA construction

After exact contained witnesses are frozen:

- BWM is the byte-frozen PR #1385 `witness_partition` rule at NetworkX 3.6.1 / modularity resolution 1.0.
- Each reportable BWM community is an immutable seed.
- CMR is the byte-frozen PR #1387 one-shot strict weighted-majority regrowth rule. A parent member is added iff more than half of its total persistence-weighted co-witness degree points directly to the original seed (`2 a(v,C) > d(v) + 1e-15`). Newly admitted members cannot recruit others.
- Exact duplicate grown memberships are deduplicated with the frozen CMR rule.
- NCA keeps **all** resulting CMR branches beneath the unchanged parent and orders branches locally by frozen CMR internal M2D descending, then membership hash. The first is the deterministic primary branch.

No new scale, persistence threshold, modularity resolution, affinity threshold, growth depth, size cutoff, score blend, branch-count cap, target-derived parameter, or rescue sweep is introduced.

## Stage-1 seal

Before canonical IDs are opened, write and seal a target-ID-unopened artifact containing:

- exact parent identity and membership;
- full-universe graph/annual-degree provenance;
- exact contained bifiltration witness catalogue;
- BWM seeds;
- CMR/NCA branches and deterministic primary branch;
- synthetic equivalence result;
- explicit `canonical_target_ids_accessed: false`.

If the synthetic equivalence or parent provenance checks fail, stop before reveal.

## Stage-2 reveal-only characterization

Only after the Stage-1 SHA is fixed may the workflow retrieve the exact canonical bundle already used by #1378/#1380 (outer ZIP SHA-256 `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`). The reveal operation is exact trajectory-ID set intersection only.

Report, without changing any branch:

- unchanged parent overlap, precision, and recall;
- every frozen BWM seed overlap, precision, and recall;
- every frozen CMR/NCA branch overlap, precision, and recall;
- deterministic primary branch overlap, precision, and recall;
- how many of the 18 canonical 2022-2023 members are covered by the union of all frozen branches.

For descriptive diagnostics only, the output may identify the post-reveal branch with maximum canonical overlap, but it must be labeled **oracle/post-reveal descriptive only** and may not become a method choice, promotion rule, or evidence of blind rediscovery.

## Interpretation

A result in which inner branches concentrate canonical members would strengthen the mechanistic interpretation that NCA separates dense shower support from the broad high-recall discovery envelope. It would not make the child branch a new flagship and would not repair the failed ECT/EMCU general-benchmark gates. The discovery claim remains the unchanged support-pruned M2D parent; cross-survey generalization remains a separate unresolved question.
