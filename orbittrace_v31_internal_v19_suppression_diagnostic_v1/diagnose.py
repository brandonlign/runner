#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

SOURCE_SHA256 = 'e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758'
SOURCE_RUN = 31451236076
SOURCE_ARTIFACT = 9086399760
SOURCE_DIGEST = 'sha256:a2c373df77ef7e0065c1d8aceb1f6e5826f1e30b6286f2331c362d959f1d7f69'
SOURCE_COMMIT = '2dd05e8d42a9620a015ea7ca880cc436c32a49d6'
HDB_N = 229
DEN = HDB_N - 1
EXPECTED = {
    '2013': {'budget': 11, 'macro_f1': 0.14888037368183737, 'recovered_f1_gt_0_5': 9},
    '2014': {'budget': 9, 'macro_f1': 0.15198123772301594, 'recovered_f1_gt_0_5': 9},
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values: list[float]) -> dict[str, Any]:
    require(values, 'empty v19-advantage stratum')
    x = np.asarray(values, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite v19 advantage')
    return {
        'count': int(len(x)),
        'median_v19_advantage': float(np.median(x)),
        'mean_v19_advantage': float(np.mean(x)),
        'q25_v19_advantage': float(np.percentile(x, 25.0, method='linear')),
        'q75_v19_advantage': float(np.percentile(x, 75.0, method='linear')),
        'min_v19_advantage': float(np.min(x)),
        'max_v19_advantage': float(np.max(x)),
        'positive_count': int(np.sum(x > 0.0)),
        'positive_fraction': float(np.mean(x > 0.0)),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--source-result', type=Path, required=True)
    p.add_argument('--source-execution-commit', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(sha(a.source_result) == SOURCE_SHA256, '#1046 result identity changed')
    require(a.source_execution_commit.read_text().strip() == SOURCE_COMMIT, '#1046 execution commit changed')
    src = json.loads(a.source_result.read_text())
    require(src['verdict'] == 'PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC', '#1046 verdict changed')
    require(src['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED', '#1046 role changed')
    require(src['orders_described'] == ['raw local-margin', 'exact #839 diversity', 'immutable v19', 'final v31 v19 rank-sum'], '#1046 described orders changed')
    require(set(src['annual']) == {'2013', '2014'}, '#1046 annual set changed')
    for y, exp in EXPECTED.items():
        r = src['v31_reproduction'][y]
        require(int(r['budget']) == exp['budget'], f'#1046 {y} budget changed')
        require(abs(float(r['macro_f1']) - exp['macro_f1']) < 1e-15, f'#1046 {y} macro changed')
        require(int(r['recovered_f1_gt_0_5']) == exp['recovered_f1_gt_0_5'], f'#1046 {y} recovery changed')
    for k in ('new_rank_evaluated', 'successor_selected', 'parameter_search', 'threshold_search', 'cutoff_selected', 'feature_search', 'model_search', 'k_search', 'metric_search', 'diversity_search', 'fusion_search', 'post_result_second_search', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(src[k] is False, f'#1046 forbidden flag set: {k}')
    require(src['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and src['blind_exclusion'] == [20.0, 55.0], '#1046 firewall changed')

    annual: dict[str, Any] = {}
    passes: list[bool] = []
    for y in ('2013', '2014'):
        rows = list(src['annual'][y]['rows'])
        surfaced = [r for r in rows if bool(r['v31_surfaced_recoverable'])]
        missed = [r for r in rows if bool(r['recoverable_but_missed'])]
        require(surfaced and missed, f'{y} empty surfaced/missed stratum')
        require(all(bool(r['candidate_recoverable']) for r in surfaced + missed), f'{y} surfaced/missed row not candidate-recoverable')

        def derive(r: dict[str, Any]) -> dict[str, Any]:
            dr = int(r['best_candidate_diversity_rank'])
            vr = int(r['best_candidate_v19_rank'])
            require(1 <= dr <= HDB_N and 1 <= vr <= HDB_N, 'rank outside fixed HDB universe')
            adv = float((dr - vr) / DEN)
            return {
                'label': str(r['label']),
                'best_fixed_candidate_family_id': str(r['best_fixed_candidate_family_id']),
                'best_fixed_candidate_f1': float(r['best_fixed_candidate_f1']),
                'best_candidate_diversity_rank': dr,
                'best_candidate_v19_rank': vr,
                'best_candidate_fused_rank': int(r['best_candidate_fused_rank']),
                'v19_advantage': adv,
            }

        srows = [derive(r) for r in surfaced]
        mrows = [derive(r) for r in missed]
        ss = summary([r['v19_advantage'] for r in srows])
        ms = summary([r['v19_advantage'] for r in mrows])
        direction = bool(ms['median_v19_advantage'] > 0.0 and ms['median_v19_advantage'] > ss['median_v19_advantage'])
        passes.append(direction)
        annual[y] = {
            'surfaced_recoverable': ss,
            'recoverable_but_missed': ms,
            'median_difference_missed_minus_surfaced': float(ms['median_v19_advantage'] - ss['median_v19_advantage']),
            'direction_pass': direction,
            'surfaced_rows': srows,
            'missed_rows': mrows,
        }

    passed = bool(all(passes))
    result = {
        'verdict': 'PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC' if passed else 'FAIL_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC',
        'scientific_role': 'POST_V31_INTERNAL_CONSTITUENT_DISAGREEMENT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_EVALUATED',
        'question': 'Among #1046 candidate-recoverable HDB shower groups, do recoverable-but-missed groups have a larger positive v19-over-local-diversity rank advantage than surfaced recoverable groups in both exposed years?',
        'source_run': SOURCE_RUN,
        'source_artifact': SOURCE_ARTIFACT,
        'source_artifact_digest': SOURCE_DIGEST,
        'source_result_sha256': SOURCE_SHA256,
        'source_execution_commit': SOURCE_COMMIT,
        'hdb_family_count': HDB_N,
        'statistic': 'v19_advantage=((best_candidate_diversity_rank-1)/228)-((best_candidate_v19_rank-1)/228); positive means immutable v19 ranks the frozen #1046 candidate better',
        'annual_diagnostics': annual,
        'direction_supported_both_years': passed,
        'new_rank_or_score_used_for_ranking': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'literature_panel_evaluated': False,
        'successor_selected': False,
        'rank_gap_threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'effect_size_cutoff_search': False,
        'alternate_constituent_pair_search': False,
        'absolute_gap_search': False,
        'ratio_search': False,
        'log_transform_search': False,
        'raw_local_substitution_search': False,
        'fused_rank_difference_search': False,
        'fusion_weight_search': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'metric_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'source_quota_selected': False,
        'oracle_identity_hardcoded': False,
        'boundary_rescue_list_created': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
