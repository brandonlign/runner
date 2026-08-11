#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from orbittrace_v31_local_geometry_margin_oof_v1 import train_evaluate as v31

PARENT = {
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
}
PARENT_SOURCE_BLOB = '917e3cd6f9310ca1282e0efa58ed0924d03ed4da'
RANKER_SOURCE_SHA256 = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def panel_map(result: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    rows = list(result['panels'])
    require(len(rows) == 4, 'panel count changed')
    out = {(str(r['comparator']), int(r['year'])): r for r in rows}
    require(set(out) == set(PARENT), 'panel identity changed')
    return out


def run_v31(
    *,
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    output: Path,
    no_diversity: bool,
) -> tuple[dict[str, Any], list[dict[str, float]]]:
    output.mkdir(parents=True, exist_ok=True)
    old_argv = list(sys.argv)
    original_load_module = v31.v22.load_module
    patch_calls: list[dict[str, float]] = []

    if no_diversity:
        def patched_load_module(path: Path, name: str):
            mod = original_load_module(path, name)
            original_diversity_order = mod.diversity_order

            def diversity_order_zero_penalty(scores, mat, lam, scale, tie):
                requested_lambda = float(lam)
                requested_scale = float(scale)
                require(abs(requested_lambda - 0.8) < 1e-15, 'v31 diversity lambda call changed')
                require(abs(requested_scale - 1.0) < 1e-15, 'v31 diversity scale call changed')
                patch_calls.append({
                    'requested_lambda': requested_lambda,
                    'effective_lambda': 0.0,
                    'scale': requested_scale,
                })
                return original_diversity_order(scores, mat, 0.0, requested_scale, tie)

            mod.diversity_order = diversity_order_zero_penalty
            return mod

        v31.v22.load_module = patched_load_module

    try:
        sys.argv = [
            'train_evaluate.py',
            '--sugar-root', str(sugar_root),
            '--hdbscan-root', str(hdbscan_root),
            '--truth-root', str(truth_root),
            '--ranker-source', str(ranker_source),
            '--output', str(output),
        ]
        rc = v31.main()
        require(rc == 0, 'frozen v31 engine failed')
    finally:
        sys.argv = old_argv
        v31.v22.load_module = original_load_module

    result_path = output / 'V31_LOCAL_GEOMETRY_OOF_RESULT.json'
    require(result_path.is_file(), 'frozen v31 result missing')
    result = json.loads(result_path.read_text())
    if no_diversity:
        require(len(patch_calls) == 2, 'expected exactly one diversity call per route')
    else:
        require(not patch_calls, 'parent unexpectedly patched')
    return result, patch_calls


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--sugar-root', type=Path, required=True)
    p.add_argument('--hdbscan-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--ranker-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(v31.v22.sha(a.ranker_source) == RANKER_SOURCE_SHA256, '#839 ranker source changed')

    parent, parent_calls = run_v31(
        sugar_root=a.sugar_root,
        hdbscan_root=a.hdbscan_root,
        truth_root=a.truth_root,
        ranker_source=a.ranker_source,
        output=a.output / 'parent_v31',
        no_diversity=False,
    )
    require(parent['verdict'] == 'FAIL_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT', 'v31 parent verdict changed')
    require(parent['strict_whole_shower_oof'] is True, 'v31 OOF semantics changed')
    require(parent['feature_dimension'] == 71 and parent['nearest_k'] == 1, 'v31 geometry changed')
    require(parent['distance'] == 'ordinary Euclidean across all 71 fold-training standardized dimensions', 'v31 distance changed')
    require(parent['annual_combiner'] == 'min(margin_2013,margin_2014)', 'v31 annual combiner changed')
    require(parent['candidate_membership_changed'] is False and parent['pretruth_feature_changed'] is False, 'v31 universe changed')
    require(parent['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'v31 SonotaCo role changed')
    require(parent['target_information_access'] is False and parent['target_region_events_accessed'] is False, 'v31 target firewall changed')
    require(parent['maarsy_scientific_access'] is False and parent['dms_scientific_access'] is False, 'v31 protected survey firewall changed')
    require(parent['blind_exclusion'] == [20.0, 55.0], 'v31 blind exclusion changed')
    require(parent_calls == [], 'parent diversity instrumentation changed')

    pmap = panel_map(parent)
    for key, (expected_f1, expected_recovered) in PARENT.items():
        row = pmap[key]
        require(abs(float(row['candidate_macro_f1']) - expected_f1) < 1e-12, f'{key} v31 macro F1 changed')
        require(int(row['candidate_recovered_f1_gt_0_5']) == expected_recovered, f'{key} v31 recovery changed')

    candidate, patch_calls = run_v31(
        sugar_root=a.sugar_root,
        hdbscan_root=a.hdbscan_root,
        truth_root=a.truth_root,
        ranker_source=a.ranker_source,
        output=a.output / 'v50_engine',
        no_diversity=True,
    )

    # Everything except the local diversity penalty must remain exact-v31 semantics.
    for key in (
        'feature_dimension', 'recovery_f1_threshold', 'nearest_k', 'distance', 'scaling',
        'annual_margin', 'annual_combiner', 'strict_whole_shower_oof',
        'candidate_membership_changed', 'pretruth_feature_changed', 'fusion',
        'promotion_variant', 'sonotaco_role', 'maarsy_scientific_access',
        'dms_scientific_access', 'target_information_access',
        'target_region_events_accessed', 'blind_exclusion',
    ):
        require(candidate[key] == parent[key], f'non-diversity v31 field changed: {key}')

    require(all(abs(float(c['requested_lambda']) - 0.8) < 1e-15 for c in patch_calls), 'unexpected requested diversity lambda')
    require(all(abs(float(c['effective_lambda'])) < 1e-15 for c in patch_calls), 'nonzero v50 diversity penalty')
    require(all(abs(float(c['scale']) - 1.0) < 1e-15 for c in patch_calls), 'v50 diversity scale changed')

    panels = list(candidate['panels'])
    wins = int(sum(bool(r['superiority_pair_pass']) for r in panels))
    require(wins == int(candidate['panel_wins']), 'v50 panel-win mismatch')
    passed = bool(wins == 4)

    result: dict[str, Any] = {
        'scientific_stage': 'EXPOSED_SONOTACO_V50_NO_DIVERSITY_LOCAL_GEOMETRY_V1',
        'verdict': 'PASS_V50_NO_DIVERSITY_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V50_NO_DIVERSITY_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'remove inherited #839 centroid-diversity penalty by delegating exact diversity_order call from lambda=0.8 to lambda=0.0; all v31 geometry, tie, annual-min, v19 fusion and evaluation semantics unchanged',
        'parent': 'v31 local-geometry-margin OOF',
        'parent_source_blob': PARENT_SOURCE_BLOB,
        'parent_reproduction_pass': True,
        'parent_controls': [
            {
                'comparator': route,
                'year': year,
                'macro_f1': float(pmap[(route, year)]['candidate_macro_f1']),
                'recovered_f1_gt_0_5': int(pmap[(route, year)]['candidate_recovered_f1_gt_0_5']),
            }
            for route, year in (('sugar', 2013), ('sugar', 2014), ('hdbscan', 2013), ('hdbscan', 2014))
        ],
        'ranker_source_sha256': RANKER_SOURCE_SHA256,
        'feature_dimension': int(candidate['feature_dimension']),
        'nearest_k': int(candidate['nearest_k']),
        'distance': candidate['distance'],
        'scaling': candidate['scaling'],
        'annual_margin': candidate['annual_margin'],
        'annual_combiner': candidate['annual_combiner'],
        'strict_whole_shower_oof': True,
        'diversity_parent_lambda': 0.8,
        'diversity_effective_lambda': 0.0,
        'diversity_scale': 1.0,
        'diversity_penalty_removed': True,
        'diversity_patch_calls': patch_calls,
        'tie_semantics_changed': False,
        'centroid_metric_changed': False,
        'local_score_changed': False,
        'v19_fusion_changed': False,
        'fusion': candidate['fusion'],
        'panel_wins': wins,
        'panels': panels,
        'order_diagnostics': candidate['order_diagnostics'],
        'candidate_membership_changed': False,
        'pretruth_feature_changed': False,
        'diversity_coefficient_search': False,
        'diversity_scale_search': False,
        'route_year_diversity_rule': False,
        'second_diversity_pass': False,
        'k_search': False,
        'metric_search': False,
        'scaling_search': False,
        'feature_search': False,
        'threshold_search': False,
        'annual_combiner_search': False,
        'fusion_search': False,
        'fusion_weight_search': False,
        'rank_algebra_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'budget_specific_rule': False,
        'quality_component_rescue': False,
        'oracle_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V50_NO_DIVERSITY_LOCAL_GEOMETRY_RESULT.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'panel_wins': wins,
        'panels': panels,
        'order_diagnostics': result['order_diagnostics'],
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
