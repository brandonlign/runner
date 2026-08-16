# OrbitTrace physical-scale modal-basin cross-scale diagnostic v1 — binding result

## 🔴 NEGATIVE — formal frozen verdict

First technically valid scientific run: `31953964066`

Job: `95181612237`

Artifact: `orbittrace-modal-basin-scale-v1` (`9265466764`)

Artifact digest: `sha256:93478dd8e5440be5b6042e90ed09a29a8a2851ce55f12ff05a6586997ee86939`

Result SHA-256: `805054340ed34320d1797615fc970f958161722059fd214983ed321f5db1ab8d`

Execution head: `75264e6737f0c7dc8eea88bf099b0287403bd87b`

Exact frozen interpretation:

`REFUTES_PHYSICAL_MODAL_BASIN_CROSS_SCALE_COHERENCE`

The run used only target-excluded GMN 2022+2023 geometry and no shower truth. The inherited physical coordinate scales, MeanShift bandwidth/rules, nested subsets, recurrent-EOM comparator, metrics, and gates were all frozen before any valid modal-basin outcome.

## Cross-scale result

Modal basins were substantially more membership-stable than exact recurrent-EOM under the frozen ~5.8k -> ~0.7k thinning stress:

- pooled candidate-unweighted mean best Jaccard: **0.7962061309** modal vs **0.6152941107** recurrent-EOM;
- median bucket candidate-unweighted mean best Jaccard: **0.8055520821** vs **0.6089001948**;
- strict bucket-level Jaccard wins: **4/4** modal;
- modal clustering was nonempty in all eight subsets.

Bucket candidate-unweighted mean best Jaccard (modal / recurrent-EOM):

- bucket 0: `0.7976769627 / 0.5606150794`;
- bucket 1: `0.8134272015 / 0.7051527695`;
- bucket 2: `0.9900000000 / 0.5504804711`;
- bucket 3: `0.6857836150 / 0.6571853102`.

The exact-restricted-match fraction was also high in the strongest modal bucket: bucket 2 had `0.8` exact modal matches versus `0.0` for recurrent-EOM.

## Decisive failed gate

The preregistered **fine-candidate non-collapse condition** required the modal method to produce at least as many eligible candidate memberships as recurrent-EOM in every fine subset.

That condition failed in exactly one of four buckets:

- bucket 2: modal **5** eligible basins vs recurrent-EOM **6** candidates.

The other three fine buckets satisfied non-collapse. Because every frozen gate was mandatory, this single failure makes the binding interpretation negative. The gate is not relaxed post-result.

## Scientific interpretation

This is not evidence that the modal membership idea lacks value. It is evidence that the **exact single-scale inherited-geometry MeanShift architecture** cannot be promoted under its preregistered structural criterion.

The unusually large cross-scale Jaccard improvement nevertheless supplies a new zero-label mechanism clue: defining memberships as attraction basins of a smooth field can be materially more sampling-stable than HDBSCAN/MST point connectivity. The remaining weakness is that a single fixed smoothing scale can eliminate one small-sample mode/candidate even when the surviving basin boundaries are extremely stable.

That observation may motivate a **genuinely distinct persistent/multiparameter modal architecture** whose scientific object is mode survival across a predeclared scale family rather than a rescue using a different MeanShift bandwidth. This exact v1 architecture may not be rerun or rescued via bandwidth, solar/radiant/speed scale, empirical rescaling, seed rule, center-merging rule, kernel, minimum basin size, subset, salt, or gate.

The first run `31934917047` remains an engineering no-result only: normalized GMN events expose the already-equivalent radiant fields as `lon/lat`, while the wrapper requested pre-normalization aliases. It failed on the first event of the first subset before MeanShift, comparator, Jaccard, or gate evaluation. The valid rerun changed only those field aliases.

Protected `[20°,55°]`, OrbitTrace target information/events, shower truth, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY and DMS were not accessed.