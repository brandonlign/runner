#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24

SIGNAL_SHA256 = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
GRAPH_SHA256 = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
RECOVERY = 0.5
HDB_N = 229
JOINT_N = 60


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def summary(values: list[float]) -> dict[str, Any]:
    require(values, 'empty placement class')
    x = np.asarray(values, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite placement statistic')
    return {
        'count': int(len(x)),
        'median_component_best_v31_percentile': float(np.median(x)),
        'q25_component_best_v31_percentile': float(np.percentile(x, 25.0, method='linear')),
        'q75_component_best_v31_percentile': float(np.percentile(x, 75.0, method='linear')),
        'min_component_best_v31_percentile': float(np.min(x)),
        'max_component_best_v31_percentile': float(np.max(x)),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--signal-file', type=Path, required=True)
    p.add_argument('--hdb-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(sha(a.signal_file) == SIGNAL_SHA256, '#1098 signal identity changed')
    signal = json.loads(a.signal_file.read_text())
    require(signal['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 signal verdict changed')
    require(int(signal['family_count']) == HDB_N and len(signal['families']) == HDB_N, 'HDB signal universe changed')
    require(signal['graph_sha256'] == GRAPH_SHA256 and signal['component_sha256'] == COMPONENT_SHA256, 'graph/component identity changed')
    require(signal['scientific_role'] == 'PRETRUTH_FIXED_229_HDB_FAMILY_JOINT_SIGNAL_ONLY', '#1098 signal role changed')
    for k in ('threshold_selected', 'top_k_selected', 'rank_window_selected', 'alternate_boolean_rule_evaluated', 'oracle_identity_hardcoded', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(signal[k] is False, f'#1098 forbidden flag set: {k}')
    require(signal['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')

    signal_rows = list(signal['families'])
    ids_signal = [str(r['family_id']) for r in signal_rows]
    require(len(set(ids_signal)) == HDB_N, 'duplicate signal family id')
    joint_rows = [r for r in signal_rows if bool(r['joint_signal'])]
    require(len(joint_rows) == JOINT_N, 'joint-positive population changed')
    for r in joint_rows:
        require(bool(r['positive_quality_suppression']) and bool(r['component_closure_opportunity']), 'joint definition changed')
        x = float(r['component_best_v31_percentile'])
        require(np.isfinite(x) and 0.0 <= x <= 1.0, 'invalid component-best percentile')

    meta = json.loads((a.hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((a.hdb_root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    fams = list(fp['families'])
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, 'HDB payload not pretruth')
    require(int(meta['feature_dimension']) == 71 and len(ids) == HDB_N, 'HDB pretruth universe changed')
    require([str(f['family_id']) for f in fams] == ids, 'HDB membership order changed')
    require(set(ids_signal) == set(ids), '#1098 signal and HDB family universes differ')
    require(meta['target_information_access'] is False, 'pretruth target access changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, 'pretruth protected survey access changed')

    by = {year: json.loads((a.truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v22.eligible_from_year_truth(by)
    hidden: dict[str, Any] = {}
    hidden.update(by[2013]); hidden.update(by[2014])

    truth_by_id: dict[str, dict[str, Any]] = {}
    for fid, fam in zip(ids, fams):
        t = v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v24.annual_f1_for_fixed_label(fam, str(label), by))
            group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            group = 'NEG/' + fid
        truth_by_id[fid] = {
            'diagnostic_group': group,
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        }

    diagnostic_rows = []
    for s in joint_rows:
        fid = str(s['family_id'])
        require(fid in truth_by_id, 'joint family missing truth attachment')
        diagnostic_rows.append({
            'family_id': fid,
            'component_id': str(s['component_id']),
            'component_best_v31_percentile': float(s['component_best_v31_percentile']),
            'v31_rank': int(s['v31_rank']),
            'quality_rank': int(s['quality_rank']),
            **truth_by_id[fid],
        })
    require(len(diagnostic_rows) == JOINT_N, 'joint diagnostic population changed')

    annual: dict[str, Any] = {}
    pass_flags: list[bool] = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        rec = [r for r in diagnostic_rows if bool(r[rk])]
        non = [r for r in diagnostic_rows if not bool(r[rk])]
        require(rec and non, f'{year} empty family diagnostic class')
        rec_s = summary([float(r['component_best_v31_percentile']) for r in rec])
        non_s = summary([float(r['component_best_v31_percentile']) for r in non])
        family_pass = bool(rec_s['median_component_best_v31_percentile'] < non_s['median_component_best_v31_percentile'])

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in diagnostic_rows:
            grouped[str(r['diagnostic_group'])].append(r)
        group_rows = []
        for g, rs in sorted(grouped.items()):
            group_rows.append({
                'diagnostic_group': g,
                'joint_family_count': len(rs),
                'group_component_best_v31_percentile': float(min(float(x['component_best_v31_percentile']) for x in rs)),
                'recoverable': bool(any(bool(x[rk]) for x in rs)),
            })
        grec = [r for r in group_rows if r['recoverable']]
        gnon = [r for r in group_rows if not r['recoverable']]
        require(grec and gnon, f'{year} empty group diagnostic class')
        grec_s = summary([float(r['group_component_best_v31_percentile']) for r in grec])
        gnon_s = summary([float(r['group_component_best_v31_percentile']) for r in gnon])
        group_pass = bool(grec_s['median_component_best_v31_percentile'] < gnon_s['median_component_best_v31_percentile'])
        annual[str(year)] = {
            'family_level': {
                'recoverable': rec_s,
                'nonrecoverable': non_s,
                'median_difference_recoverable_minus_nonrecoverable': float(rec_s['median_component_best_v31_percentile'] - non_s['median_component_best_v31_percentile']),
                'direction_pass': family_pass,
            },
            'diagnostic_group_level': {
                'group_count': len(group_rows),
                'recoverable': grec_s,
                'nonrecoverable': gnon_s,
                'median_difference_recoverable_minus_nonrecoverable': float(grec_s['median_component_best_v31_percentile'] - gnon_s['median_component_best_v31_percentile']),
                'direction_pass': group_pass,
            },
        }
        pass_flags.extend([family_pass, group_pass])

    passed = bool(all(pass_flags))
    result = {
        'verdict': 'PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC' if passed else 'FAIL_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC',
        'scientific_role': 'POST_V42_DIAGNOSTIC_ONLY_CONDITIONAL_COMPONENT_PLACEMENT_NO_SUCCESSOR_EVALUATED',
        'question': 'Within the fixed 60 joint-positive HDB candidates, is lower frozen component-best exact-v31 percentile associated with annual recoverability at both family and strict-group levels in both years?',
        'source_1098_run': 31457923695,
        'source_1098_artifact': 9088724826,
        'source_1098_artifact_digest': 'sha256:11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978',
        'source_signal_sha256': SIGNAL_SHA256,
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'joint_family_count': JOINT_N,
        'placement_statistic': 'component_best_v31_percentile from frozen #1098 signal; lower is better',
        'annual_diagnostics': annual,
        'placement_direction_supported_both_years_both_levels': passed,
        'new_rank_or_score_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'quality_rank_placement_retry': False,
        'threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'component_size_statistic_search': False,
        'q_calibration_search': False,
        'alternate_component_aggregation_search': False,
        'suppression_magnitude_search': False,
        'promotion_gain_search': False,
        'route_specific_rule': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
        'graph_or_component_redefinition': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'oracle_identity_hardcoded': False,
        'truth_aware_group_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (a.output / 'V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
