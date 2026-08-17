# Fixed-scale TopoModal flagship — binding matched literature benchmark result

## 🔴 NEGATIVE for universal matched-literature superiority

Binding workflow run: `31984510791`

Binding result artifact:

- artifact ID: `9273347293`
- artifact name: `orbittrace-topomodal-flagship-matched-literature-result-v1-r4`
- artifact digest: `sha256:a287385283c48579c85fb70c260bacdae95b673658b21a37e4e8cda7807dcf6b`
- result JSON SHA-256: `41fbc2ccf000949a6308f72e2cf210af2e3b8d1f22962725754e17f370f49df9`

Pretruth six-panel freeze:

- artifact ID: `9273336433`
- artifact name: `orbittrace-topomodal-flagship-literature-pretruth-freeze-v1-r4`
- artifact digest: `sha256:26ec9eac4b8c4ca6e98caf83cd674369e8293909571deabfcd80c3fca1962a49`

Exact verdict:

`FAIL_TOPOMODAL_FLAGSHIP_MATCHED_LITERATURE_V1`

The frozen flagship won **4 of 6** matched SonotaCo 2013/2014 panels. The all-six superiority gate therefore fails and must not be relaxed.

| Literature comparator | Year | TopoModal macro-F1 | Literature macro-F1 | TopoModal recovered F1>0.5 | Literature recovered F1>0.5 | Panel |
|---|---:|---:|---:|---:|---:|---|
| Sugar uncertainty-aware DBSCAN | 2013 | **0.3688927121** | 0.2037265747 | **22** | 13 | **WIN** |
| Sugar uncertainty-aware DBSCAN | 2014 | **0.3744117679** | 0.2590152773 | **22** | 15 | **WIN** |
| Published catalogue HDBSCAN | 2013 | 0.1641758861 | **0.1681717489** | 9 | **10** | **LOSS** |
| Published catalogue HDBSCAN | 2014 | 0.1478277890 | **0.1568959558** | 7 | **9** | **LOSS** |
| Rudawska-Jenniskens D_SH single linkage | 2013 | **0.2638102363** | 0.2528566656 | 16 | 16 | **WIN** |
| Rudawska-Jenniskens D_SH single linkage | 2014 | **0.3027155948** | 0.2341280610 | **19** | 13 | **WIN** |

## Scientific interpretation

The fixed-scale TopoModal flagship **does outperform two important literature families** under the frozen matched benchmark:

- Sugar et al.-style uncertainty-aware DBSCAN: 2/2 wins, with large macro-F1 and recovered-shower gains;
- classical Southworth-Hawkins D_SH single linkage: 2/2 wins, including a strong 2014 gain.

However, it **does not outperform the exact published 2025 catalogue-HDBSCAN implementation** on these exposed SonotaCo panels. The differences are modest in macro-F1 but adverse in both years, and recovered-shower count is also lower (`9 vs 10`; `7 vs 9`). Therefore the paper must not claim that TopoModal generally beats the literature or represents demonstrated state-of-the-art performance across all included comparators.

This result does not erase the separate positive sparse-sample result. On target-excluded GMN scale stress, TopoModal remains substantially more stable across ~5.8k -> ~0.7k thinning and recovers substantially more known showers than the fixed-support ordinary HDBSCAN comparator at matched complete-catalogue budgets. That is a different scientific claim from beating the catalogue-scale published HDBSCAN implementation on SonotaCo.

## Supportable paper claims

Appropriate:

> We introduce a novel fixed-physical-scale topological modal methodology for sparse meteoroid-stream detection. In matched SonotaCo benchmarks it outperformed uncertainty-aware DBSCAN and classical D_SH single linkage, while the published catalogue-HDBSCAN method retained a modest advantage; under controlled sparse-sample stress, TopoModal showed substantially stronger cross-scale stability and recovery than fixed-support HDBSCAN.

Not supported:

- `TopoModal beats the literature.`
- `TopoModal is state of the art across established meteor-stream methods.`
- `TopoModal outperforms published HDBSCAN.`
- any claim of pristine external validation from these SonotaCo panels.

## Closure

This benchmark is binding. No TopoModal radius, physical scale, support floor, density, hierarchy, candidate ordering, literature parameter, quality predicate, matched budget, truth mapping, metric, or panel definition may be changed in response to the two HDBSCAN losses.

The flagship method remains frozen. Future work should characterize the scientific tradeoff rather than restart result-informed method search.

## Firewall

The binding result preserved:

- complete six-panel method outputs frozen before truth;
- protected solar longitude `[20.0,55.0]` excluded;
- `truth_access_before_pretruth=false`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `post_result_parameter_search=false`.
