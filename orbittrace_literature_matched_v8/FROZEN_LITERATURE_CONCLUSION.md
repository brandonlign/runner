# Frozen literature-method comparison conclusion

## Status

This document freezes the scientific conclusion of the literature-comparison track for the already-promoted **v8 pooled-year-centroid label-free sparse-support multiplicity** method. It is based on preregistered, target-excluded SonotaCo 2023/2025 comparisons and preserves all negative results and technical incompatibilities.

No v8 parameter was changed in response to competitor performance. The OrbitTrace target, its coordinates, members, identity, excluded-interval contents, and final target result were not accessed.

## Strongest comparison: v8 vs full Sugar on identical event rows

Authoritative exact-row workflow: `31227437130`.

The comparison used the exact frozen full-Sugar retained-master row universes and a common post-hoc mapped truth set:

- 2023: 30,414 identical event rows;
- 2025: 23,200 identical event rows.

The v8 family graph, pooled year centroids, multiplicity scores, and ranking were frozen before common shower-label access. All v8 episodes remained exactly 128 events and all integrity gates passed.

### Mean annual F1

| Year | Size bin | v8 | full Sugar | delta v8-Sugar |
|---:|:---|---:|---:|---:|
| 2023 | 4-9 | 0.076923 | 0.057692 | +0.019231 |
| 2023 | 10-24 | 0.047870 | 0.379103 | -0.331233 |
| 2023 | 25-49 | 0.057143 | 0.153432 | -0.096289 |
| 2023 | 50-99 | 0.025974 | 0.615936 | -0.589962 |
| 2023 | 100+ | 0.142393 | 0.739703 | -0.597309 |
| 2023 | all | 0.077449 | 0.387577 | -0.310127 |
| 2025 | 4-9 | 0.069930 | 0.064103 | +0.005828 |
| 2025 | 10-24 | 0.049689 | 0.239926 | -0.190236 |
| 2025 | 25-49 | 0.048986 | 0.255675 | -0.206688 |
| 2025 | 50-99 | 0.130586 | 0.416357 | -0.285771 |
| 2025 | 100+ | 0.150881 | 0.775341 | -0.624460 |
| 2025 | all | 0.084203 | 0.335825 | -0.251622 |

The preregistered material-advantage threshold was `delta >= 0.10` in both years.

**Result:** v8 fails the 4-9 superiority gate and fails the broader 4-24 superiority gate. Its numerical advantage in the 4-9 bin is only +0.019 in 2023 and +0.006 in 2025, far below the frozen material threshold. Full Sugar materially outperforms v8 in the 10-24 bin in both years and dominates overall and at larger shower sizes.

### Purity / false-positive burden

On the same exact-row Sugar panel:

- v8: 43 returned recurrent families; mean dominant-known-label precision 0.737906; 0.767442 of returned families have dominant-known-label precision >=0.5.
- Sugar 2023: 64 returned clusters; mean dominant-known-label precision 0.890505; fraction >=0.5 = 0.953125.
- Sugar 2025: 49 returned clusters; mean dominant-known-label precision 0.890344; fraction >=0.5 = 0.959184.

Thus v8 does not recover an overall precision advantage over full Sugar on this exact matched benchmark.

### Ranking / recurrence diagnostics

On the exact Sugar row universe v8 produced 43 recurrent families. Of 49 eligible recurrent known labels, 16 had qualified matches and 11 were recovered at the scaled top-K cutoff (`K=20`). MRR was 0.194673 and median qualified rank was 9.5. No eligible recurrent shower achieved minimum annual F1 >=0.5 across both years.

These diagnostics show that v8 can rank some known recurrent structure, but they do not establish superior catalogue recognition performance.

## v8 vs catalogue HDBSCAN

### Same-survey/year comparison

Authoritative matched-survey workflow: `31226030807`.

This comparison used the same SonotaCo years and blind-label universe, while each published method retained its own frozen quality cuts. It is therefore weaker than exact-row matching.

Mean-F1 deltas v8-HDBSCAN were:

- 2023: 4-9 +0.100000; 10-24 +0.060913; 25-49 +0.089933; 50-99 -0.121747; 100+ -0.508750.
- 2025: 4-9 +0.000000; 10-24 +0.057971; 25-49 +0.084544; 50-99 -0.242036; 100+ -0.562213.

The preregistered 4-9 superiority gate required a material `>=0.10` advantage in **both** years. It therefore fails: 2025 is a tie at the reported mean-F1 endpoint. HDBSCAN is substantially stronger for large showers and becomes better already in the 50-99 bin on these reports.

### Strict exact-row comparison

A blind-safe canonical HDBSCAN-2023 assignment was produced and independently verified: 26,460 unique quality-filtered rows, every ID resolved, zero rows in the excluded interval, and no labels read by the verifier.

Final strict exact-row workflow `31227299751` then ran frozen v8 on HDBSCAN's exact event universes:

- 2023: 26,460 rows, 2,410 retained quartets, 413 components;
- 2025: 19,658 rows, 1,859 retained quartets, 327 components.

Before common shower-label access, multiplicity scoring stopped because one valid recurrent family had only 64 available 2025 local-window events while frozen v8 requires an exact 128-event episode.

This is a genuine method/input compatibility limit. Reducing the episode size, dropping the family, widening the window, borrowing off-panel rows, or altering HDBSCAN quality cuts would change the frozen methods after exposure and is prohibited.

**Result:** strict full-v8 exact-row superiority over catalogue HDBSCAN is not established. The comparison is technically infeasible under the frozen methods on this SonotaCo pair. The weaker same-survey result also does not satisfy the preregistered sparse superiority gate.

## D_SH and nearest-orbit methods

D_SH / nearest-orbit comparisons remain scientifically useful for targeted association, episode-level recovery, or checking proximity to a supplied reference orbit. They are not treated here as a standalone annual catalogue discovery/ranking algorithm unless a published method specifies a complete target-free proposal and ranking procedure. No such procedure is invented for this benchmark.

Accordingly, D_SH evidence cannot be used to claim catalogue-discovery superiority for v8 or against v8.

## CMOR-style wavelet

The frozen CMOR/wavelet feasibility audit found only 199 of 324 bins with the required local radiant support, fraction 0.6142, below the preregistered 0.8 requirement. A scientifically faithful matched implementation is therefore deferred for input incompatibility. No CMOR performance comparison or superiority claim is permitted from this track.

## Compute cost

Recorded v8 exact-Sugar runtime was 56.315 s for its combined two-year scan/family/scoring benchmark. The frozen full-Sugar pipelines recorded approximately 321.36 s for 2023 and 184.84 s for 2025 (~506.20 s total).

These are not a hardware-normalized runtime study and the workflows do not perform identical computational objectives, so the ratio must not be presented as a rigorous speedup. It is nevertheless fair to state that **v8 was substantially cheaper in the recorded GitHub Actions executions**, while full Sugar achieved much better 10+ and overall recognition performance.

## Answers to the preregistered scientific questions

### Does v8 beat HDBSCAN for sparse-stream discovery?

**Not established.** On the same-survey/year benchmark v8 is better numerically for several <50-member bins but fails the preregistered 4-9 superiority gate because the 2025 4-9 result is a tie. The strict exact-row comparison cannot be completed without violating frozen v8 because HDBSCAN's filtered rows are locally too sparse for the fixed 128-event scoring episode. HDBSCAN is clearly stronger for 50+ member showers on the available matched-survey evidence.

### Does v8 beat full Sugar in the sparse regime?

**No.** On exact identical rows, v8 is only marginally higher in the extreme 4-9 bin (+0.019 and +0.006), far below the preregistered material threshold. Full Sugar materially wins 10-24 in both years and strongly wins overall and at larger sizes. Therefore v8 fails both the 4-9 and 4-24 superiority gates.

### Where does each method win or lose?

- **v8:** useful label-free cross-year recurrent proposal/ranking architecture; computationally cheaper in the recorded runs; roughly competitive with Sugar/HDBSCAN only at the very lowest 4-9 annual-member endpoint on these SonotaCo years. Its annual recognition recall/F1 is weak beyond that extreme low-count bin, and its fixed 128-event scorer creates an exact-row compatibility limitation on sufficiently sparse filtered catalogues.
- **Full Sugar:** strongest faithfully implemented comparator here for catalogue recognition. It materially dominates v8 for 10-24 and larger bins and has higher returned-cluster dominant-label purity on the exact matched panel, at substantially higher compute cost.
- **Catalogue HDBSCAN:** structurally poor at the smallest annual showers under the published min-cluster-size-100 configuration, but strong for large showers. Available evidence does not support a consistent/material v8 sparse superiority claim, and strict exact-row comparison is blocked by v8's episode-size precondition.
- **D_SH:** appropriate as targeted/association evidence, not a complete target-free catalogue discovery comparator in the form benchmarked here.
- **CMOR wavelet:** no matched performance conclusion because the available catalogue failed the preregistered input-support requirement.

## State-of-the-art claim boundary

A broad claim that v8 / OrbitTrace is **"state of the art for sparse meteor-stream discovery" is not scientifically supported** by this benchmark track.

The strongest defensible positive wording is narrower:

> The promoted v8 method is a label-free cross-year sparse-support proposal and ranking method that is competitive with the tested catalogue methods only at the extreme 4-9 annual-member scale on SonotaCo 2023/2025, while the full uncertainty-aware Sugar pipeline performs substantially better from 10 members upward and overall. A strict exact-row HDBSCAN comparison is incompatible with the frozen v8 128-event scoring requirement.

Even that statement must be presented as a result on the tested surveys/method implementations, not as universal dominance over all meteor-stream discovery literature.

## Final frozen conclusion

The literature-comparison track is complete enough to answer the primary claim question negatively. v8 remains scientifically interesting as a different sparse recurrent discovery architecture and has a compute-cost advantage in these runs, but **the evidence does not justify a state-of-the-art superiority claim**. This negative result must be preserved unchanged and must not trigger retuning of v8.
