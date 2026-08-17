# Recurrent-EOM condensed-tree oracle diagnostic v1

## Scientific role

This is a diagnostic on the already-exposed SonotaCo 2013/2014 development benchmark. It does not modify recurrent-EOM, choose a successor, tune a threshold, access protected `[20°,55°]`, or constitute external validation.

The previous frozen residual analysis found 58 panel-level `CANDIDATE_GENERATION_FAILURE` misses. This diagnostic asks one narrower question: are those misses truly absent from the fixed HDBSCAN hierarchy, or are recoverable structures already present in the condensed tree but discarded by recurrent-EOM EOM extraction?

## Immutable inputs

- exact label-free SonotaCo row preparation: run `31354363306`;
- exact recurrent-EOM parent pretruth: run `31829200215`, expected SHA-256 `c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef`;
- exact residual diagnostic: run `31994209058`, expected result SHA-256 `19a50655a5612e6ef00e40e0eba7c1793f5bfe298c68c082baf8b35af4856078`;
- exact already-exposed SonotaCo truth: run `31405109267`.

The HDBSCAN runtime and parameters remain the recurrent-EOM parent settings: GEO6, `min_cluster_size=10`, `min_samples=10`, Euclidean metric, zero-epsilon EOM, no single cluster.

## Pretruth hierarchy freeze

Before residual categories or truth are available, rebuild the exact two pooled route hierarchies from the immutable label-free rows. For every non-root condensed-tree cluster node, freeze:

- node ID and depth;
- full descendant event-index membership;
- member count;
- ordinary HDBSCAN stability;
- recurrent-EOM stability;
- whether the node is selected by recurrent-EOM.

The reconstruction must reproduce every selected recurrent-EOM node and its exact immutable parent membership. Failure to reproduce the parent is a technical no-result.

No truth label, residual category, target information, or pristine external data may be available during this freeze.

## Oracle diagnostic after freeze

After the complete hierarchy universe is frozen, load the already-exposed residual categories and truth. Evaluate only showers previously classified as `CANDIDATE_GENERATION_FAILURE`.

For each such shower, compute precision, recall and F1 against every frozen non-root condensed-tree cluster node, intersecting node membership with the panel truth universe exactly as the parent evaluator does.

Classification is fixed:

- `EOM_EXTRACTION_FAILURE`: at least one frozen hierarchy node has strict `F1 > 0.5` although no recurrent-EOM selected family did.
- `HIERARCHY_ABSENT`: no frozen hierarchy node has strict `F1 > 0.5`.

The best node is reporting-only and chosen deterministically by F1, recall, precision, smaller panel-intersected membership, then smaller node ID.

No threshold, HDBSCAN setting, node subset, depth rule, persistence rule, stability rule, or successor is selected by this diagnostic.

## Interpretation boundary

If extraction failures are the majority, the next independently frozen GMN-only method-development lane may investigate alternative extraction on the existing hierarchy. If hierarchy-absent failures are the majority, extraction-only work is not the dominant missing-structure remedy and the next method lane should instead address hierarchy/candidate geometry.

This diagnostic itself does not authorize a particular algorithm.

## Firewall

Protected `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY, DMS and any pristine external endpoint remain inaccessible. SonotaCo remains exposed development only.