#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256((json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def summarize(values: list[float]) -> dict[str, Any]:
    require(values, 'empty inheritance-gap class')
    x = np.asarray(values, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite inheritance gap')
    return {
        'count': int(len(x)),
        'median_inheritance_gap': float(np.median(x)),
        'q25_inheritance_gap': float(np.percentile(x, 25.0, method='linear')),
        'q75_inheritance_gap': float(np.percentile(x, 75.0, method='linear')),
        'min_inheritance_gap': float(np.min(x)),
        'max_inheritance_gap': float(np.max(x)),
    }


def load_signal(path: Path) -> dict[str, Any]:
    require(sha(path) == SIGNAL_SHA256, '#1098 signal identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 verdict changed')
    require(r['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', '#1098 role changed')
    require(int(r['family_count']) == HDB_N and len(r['families']) == HDB_N, '#1098 HDB universe changed')
    require(r['graph_sha256'] == GRAPH_SHA256 and r['component_sha256'] == COMPONENT_SHA256, '#1098 geometry changed')
    for k in ('threshold_selected', 'top_k_selected', 'rank_window_selected', 'alternate_boolean_rule_evaluated', 'oracle_identity_hardcoded', 'target_information_access', 'target_region_events_accessed', 'maarsy_scientific_access', 'dms_scientific_access'):
        require(r[k] is False, f'#1098 forbidden flag set: {k}')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')
    return r


def freeze_mode(signal_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    signal = load_signal(signal_file)
    ids = [str(r['family_id']) for r in signal['families']]
    require(len(set(ids)) == HDB_N, 'duplicate #1098 family identity')

    joint = [r for r in signal['families'] if bool(r['joint_signal'])]
    require(len(joint) == JOINT_N, 'joint-positive population changed')
    rows = []
    for r in joint:
        require(bool(r['positive_quality_suppression']) and bool(r['component_closure_opportunity']), 'joint definition changed')
        own = float(r['v31_percentile'])
        comp = float(r['component_best_v31_percentile'])
        gap = own - comp
        require(np.isfinite(own) and np.isfinite(comp) and np.isfinite(gap), 'nonfinite inheritance statistic')
        require(0.0 <= own <= 1.0 and 0.0 <= comp <= 1.0, 'invalid percentile')
        require(gap > 0.0, 'joint family lacks strictly positive component inheritance gap')
        rows.append({
            'family_id': str(r['family_id']),
            'component_id': str(r['component_id']),
            'v31_rank': int(r['v31_rank']),
            'v31_percentile': own,
            'quality_rank': int(r['quality_rank']),
            'quality_percentile': float(r['quality_percentile']),
            'component_best_v31_percentile': comp,
            'inheritance_gap': gap,
        })
    rows.sort(key=lambda x: (int(x['v31_rank']), str(x['family_id'])))

    freeze: dict[str, Any] = {
        'verdict': 'PASS_V46_JOINT_INHERITANCE_GAP_VECTOR_FREEZE',
        'scientific_role': 'EXACT_60_JOINT_FAMILY_INHERITANCE_GAP_FROZEN_BEFORE_OUTCOME_TRUTH',
        'source_1098_run': 31457923695,
        'source_1098_artifact': 9088724826,
        'source_1098_artifact_digest': 'sha256:11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978',
        'source_signal_sha256': SIGNAL_SHA256,
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'family_count': HDB_N,
        'joint_family_count': JOINT_N,
        'statistic': 'inheritance_gap = v31_percentile - component_best_v31_percentile; larger means more borrowed component evidence',
        'families': rows,
        'truth_accessed': False,
        'literature_budget_used': False,
        'boundary_identity_used': False,
        'new_rank_or_score_evaluated': False,
        'selector_evaluated': False,
        'successor_selected': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    freeze['canonical_sha256_without_self_field'] = canonical_sha(freeze)
    out = output / 'V46_JOINT_INHERITANCE_GAP_VECTOR.json'
    out.write_text(json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': freeze['verdict'],
        'joint_family_count': JOINT_N,
        'canonical_sha256_without_self_field': freeze['canonical_sha256_without_self_field'],
        'file_sha256': sha(out),
    }, indent=2, sort_keys=True))
    return 0


def diagnose_mode(vector_file: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector = json.loads(vector_file.read_text())
    require(vector['verdict'] == 'PASS_V46_JOINT_INHERITANCE_GAP_VECTOR_FREEZE', 'inheritance-gap vector verdict changed')
    require(vector['scientific_role'] == 'EXACT_60_JOINT_FAMILY_INHERITANCE_GAP_FROZEN_BEFORE_OUTCOME_TRUTH', 'inheritance-gap vector role changed')
    require(vector['source_signal_sha256'] == SIGNAL_SHA256, 'inheritance-gap source changed')
    require(vector['graph_sha256'] == GRAPH_SHA256 and vector['component_sha256'] == COMPONENT_SHA256, 'inheritance-gap geometry changed')
    require(int(vector['joint_family_count']) == JOINT_N and len(vector['families']) == JOINT_N, 'inheritance-gap population changed')
    require(vector['truth_accessed'] is False and vector['literature_budget_used'] is False and vector['boundary_identity_used'] is False, 'inheritance-gap vector was not truth/budget independent')
    expected_canonical = str(vector['canonical_sha256_without_self_field'])
    check = dict(vector)
    del check['canonical_sha256_without_self_field']
    require(canonical_sha(check) == expected_canonical, 'inheritance-gap vector canonical identity changed')

    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((hdb_root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    fams = list(fp['families'])
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, '#950 HDB payload not pretruth')
    require(int(meta['feature_dimension']) == 71 and len(ids) == HDB_N, '#950 HDB universe changed')
    require([str(f['family_id']) for f in fams] == ids, '#950 HDB membership order changed')
    require(meta['target_information_access'] is False, '#950 target access changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, '#950 protected survey access changed')
    fam_by_id = {str(f['family_id']): f for f in fams}

    vector_rows = list(vector['families'])
    vector_ids = [str(r['family_id']) for r in vector_rows]
    require(len(set(vector_ids)) == JOINT_N and set(vector_ids) <= set(ids), 'inheritance-gap vector identity mismatch')
    for r in vector_rows:
        require(float(r['inheritance_gap']) > 0.0, 'nonpositive inheritance gap after freeze')
        require(abs(float(r['inheritance_gap']) - (float(r['v31_percentile']) - float(r['component_best_v31_percentile']))) < 1e-15, 'inheritance-gap arithmetic changed')

    by = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v22.eligible_from_year_truth(by)
    hidden: dict[str, Any] = {}
    hidden.update(by[2013]); hidden.update(by[2014])

    truth_by_id: dict[str, dict[str, Any]] = {}
    for fid in vector_ids:
        fam = fam_by_id[fid]
        t = v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v24.annual_f1_for_fixed_label(fam, str(label), by))
        else:
            f13 = f14 = 0.0
        truth_by_id[fid] = {
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        }

    diagnostic_rows = []
    for r in vector_rows:
        fid = str(r['family_id'])
        diagnostic_rows.append({
            'family_id': fid,
            'component_id': str(r['component_id']),
            'v31_rank': int(r['v31_rank']),
            'v31_percentile': float(r['v31_percentile']),
            'component_best_v31_percentile': float(r['component_best_v31_percentile']),
            'inheritance_gap': float(r['inheritance_gap']),
            **truth_by_id[fid],
        })

    annual: dict[str, Any] = {}
    pass_flags: list[bool] = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        rec = [r for r in diagnostic_rows if bool(r[rk])]
        non = [r for r in diagnostic_rows if not bool(r[rk])]
        require(rec and non, f'{year} empty inheritance-gap class')
        rec_s = summarize([float(r['inheritance_gap']) for r in rec])
        non_s = summarize([float(r['inheritance_gap']) for r in non])
        direction = bool(rec_s['median_inheritance_gap'] < non_s['median_inheritance_gap'])
        pass_flags.append(direction)
        annual[str(year)] = {
            'recoverable': rec_s,
            'nonrecoverable': non_s,
            'median_difference_recoverable_minus_nonrecoverable': float(rec_s['median_inheritance_gap'] - non_s['median_inheritance_gap']),
            'direction_pass': direction,
        }

    passed = bool(all(pass_flags))
    result = {
        'verdict': 'PASS_V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC' if passed else 'FAIL_V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC',
        'scientific_role': 'POST_V46_DIAGNOSTIC_ONLY_JOINT_INHERITANCE_GAP_NO_SUCCESSOR_EVALUATED',
        'question': 'Within the exact fixed 60 #1098 joint-positive HDB families, is median inherited-component evidence gap strictly lower among recoverable than nonrecoverable families in both exposed years?',
        'source_1098_run': 31457923695,
        'source_1098_artifact': 9088724826,
        'source_signal_sha256': SIGNAL_SHA256,
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'vector_file_sha256': sha(vector_file),
        'vector_canonical_sha256': expected_canonical,
        'joint_family_count': JOINT_N,
        'recovery_f1_threshold': RECOVERY,
        'statistic': 'inheritance_gap = v31_percentile - component_best_v31_percentile; larger means more borrowed component evidence',
        'annual_diagnostics': annual,
        'direction_supported_both_years': passed,
        'new_rank_or_score_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'group_aggregation_evaluated': False,
        'auc_evaluated': False,
        'correlation_evaluated': False,
        'regression_evaluated': False,
        'p_value_evaluated': False,
        'threshold_search': False,
        'quantile_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'alternate_statistic_search': False,
        'alternate_direction_test': False,
        'component_size_rule_search': False,
        'quality_rank_placement_retry': False,
        'component_placement_retry': False,
        'component_representative_retry': False,
        'pareto_layer_evaluated': False,
        'pairwise_dominance_evaluated': False,
        'boundary_identity_used': False,
        'boundary_rescue_list_created': False,
        'oracle_identity_used_for_ranking': False,
        'truth_aware_group_identity_used_for_ranking': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('--signal-file', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    d = sub.add_parser('diagnose')
    d.add_argument('--vector-file', type=Path, required=True)
    d.add_argument('--hdb-root', type=Path, required=True)
    d.add_argument('--truth-root', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'freeze':
        return freeze_mode(a.signal_file, a.output)
    return diagnose_mode(a.vector_file, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
