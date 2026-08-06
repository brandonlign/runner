# SonotaCo 2025 Sugar uncertainty-aware catalogue result

The full checksum-pinned Sugar et al. uncertainty-stage reconstruction completed successfully.

- workflow run: `31075178517`;
- artifact: `8957263372`;
- artifact digest: `sha256:9df4a48f4808180d534086e560e68ae56486f60171510207acd7bd6fedeebbc9`;
- result SHA-256: `e65f09c453f30c64649314554ab44fc878ac8da4b4c726c6c79254b9717d909a`;
- verdict: `PASS_SONOTACO_2025_SUGAR_UNCERTAINTY_CATALOGUE_TRANSFER`;
- all 15 source, parser, archive, feature, epsilon, clone-count, merge, recurrence, package-version, self-test, and finite-metric gates passed.

## Frozen configuration

The catalogue contained 23,200 events after the inherited blindness and parser exclusions plus the paper's convergence-angle, speed, and speed-uncertainty filters. The transferred epsilon was `0.028705145052265017`, computed as the 23rd percentile of fourth-nearest-neighbor distances. The workflow then ran 1,000 Gaussian uncertainty-clone catalogues, DBSCAN with `min_samples=5`, and the preregistered literal 50%-overlap connected-component merge. Master clusters recurring in at least 100 runs were retained; 500 or more was classified as strong.

## Results

| Assignment | Clusters | Noise | NMI | ARI | F1>.5 | F1>.8 | Macro F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| observed deterministic DBSCAN | 64 | 0.743017 | 0.708278 | 0.758080 | 19 | 8 | 0.222874 |
| retained masters, >=100/1000 | 49 | 0.693707 | 0.751013 | 0.822827 | 23 | 13 | 0.272161 |
| strong masters, >=500/1000 | 42 | 0.696767 | 0.746935 | 0.818488 | 20 | 10 | 0.229026 |

The 1,000 clone runs produced 58,552 cluster instances and 27,408,070 qualifying overlap edges, resolving to 109 raw master components, 49 retained components, 42 strong components, and seven weak components.

Mean matched-shower F1 for retained master clusters by quality-filtered annual shower size:

- 4–9: 0.030864;
- 10–24: 0.239926;
- 25–49: 0.258805;
- 50–99: 0.406617;
- 100+: 0.777964.

## Interpretation

The uncertainty-clone, recurrence, and merge stages materially improved catalogue recovery over the deterministic published core: NMI increased from 0.708278 to 0.751013, ARI from 0.758080 to 0.822827, and the number of showers above matched F1 0.5 from 19 to 23. The improvement is real and must be credited to the full pipeline rather than treating the weak deterministic episode result as representative of Sugar et al.'s complete method.

The complete catalogue pipeline nevertheless remained weak for the smallest annual showers. Only one of 27 showers with four to nine retained events exceeded F1 0.5, and the stratum mean was 0.030864. This does not constitute an episode-scale comparison with fixed4; it supports the narrower conclusion that the methods target different regimes.

SonotaCo provides marginal RA, Dec, and speed uncertainties rather than the original ASGARD covariance model, and the paper does not publish source code or a detailed merge order. The result therefore remains labelled a preregistered survey transfer using independent marginal Gaussian draws and a deterministic connected-component interpretation of the stated 50%-overlap rule. The 20°–55° blind interval was removed before label access, so OrbitTrace was not inspected or scored.
