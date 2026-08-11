#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

SOURCE_RUN = 31457788803
SOURCE_ARTIFACT = 9088683367
SOURCE_ZIP_DIGEST = 'sha256:1ad3513e021136b402e8aa121faa37675e2982d57aa2a14f1bc5e28d81b61b11'
SOURCE_SIGNAL_SHA = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
CROSS_RUN = 31457199102
CROSS_ARTIFACT = 9088482597
CROSS_ZIP_DIGEST = 'sha256:c709ca3f5aaef103a1cf7668fce7241cb52a4c43b36c0263d5b6b34b8208e6c4'
CROSS_RESULT_SHA = '62ed82eeb4f10b4371ec2072af7de527482ab070866693a2230be564ebf6af35'
N_HDB = 229
JOINT_COUNT = 60
RECOVERY = 0.5


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'
    return hashlib.sha256(raw.encode()).hexdigest()


def stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    k = sum(bool(r['recoverable']) for r in rows)
    return {
        'count': n,
        'recoverable_count': int(k),
        'recoverable_fraction': (float(k / n) if n > 0 else None),
    }


def compare(threeway: list[dict[str, Any]], joint_only: list[dict[str, Any]]) -> dict[str, Any]:
    a = stats(threeway)
    b = stats(joint_only)
    pa = a['recoverable_fraction']
    pb = b['recoverable_fraction']
    infinite = bool(pa is not None and pb is not None and pb == 0.0 and pa > 0.0)
    rr = None
    if pa is not None and pb is not None and pb > 0.0:
        rr = float(pa / pb)
    rr_condition = bool(infinite or (rr is not None and rr > 1.0))
    direction = bool(pa is not None and pb is not None and pa > pb and rr_condition)
    return {
        'threeway': a,
        'joint_only': b,
        'threeway_minus_joint_only_recoverable_fraction': (float(pa - pb) if pa is not None and pb is not None else None),
        'risk_ratio': rr,
        'risk_ratio_infinite': infinite,
        'risk_ratio_condition_pass': rr_condition,
        'direction_pass': direction,
    }


def validate_1093(vector: dict[str, Any], path: Path) -> dict[str, Any]:
    require(sha(path) == CROSS_RESULT_SHA, '#1093 result SHA changed')
    cross = json.loads(path.read_text())
    require(cross['verdict'] == 'PASS_V31_CONCORDANT_INDEPENDENT_SUPPRESSION_DIAGNOSTIC', '#1093 verdict changed')
    require(cross['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CONCORDANT_SELECTOR_OR_SUCCESSOR_EVALUATED', '#1093 role changed')
    require(cross['crossroute_positive_definition'] == 'crossroute_rank_gap>0; unlinked/no usable Sugar rank is false', '#1093 sign definition changed')
    require(cross['new_rank_or_score_evaluated'] is False and cross['selector_evaluated'] is False, '#1093 not diagnostic-only')
    require(cross['replacement_rule_evaluated'] is False and cross['successor_selected'] is False, '#1093 unexpectedly selected a rule')
    require(cross['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1093 SonotaCo role changed')
    require(cross['target_information_access'] is False and cross['target_region_events_accessed'] is False, '#1093 target firewall changed')
    require(cross['maarsy_scientific_access'] is False and cross['dms_scientific_access'] is False, '#1093 protected-survey firewall changed')
    require(cross['blind_exclusion'] == [20.0, 55.0], '#1093 blind exclusion changed')
    vmap = {str(r['family_id']): r for r in vector['families']}
    require(len(vmap) == N_HDB, 'vector duplicate family')
    checked = 0
    for year in ('2013', '2014'):
        rows = cross['annual_diagnostics'][year]['groups']
        require(len(rows) == 18, f'#1093 {year} group count changed')
        for r in rows:
            fid = str(r['representative_family_id'])
            require(fid in vmap, f'#1093 representative absent from vector: {fid}')
            vr = vmap[fid]
            require(int(vr['v31_rank']) == int(r['v31_rank']), f'#1093 v31 rank mismatch: {fid}')
            require(bool(vr['crossroute_positive']) == bool(r['crossroute_positive']), f'#1093 sign mismatch: {fid}')
            a = vr['crossroute_rank_gap']
            b = r['crossroute_rank_gap']
            require((a is None) == (b is None), f'#1093 null gap mismatch: {fid}')
            if a is not None:
                require(abs(float(a) - float(b)) <= 1e-15, f'#1093 gap mismatch: {fid}')
            checked += 1
    require(checked == 36, '#1093 validation row count changed')
    return {'representative_rows_checked': checked, 'exact_crossroute_validation_pass': True}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--vector', type=Path, required=True)
    p.add_argument('--cross-result', type=Path, required=True)
    p.add_argument('--hdb-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    vector = json.loads(a.vector.read_text())
    require(vector['verdict'] == 'PASS_V31_THREEWAY_FULL_UNIVERSE_VECTOR_FREEZE', 'three-way vector verdict changed')
    require(vector['scientific_role'] == 'FULL_FIXED_229_HDB_THREEWAY_VECTOR_FROZEN_BEFORE_VALIDATION_OR_OUTCOME_AUDIT', 'three-way vector role changed')
    require(int(vector['family_count']) == N_HDB and len(vector['families']) == N_HDB, 'vector universe changed')
    require(int(vector['joint_family_count']) == JOINT_COUNT, 'joint family count changed')
    require(vector['threeway_definition'] == 'joint_signal AND crossroute_positive', 'three-way definition changed')
    for k in ('threshold_selected','top_k_selected','rank_window_selected','neighbor_aggregation_search','alternate_crossroute_statistic_search','boolean_combination_search','new_rank_or_score_evaluated','selector_order_evaluated','replacement_rule_evaluated','promotion_position_evaluated','literature_panel_evaluated','oracle_identity_hardcoded','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(vector[k] is False, f'vector firewall changed: {k}')
    require(vector['blind_exclusion'] == [20.0, 55.0], 'vector blind exclusion changed')
    expected_sha = str(vector['canonical_sha256_without_self_field'])
    check = dict(vector)
    del check['canonical_sha256_without_self_field']
    require(canonical_sha(check) == expected_sha, 'vector canonical SHA mismatch')
    validation = validate_1093(vector, a.cross_result)

    hfp = json.loads((a.hdb_root / 'family_memberships.json').read_text())
    hmeta = json.loads((a.hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    require(hfp['truth_accessed'] is False and hmeta['truth_accessed'] is False, '#950 HDB payload not pretruth')
    fams = list(hfp['families'])
    ids = list(map(str, hmeta['family_ids']))
    require(int(hmeta['feature_dimension']) == 71 and len(fams) == N_HDB and len(ids) == N_HDB, '#950 HDB universe changed')
    require([str(f['family_id']) for f in fams] == ids, '#950 family order changed')
    require(hmeta['target_information_access'] is False, '#950 target firewall changed')
    require(hmeta['maarsy_scientific_access'] is False and hmeta['dms_scientific_access'] is False, '#950 protected-survey firewall changed')
    vmap = {str(r['family_id']): dict(r) for r in vector['families']}
    require(set(vmap) == set(ids), '#950/vector universe mismatch')

    from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
    from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24

    by_year = {year: json.loads((a.truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v22.eligible_from_year_truth(by_year)
    hidden: dict[str, Any] = {}
    hidden.update(by_year[2013]); hidden.update(by_year[2014])
    truth_rows: list[dict[str, Any]] = []
    for fid, fam in zip(ids, fams):
        t = v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v24.annual_f1_for_fixed_label(fam, str(label), by_year))
            group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            group = 'NEG/' + fid
        sr = vmap[fid]
        truth_rows.append({
            'family_id': fid,
            'diagnostic_group': group,
            'joint_signal': bool(sr['joint_signal']),
            'threeway_signal': bool(sr['threeway_signal']),
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        })

    threeway_count = int(vector['threeway_family_count'])
    strict_subset = bool(0 < threeway_count < JOINT_COUNT)
    annual: dict[str, Any] = {}
    year_flags: list[bool] = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        joint = [r for r in truth_rows if r['joint_signal']]
        require(len(joint) == JOINT_COUNT, f'{year} joint family count changed')
        tf = [dict(r, recoverable=bool(r[rk])) for r in joint if r['threeway_signal']]
        jf = [dict(r, recoverable=bool(r[rk])) for r in joint if not r['threeway_signal']]
        require(len(tf) == threeway_count and len(jf) == JOINT_COUNT - threeway_count, f'{year} family split changed')
        family_cmp = compare(tf, jf)

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in truth_rows:
            grouped[str(r['diagnostic_group'])].append(r)
        grows: list[dict[str, Any]] = []
        for group, members in sorted(grouped.items()):
            grows.append({
                'diagnostic_group': group,
                'group_joint': bool(any(m['joint_signal'] for m in members)),
                'group_threeway': bool(any(m['threeway_signal'] for m in members)),
                'recoverable': bool(any(m[rk] for m in members)),
            })
        gjoint = [r for r in grows if r['group_joint']]
        tg = [r for r in gjoint if r['group_threeway']]
        jg = [r for r in gjoint if not r['group_threeway']]
        group_cmp = compare(tg, jg)
        year_gate = bool(family_cmp['direction_pass'] and group_cmp['direction_pass'])
        year_flags.append(year_gate)
        annual[str(year)] = {
            'interpretation_gate_pass': year_gate,
            'family_level_within_joint': family_cmp,
            'diagnostic_group_level_within_joint': group_cmp,
            'joint_group_count': len(gjoint),
            'threeway_group_count': len(tg),
            'joint_only_group_count': len(jg),
        }

    passed = bool(strict_subset and all(year_flags))
    result = {
        'verdict': 'PASS_V31_THREEWAY_FULL_UNIVERSE_REFINEMENT_DIAGNOSTIC' if passed else 'FAIL_V31_THREEWAY_FULL_UNIVERSE_REFINEMENT_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_INCREMENTAL_FULL_UNIVERSE_SELECTOR_REFINEMENT_DIAGNOSTIC_NO_ORDER_EVALUATED',
        'source_run': SOURCE_RUN,
        'source_artifact': SOURCE_ARTIFACT,
        'source_zip_digest': SOURCE_ZIP_DIGEST,
        'source_signal_sha256': SOURCE_SIGNAL_SHA,
        'cross_validation_run': CROSS_RUN,
        'cross_validation_artifact': CROSS_ARTIFACT,
        'cross_validation_zip_digest': CROSS_ZIP_DIGEST,
        'cross_validation_result_sha256': CROSS_RESULT_SHA,
        'vector_sha256': expected_sha,
        'family_count': N_HDB,
        'joint_family_count': JOINT_COUNT,
        'threeway_family_count': threeway_count,
        'joint_only_family_count': JOINT_COUNT - threeway_count,
        'threeway_family_fraction_of_all_hdb': float(threeway_count / N_HDB),
        'threeway_family_fraction_of_joint': float(threeway_count / JOINT_COUNT),
        'family_count_reduction_from_joint': JOINT_COUNT - threeway_count,
        'strict_nonempty_subset_of_joint': strict_subset,
        'validation_against_1093': validation,
        'annual_diagnostics': annual,
        'threeway_incremental_refinement_supported_both_years': passed,
        'interpretation_gate': 'strict nonempty subset of 60 and higher recoverability fraction plus finite RR>1 or protocol-defined infinite RR at family and diagnostic-group levels in both years',
        'new_rank_or_score_evaluated': False,
        'selector_order_evaluated': False,
        'replacement_rule_evaluated': False,
        'promotion_position_evaluated': False,
        'literature_panel_evaluated': False,
        'successor_selected': False,
        'signal_magnitude_used': False,
        'rank_gap_threshold_search': False,
        'threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'neighbor_aggregation_search': False,
        'alternate_crossroute_statistic_search': False,
        'boolean_combination_search': False,
        'or_logic_search': False,
        'component_size_search': False,
        'route_specific_rule': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
        'feature_search': False,
        'model_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'candidate_membership_changed': False,
        'candidate_generation_changed': False,
        'oracle_identity_used_for_statistic': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V31_THREEWAY_FULL_UNIVERSE_REFINEMENT_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
