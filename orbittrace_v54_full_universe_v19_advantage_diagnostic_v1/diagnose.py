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

HDB_N = 229
RECOVERY = 0.5
DENOM = HDB_N - 1

V1157_RESULT_SHA256 = '165f094fafa0f0f1e78b57dca83fbbf2aeee5d15bdefc9ba4b6f349d495e0aa7'
V1157_VERDICT = 'PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC'
V1157_ARTIFACT_DIGEST = 'sha256:2441cb6fb4401601976ada3feb59db6cf658bc8eba4f0e5a3bc06b743aa8c167'

V51_VECTOR_SHA256 = '5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc'
V51_VECTOR_CANONICAL = '0e13b3f9e6b791a13a3e90d853f8704573b1264dffcb67236e6423491ad70020'
LOCAL_ORDER_SHA256 = '9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595'
V19_ORDER_SHA256 = 'e1e82ad70fb8c575ee7ee269906668931f07cbe3375c15ab84b0717b1f2c85dc'
V31_FUSED_SHA256 = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'

MIN_ADV_NUM = -176
MAX_ADV_NUM = 160
POSITIVE_N = 104
NEGATIVE_N = 124
ZERO_N = 1


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256(
        (json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    ).hexdigest()


def dump_with_canonical(path: Path, payload: dict[str, Any]) -> tuple[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    core = dict(payload)
    core.pop('canonical_sha256_without_self_field', None)
    can = canonical_sha(core)
    payload = dict(core)
    payload['canonical_sha256_without_self_field'] = can
    raw = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest(), can


def verify_v1157(path: Path) -> dict[str, Any]:
    require(sha(path) == V1157_RESULT_SHA256, '#1157 diagnostic result identity changed')
    r = json.loads(path.read_text())
    require(r['verdict'] == V1157_VERDICT, '#1157 verdict changed')
    require(
        r['scientific_role'] == 'POST_V31_INTERNAL_CONSTITUENT_DISAGREEMENT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_EVALUATED',
        '#1157 scientific role changed',
    )
    require(r['direction_supported_both_years'] is True, '#1157 direction no longer supported')
    require(int(r['hdb_family_count']) == HDB_N, '#1157 HDB universe changed')
    require(r['literature_panel_evaluated'] is False, '#1157 unexpectedly evaluated a literature panel')
    for k in (
        'selector_evaluated', 'replacement_rule_evaluated', 'successor_selected',
        'rank_gap_threshold_search', 'rank_window_search', 'top_k_search',
        'fusion_weight_search', 'alternate_constituent_pair_search', 'absolute_gap_search',
        'ratio_search', 'log_transform_search', 'raw_local_substitution_search',
        'fused_rank_difference_search', 'effect_size_cutoff_search', 'post_result_second_search',
        'target_information_access', 'target_region_events_accessed',
        'maarsy_scientific_access', 'dms_scientific_access',
    ):
        require(r[k] is False, f'#1157 firewall/search flag changed: {k}')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1157 SonotaCo role changed')
    require(r['blind_exclusion'] == [20.0, 55.0], '#1157 blind exclusion changed')
    return r


def verify_v51(path: Path) -> dict[str, Any]:
    require(sha(path) == V51_VECTOR_SHA256, 'v51 rank vector identity changed')
    v = json.loads(path.read_text())
    require(v['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE', 'v51 vector verdict changed')
    require(
        v['scientific_role'] == 'EXACT_V31_FUSION_INPUT_RANKS_CAPTURED_BEFORE_DIAGNOSTIC_RECOVERABILITY_ATTACHMENT',
        'v51 vector role changed',
    )
    require(v['canonical_sha256_without_self_field'] == V51_VECTOR_CANONICAL, 'v51 canonical identity changed')
    core = dict(v)
    core.pop('canonical_sha256_without_self_field', None)
    require(canonical_sha(core) == V51_VECTOR_CANONICAL, 'v51 canonical payload changed')
    require(int(v['family_count']) == HDB_N and len(v['families']) == HDB_N, 'v51 HDB universe changed')
    require(v['local_order_sha256'] == LOCAL_ORDER_SHA256, 'v51 local order changed')
    require(v['v19_order_sha256'] == V19_ORDER_SHA256, 'v51 v19 order changed')
    require(v['fused_order_sha256'] == V31_FUSED_SHA256, 'v51 fused order changed')
    require(v['diagnostic_recoverability_attached'] is False, 'v51 vector contains diagnostic recoverability')
    require(v['annual_own_family_f1_attached'] is False, 'v51 vector contains annual own-family F1')
    require(v['literature_budget_used_in_statistic'] is False, 'v51 vector used literature budget')
    require(v['boundary_identity_used'] is False, 'v51 vector used boundary identity')
    require(v['new_candidate_order_evaluated'] is False and v['selector_evaluated'] is False, 'v51 vector evaluated an order/selector')
    require(v['successor_selected'] is False, 'v51 vector selected a successor')
    require(v['target_information_access'] is False and v['target_region_events_accessed'] is False, 'v51 target firewall changed')
    require(v['maarsy_scientific_access'] is False and v['dms_scientific_access'] is False, 'v51 survey firewall changed')
    require(v['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and v['blind_exclusion'] == [20.0, 55.0], 'v51 role/firewall changed')
    return v


def freeze_mode(v51_vector: Path, v1157_result: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    verify_v1157(v1157_result)
    v = verify_v51(v51_vector)

    ids = [str(x['family_id']) for x in v['families']]
    require(len(set(ids)) == HDB_N, 'duplicate HDB family identity in v51 vector')
    local_ranks = [int(x['local_rank']) for x in v['families']]
    v19_ranks = [int(x['v19_rank']) for x in v['families']]
    require(sorted(local_ranks) == list(range(1, HDB_N + 1)), 'local ranks are not 1..229 permutation')
    require(sorted(v19_ranks) == list(range(1, HDB_N + 1)), 'v19 ranks are not 1..229 permutation')

    rows: list[dict[str, Any]] = []
    nums: list[int] = []
    for x in v['families']:
        lr = int(x['local_rank'])
        vr = int(x['v19_rank'])
        num = lr - vr
        adv = float(num / DENOM)
        require(abs(float(x['local_rank_percentile']) - (lr - 1) / DENOM) < 1e-15, 'local percentile/rank mismatch')
        require(abs(float(x['v19_rank_percentile']) - (vr - 1) / DENOM) < 1e-15, 'v19 percentile/rank mismatch')
        require(
            abs((float(x['local_rank_percentile']) - float(x['v19_rank_percentile'])) - adv) < 1e-15,
            'v19 advantage mismatch',
        )
        rows.append({
            'family_id': str(x['family_id']),
            'local_rank': lr,
            'v19_rank': vr,
            'v19_advantage': adv,
        })
        nums.append(num)

    rows.sort(key=lambda x: str(x['family_id']))
    require(min(nums) == MIN_ADV_NUM and max(nums) == MAX_ADV_NUM, 'frozen v19-advantage range changed')
    require(sum(n > 0 for n in nums) == POSITIVE_N, 'positive advantage count changed')
    require(sum(n < 0 for n in nums) == NEGATIVE_N, 'negative advantage count changed')
    require(sum(n == 0 for n in nums) == ZERO_N, 'zero advantage count changed')

    payload: dict[str, Any] = {
        'verdict': 'PASS_V54_FULL_UNIVERSE_V19_ADVANTAGE_VECTOR_FREEZE',
        'scientific_role': 'COMPLETE_229_HDB_V19_ADVANTAGE_VECTOR_FROZEN_BEFORE_CURRENT_RECOVERABILITY_ATTACHMENT',
        'question': 'Across all 229 fixed HDB families, do annually recoverable families have larger local-minus-v19 rank advantage than nonrecoverable families in both exposed years?',
        'statistic': 'v19_advantage=(local_rank-v19_rank)/228; positive means immutable v19 ranks the family better than the exact-v31 local/diversity constituent',
        'authorizing_v1157_run': 31495853601,
        'authorizing_v1157_artifact': 9102914767,
        'authorizing_v1157_artifact_digest': V1157_ARTIFACT_DIGEST,
        'authorizing_v1157_result_sha256': V1157_RESULT_SHA256,
        'source_v51_run': 31493423814,
        'source_v51_artifact': 9101972590,
        'source_v51_artifact_digest': 'sha256:56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9',
        'source_v51_vector_sha256': V51_VECTOR_SHA256,
        'source_v51_vector_canonical_sha256': V51_VECTOR_CANONICAL,
        'local_order_sha256': LOCAL_ORDER_SHA256,
        'v19_order_sha256': V19_ORDER_SHA256,
        'v31_fused_order_sha256': V31_FUSED_SHA256,
        'family_count': HDB_N,
        'positive_advantage_count': POSITIVE_N,
        'negative_advantage_count': NEGATIVE_N,
        'zero_advantage_count': ZERO_N,
        'minimum_v19_advantage': float(MIN_ADV_NUM / DENOM),
        'maximum_v19_advantage': float(MAX_ADV_NUM / DENOM),
        'families': rows,
        'current_annual_f1_attached': False,
        'current_recoverability_attached': False,
        'literature_budget_used': False,
        'literature_panel_evaluated': False,
        'boundary_identity_used': False,
        'v1157_missed_surfaced_identity_used': False,
        'v52_substitution_identity_used': False,
        'component_quality_topology_signal_used': False,
        'new_candidate_order_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'threshold_selected': False,
        'quantile_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'fusion_weight_search': False,
        'rank_algebra_search': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'blind_exclusion': [20.0, 55.0],
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
    }
    out = output / 'V54_FULL_UNIVERSE_V19_ADVANTAGE_VECTOR.json'
    file_sha, can = dump_with_canonical(out, payload)
    print(json.dumps({
        'verdict': payload['verdict'],
        'file_sha256': file_sha,
        'canonical_sha256_without_self_field': can,
        'family_count': HDB_N,
        'positive_advantage_count': POSITIVE_N,
        'negative_advantage_count': NEGATIVE_N,
        'zero_advantage_count': ZERO_N,
        'minimum_v19_advantage': float(MIN_ADV_NUM / DENOM),
        'maximum_v19_advantage': float(MAX_ADV_NUM / DENOM),
    }, indent=2, sort_keys=True))
    return 0


def verify_frozen_vector(path: Path) -> dict[str, Any]:
    v = json.loads(path.read_text())
    require(v['verdict'] == 'PASS_V54_FULL_UNIVERSE_V19_ADVANTAGE_VECTOR_FREEZE', 'v54 vector verdict changed')
    require(
        v['scientific_role'] == 'COMPLETE_229_HDB_V19_ADVANTAGE_VECTOR_FROZEN_BEFORE_CURRENT_RECOVERABILITY_ATTACHMENT',
        'v54 vector role changed',
    )
    core = dict(v)
    can = core.pop('canonical_sha256_without_self_field')
    require(canonical_sha(core) == can, 'v54 vector canonical identity invalid')
    require(int(v['family_count']) == HDB_N and len(v['families']) == HDB_N, 'v54 family universe changed')
    require(v['local_order_sha256'] == LOCAL_ORDER_SHA256 and v['v19_order_sha256'] == V19_ORDER_SHA256, 'v54 constituent identities changed')
    require(v['v31_fused_order_sha256'] == V31_FUSED_SHA256, 'v54 parent fused identity changed')
    require(v['authorizing_v1157_result_sha256'] == V1157_RESULT_SHA256, 'v54 #1157 authorizer changed')
    require(v['source_v51_vector_sha256'] == V51_VECTOR_SHA256, 'v54 v51 source changed')
    require(v['current_annual_f1_attached'] is False and v['current_recoverability_attached'] is False, 'v54 vector contains current outcome')
    require(v['literature_panel_evaluated'] is False and v['new_candidate_order_evaluated'] is False, 'v54 vector evaluated a panel/order')
    require(v['selector_evaluated'] is False and v['successor_selected'] is False, 'v54 vector selected a successor')
    require(v['target_information_access'] is False and v['target_region_events_accessed'] is False, 'v54 target firewall changed')
    require(v['maarsy_scientific_access'] is False and v['dms_scientific_access'] is False, 'v54 survey firewall changed')
    require(v['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY' and v['blind_exclusion'] == [20.0, 55.0], 'v54 role/firewall changed')

    ids = [str(x['family_id']) for x in v['families']]
    require(len(set(ids)) == HDB_N, 'v54 duplicate family identity')
    require(sorted(int(x['local_rank']) for x in v['families']) == list(range(1, HDB_N + 1)), 'v54 local rank permutation changed')
    require(sorted(int(x['v19_rank']) for x in v['families']) == list(range(1, HDB_N + 1)), 'v54 v19 rank permutation changed')
    nums = [int(x['local_rank']) - int(x['v19_rank']) for x in v['families']]
    require(min(nums) == MIN_ADV_NUM and max(nums) == MAX_ADV_NUM, 'v54 structural range changed')
    require(sum(n > 0 for n in nums) == POSITIVE_N and sum(n < 0 for n in nums) == NEGATIVE_N and sum(n == 0 for n in nums) == ZERO_N, 'v54 structural sign counts changed')
    for x in v['families']:
        expected = (int(x['local_rank']) - int(x['v19_rank'])) / DENOM
        require(abs(float(x['v19_advantage']) - expected) < 1e-15, 'v54 advantage value changed')
    return v


def summarize(values: list[float]) -> dict[str, Any]:
    require(values, 'empty annual recoverability class')
    x = np.asarray(values, dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite v19 advantage')
    return {
        'count': int(len(x)),
        'median_v19_advantage': float(np.median(x)),
        'q25_v19_advantage': float(np.percentile(x, 25.0, method='linear')),
        'q75_v19_advantage': float(np.percentile(x, 75.0, method='linear')),
        'min_v19_advantage': float(np.min(x)),
        'max_v19_advantage': float(np.max(x)),
    }


def diagnose_mode(vector_file: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector = verify_frozen_vector(vector_file)

    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((hdb_root / 'family_memberships.json').read_text())
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, '#950 HDB payload is not pretruth')
    require(int(meta['feature_dimension']) == 71 and len(meta['family_ids']) == HDB_N, '#950 HDB feature universe changed')
    fams = fp['families']
    require(len(fams) == HDB_N, '#950 HDB membership universe changed')
    ids = [str(f['family_id']) for f in fams]
    require(ids == list(map(str, meta['family_ids'])), '#950 HDB family order changed')
    require(set(ids) == {str(x['family_id']) for x in vector['families']}, 'v54/#950 HDB family universe mismatch')
    require(meta['target_information_access'] is False, '#950 target firewall changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, '#950 survey firewall changed')

    by = {
        2013: json.loads((truth_root / 'truth_hdbscan_2013.json').read_text()),
        2014: json.loads((truth_root / 'truth_hdbscan_2014.json').read_text()),
    }
    eligible = v22.eligible_from_year_truth(by)
    hidden: dict[str, Any] = {}
    hidden.update(by[2013])
    hidden.update(by[2014])

    annual_f1: dict[int, dict[str, float]] = {2013: {}, 2014: {}}
    for fam in fams:
        fid = str(fam['family_id'])
        t = v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if not t['positive'] or label is None:
            q13 = q14 = 0.0
        else:
            q13, q14 = v24.annual_f1_for_fixed_label(fam, str(label), by)
        annual_f1[2013][fid] = float(q13)
        annual_f1[2014][fid] = float(q14)

    advantage = {str(x['family_id']): float(x['v19_advantage']) for x in vector['families']}
    annual: dict[str, Any] = {}
    all_pass = True
    for year in (2013, 2014):
        rec = [advantage[fid] for fid in ids if annual_f1[year][fid] > RECOVERY]
        non = [advantage[fid] for fid in ids if annual_f1[year][fid] <= RECOVERY]
        require(rec and non and len(rec) + len(non) == HDB_N, f'{year} invalid recoverability split')
        sr = summarize(rec)
        sn = summarize(non)
        diff = float(sr['median_v19_advantage'] - sn['median_v19_advantage'])
        passed = bool(sr['median_v19_advantage'] > sn['median_v19_advantage'])
        all_pass = all_pass and passed
        annual[str(year)] = {
            'recoverable': sr,
            'nonrecoverable': sn,
            'median_difference_recoverable_minus_nonrecoverable': diff,
            'direction_pass': passed,
        }

    verdict = (
        'PASS_V54_FULL_UNIVERSE_V19_ADVANTAGE_DIAGNOSTIC'
        if all_pass else
        'FAIL_V54_FULL_UNIVERSE_V19_ADVANTAGE_DIAGNOSTIC'
    )
    payload: dict[str, Any] = {
        'verdict': verdict,
        'scientific_role': 'POST_V1157_FULL_UNIVERSE_V19_ADVANTAGE_MECHANISM_DIAGNOSTIC_ONLY_NO_SUCCESSOR_EVALUATED',
        'question': 'Across all 229 fixed HDB families, is median local-minus-v19 rank advantage higher for annually recoverable than nonrecoverable families in both exposed years?',
        'statistic': 'v19_advantage=(local_rank-v19_rank)/228; positive means immutable v19 ranks the family better than exact-v31 local/diversity',
        'recovery_f1_threshold': RECOVERY,
        'family_count': HDB_N,
        'vector_file_sha256': sha(vector_file),
        'vector_canonical_sha256': vector['canonical_sha256_without_self_field'],
        'authorizing_v1157_run': 31495853601,
        'authorizing_v1157_artifact': 9102914767,
        'authorizing_v1157_result_sha256': V1157_RESULT_SHA256,
        'source_v51_vector_sha256': V51_VECTOR_SHA256,
        'annual_diagnostics': annual,
        'direction_supported_both_years': bool(all_pass),
        'literature_panel_evaluated': False,
        'new_candidate_order_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'positive_sign_selector_evaluated': False,
        'rank_gap_threshold_search': False,
        'magnitude_threshold_search': False,
        'quantile_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'group_aggregation_evaluated': False,
        'alternate_rank_normalization_search': False,
        'absolute_gap_search': False,
        'ratio_search': False,
        'log_transform_search': False,
        'fusion_weight_search': False,
        'rank_algebra_search': False,
        'component_quality_topology_rescue': False,
        'boundary_identity_used': False,
        'oracle_identity_used_for_ranking': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'metric_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'blind_exclusion': [20.0, 55.0],
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
    }
    out = output / 'V54_FULL_UNIVERSE_V19_ADVANTAGE_DIAGNOSTIC.json'
    file_sha, can = dump_with_canonical(out, payload)
    print(json.dumps({
        'verdict': verdict,
        'annual_diagnostics': annual,
        'result_file_sha256': file_sha,
        'canonical_sha256_without_self_field': can,
    }, indent=2, sort_keys=True))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)

    pf = sub.add_parser('freeze')
    pf.add_argument('--v51-vector', type=Path, required=True)
    pf.add_argument('--v1157-result', type=Path, required=True)
    pf.add_argument('--output', type=Path, required=True)

    pd = sub.add_parser('diagnose')
    pd.add_argument('--vector-file', type=Path, required=True)
    pd.add_argument('--hdb-root', type=Path, required=True)
    pd.add_argument('--truth-root', type=Path, required=True)
    pd.add_argument('--output', type=Path, required=True)

    a = p.parse_args()
    if a.mode == 'freeze':
        return freeze_mode(a.v51_vector, a.v1157_result, a.output)
    return diagnose_mode(a.vector_file, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
