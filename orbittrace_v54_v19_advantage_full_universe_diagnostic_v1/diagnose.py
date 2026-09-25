#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from orbittrace_v31_local_geometry_margin_oof_v1 import train_evaluate as v31

HDB_N = 229
RECOVERY = 0.5
V51_VECTOR_SHA256 = '5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc'
V51_VECTOR_CANONICAL_SHA256 = '0e13b3f9e6b791a13a3e90d853f8704573b1264dffcb67236e6423491ad70020'
V51_LOCAL_ORDER_SHA256 = '9898a2ad69f251595b0de4ce5763ffb6641ad27141b6e54f839ebe240eb94595'
V51_FUSED_ORDER_SHA256 = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
V1157_RESULT_SHA256 = '165f094fafa0f0f1e78b57dca83fbbf2aeee5d15bdefc9ba4b6f349d495e0aa7'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256((json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def freeze_mode(vector_file: Path, authorizer_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(sha(vector_file) == V51_VECTOR_SHA256, 'binding v51 vector bytes changed')
    require(sha(authorizer_file) == V1157_RESULT_SHA256, 'binding #1157 result bytes changed')

    v51 = json.loads(vector_file.read_text())
    auth = json.loads(authorizer_file.read_text())
    require(v51['verdict'] == 'PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE', 'v51 vector verdict changed')
    require(v51['canonical_sha256_without_self_field'] == V51_VECTOR_CANONICAL_SHA256, 'v51 vector canonical identity changed')
    chk = dict(v51)
    del chk['canonical_sha256_without_self_field']
    require(canonical_sha(chk) == V51_VECTOR_CANONICAL_SHA256, 'v51 vector canonical bytes changed')
    require(int(v51['family_count']) == HDB_N and len(v51['families']) == HDB_N, 'v51 family universe changed')
    require(v51['local_order_sha256'] == V51_LOCAL_ORDER_SHA256, 'v51 local order changed')
    require(v51['fused_order_sha256'] == V51_FUSED_ORDER_SHA256, 'v51 fused order changed')
    require(v51['diagnostic_recoverability_attached'] is False and v51['annual_own_family_f1_attached'] is False, 'v51 vector contains outcome attachment')
    require(v51['new_candidate_order_evaluated'] is False and v51['successor_selected'] is False, 'v51 vector contains successor')

    require(auth['verdict'] == 'PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC', '#1157 binding verdict changed')
    require(auth['direction_supported_both_years'] is True, '#1157 direction support changed')
    require(auth['new_candidate_order_evaluated'] is False, '#1157 unexpectedly evaluated an order')
    require(auth['successor_selected'] is False, '#1157 unexpectedly selected a successor')
    require(auth['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1157 SonotaCo role changed')
    require(auth['target_information_access'] is False and auth['target_region_events_accessed'] is False, '#1157 target firewall changed')
    require(auth['maarsy_scientific_access'] is False and auth['dms_scientific_access'] is False, '#1157 protected-survey firewall changed')

    rows = []
    seen = set()
    positive_count = 0
    nonpositive_count = 0
    for r in v51['families']:
        fid = str(r['family_id'])
        require(fid not in seen, 'duplicate v51 family identity')
        seen.add(fid)
        lr = int(r['local_rank'])
        vr = int(r['v19_rank'])
        lp = float(r['local_rank_percentile'])
        vp = float(r['v19_rank_percentile'])
        require(1 <= lr <= HDB_N and 1 <= vr <= HDB_N, 'invalid constituent rank')
        require(math.isfinite(lp) and math.isfinite(vp), 'nonfinite constituent percentile')
        require(abs(lp - (lr - 1) / (HDB_N - 1)) < 1e-15, 'local percentile arithmetic changed')
        require(abs(vp - (vr - 1) / (HDB_N - 1)) < 1e-15, 'v19 percentile arithmetic changed')
        advantage = float(lp - vp)
        positive = bool(advantage > 0.0)
        require(positive == (vr < lr), 'v19-advantage sign/rank crossing mismatch')
        if positive:
            positive_count += 1
            split = 'POSITIVE_V19_ADVANTAGE'
        else:
            nonpositive_count += 1
            split = 'NONPOSITIVE_V19_ADVANTAGE'
        rows.append({
            'family_id': fid,
            'local_rank': lr,
            'local_rank_percentile': lp,
            'v19_rank': vr,
            'v19_rank_percentile': vp,
            'v19_advantage': advantage,
            'split': split,
        })
    require(len(rows) == HDB_N and len(seen) == HDB_N, 'incomplete v54 universe')
    require(positive_count > 0 and nonpositive_count > 0, 'empty v54 split class')
    rows.sort(key=lambda x: str(x['family_id']))

    vector: dict[str, Any] = {
        'verdict': 'PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_SPLIT_FREEZE',
        'scientific_role': 'COMPLETE_229_FAMILY_HDB_V19_ADVANTAGE_SPLIT_FROZEN_BEFORE_V54_RECOVERABILITY_ATTACHMENT',
        'authorizing_diagnostic': 'PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC',
        'authorizing_run': 31495853601,
        'authorizing_artifact': 9102914767,
        'authorizing_result_sha256': V1157_RESULT_SHA256,
        'v51_vector_sha256': V51_VECTOR_SHA256,
        'v51_vector_canonical_sha256': V51_VECTOR_CANONICAL_SHA256,
        'family_count': HDB_N,
        'positive_v19_advantage_count': positive_count,
        'nonpositive_v19_advantage_count': nonpositive_count,
        'statistic': 'v19_advantage = local_rank_percentile - v19_rank_percentile',
        'split_rule': 'POSITIVE_V19_ADVANTAGE iff v19_advantage > 0 iff v19_rank < local_rank; NONPOSITIVE otherwise',
        'families': rows,
        'current_v54_recoverability_attached': False,
        'annual_own_family_f1_attached': False,
        'literature_budget_used_in_split': False,
        'top_k_used_in_split': False,
        'rank_window_used_in_split': False,
        'boundary_identity_used': False,
        'group_identity_used': False,
        'v1157_surfaced_missed_identity_used': False,
        'component_quality_topology_signal_used': False,
        'new_candidate_order_evaluated': False,
        'selector_evaluated': False,
        'successor_selected': False,
        'nonzero_threshold_selected': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
    }
    vector['canonical_sha256_without_self_field'] = canonical_sha(vector)
    out = output / 'V54_V19_ADVANTAGE_FULL_UNIVERSE_SPLIT.json'
    out.write_text(json.dumps(vector, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': vector['verdict'],
        'family_count': HDB_N,
        'positive_v19_advantage_count': positive_count,
        'nonpositive_v19_advantage_count': nonpositive_count,
        'canonical_sha256_without_self_field': vector['canonical_sha256_without_self_field'],
        'file_sha256': sha(out),
    }, indent=2, sort_keys=True))
    return 0


def diagnose_mode(split_file: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    vector = json.loads(split_file.read_text())
    require(vector['verdict'] == 'PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_SPLIT_FREEZE', 'v54 split verdict changed')
    require(vector['scientific_role'] == 'COMPLETE_229_FAMILY_HDB_V19_ADVANTAGE_SPLIT_FROZEN_BEFORE_V54_RECOVERABILITY_ATTACHMENT', 'v54 split role changed')
    require(vector['authorizing_diagnostic'] == 'PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC', 'v54 authorizer changed')
    require(vector['authorizing_run'] == 31495853601 and vector['authorizing_artifact'] == 9102914767, 'v54 authorizer provenance changed')
    require(vector['authorizing_result_sha256'] == V1157_RESULT_SHA256, 'v54 authorizer result SHA changed')
    require(vector['v51_vector_sha256'] == V51_VECTOR_SHA256 and vector['v51_vector_canonical_sha256'] == V51_VECTOR_CANONICAL_SHA256, 'v54 v51 identity changed')
    require(int(vector['family_count']) == HDB_N and len(vector['families']) == HDB_N, 'v54 family universe changed')
    require(vector['current_v54_recoverability_attached'] is False and vector['annual_own_family_f1_attached'] is False, 'v54 split already contains outcomes')
    for k in ('literature_budget_used_in_split','top_k_used_in_split','rank_window_used_in_split','boundary_identity_used','group_identity_used','v1157_surfaced_missed_identity_used','component_quality_topology_signal_used','new_candidate_order_evaluated','selector_evaluated','successor_selected','nonzero_threshold_selected','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        require(vector[k] is False, f'v54 split guard changed: {k}')
    expected_canonical = str(vector['canonical_sha256_without_self_field'])
    chk = dict(vector)
    del chk['canonical_sha256_without_self_field']
    require(canonical_sha(chk) == expected_canonical, 'v54 split canonical identity changed')

    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((hdb_root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    fams = list(fp['families'])
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, '#950 HDB payload not pretruth')
    require(meta['feature_dimension'] == 71 and len(ids) == HDB_N and len(fams) == HDB_N, '#950 HDB universe changed')
    require([str(f['family_id']) for f in fams] == ids, '#950 HDB membership order changed')
    require(meta['target_information_access'] is False, '#950 target access changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, '#950 protected-survey access changed')
    fam_by_id = {str(f['family_id']): f for f in fams}
    vrows = list(vector['families'])
    vids = [str(r['family_id']) for r in vrows]
    require(len(set(vids)) == HDB_N and set(vids) == set(ids), 'v54 split identities differ from #950')

    by = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v31.v22.eligible_from_year_truth(by)
    hidden: dict[str, Any] = {}
    hidden.update(by[2013])
    hidden.update(by[2014])

    diagnostic_rows = []
    for r in vrows:
        fid = str(r['family_id'])
        lr = int(r['local_rank'])
        vr = int(r['v19_rank'])
        advantage = float(r['v19_advantage'])
        require(math.isfinite(advantage), 'nonfinite v19 advantage')
        require(abs(advantage - (float(r['local_rank_percentile']) - float(r['v19_rank_percentile']))) < 1e-15, 'v19-advantage arithmetic changed')
        positive = bool(advantage > 0.0)
        require(positive == (vr < lr), 'v19-advantage sign/rank mismatch at diagnosis')
        expected_split = 'POSITIVE_V19_ADVANTAGE' if positive else 'NONPOSITIVE_V19_ADVANTAGE'
        require(str(r['split']) == expected_split, 'v54 split label changed')
        fam = fam_by_id[fid]
        t = v31.v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v31.v24.annual_f1_for_fixed_label(fam, str(label), by))
        else:
            f13 = f14 = 0.0
        diagnostic_rows.append({
            'family_id': fid,
            'split': expected_split,
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        })

    annual: dict[str, Any] = {}
    directions = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        pos = [x for x in diagnostic_rows if x['split'] == 'POSITIVE_V19_ADVANTAGE']
        non = [x for x in diagnostic_rows if x['split'] == 'NONPOSITIVE_V19_ADVANTAGE']
        require(pos and non, f'{year} empty v54 split class')
        pos_rec = sum(bool(x[rk]) for x in pos)
        non_rec = sum(bool(x[rk]) for x in non)
        pos_frac = float(pos_rec / len(pos))
        non_frac = float(non_rec / len(non))
        direction = bool(pos_frac > non_frac)
        directions.append(direction)
        annual[str(year)] = {
            'positive_v19_advantage': {
                'families': len(pos),
                'recoverable': int(pos_rec),
                'recoverability_fraction': pos_frac,
            },
            'nonpositive_v19_advantage': {
                'families': len(non),
                'recoverable': int(non_rec),
                'recoverability_fraction': non_frac,
            },
            'fraction_difference_positive_minus_nonpositive': float(pos_frac - non_frac),
            'direction_pass': direction,
        }

    passed = bool(all(directions))
    result: dict[str, Any] = {
        'verdict': 'PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC' if passed else 'FAIL_V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC',
        'scientific_role': 'POST_1157_FULL_229_FAMILY_HDB_MECHANISM_DIAGNOSTIC_ONLY_NO_NEW_ORDER_OR_PANEL_EVALUATED',
        'question': 'Across all 229 fixed HDB families, is annual recoverability fraction strictly higher when immutable v19 ranks the family better than exact-v31 local/diversity does, in both exposed years?',
        'authorizing_diagnostic': 'PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC',
        'authorizing_run': 31495853601,
        'authorizing_artifact': 9102914767,
        'authorizing_result_sha256': V1157_RESULT_SHA256,
        'split_file_sha256': sha(split_file),
        'split_canonical_sha256': expected_canonical,
        'family_count': HDB_N,
        'statistic': vector['statistic'],
        'split_rule': vector['split_rule'],
        'recovery_f1_threshold': RECOVERY,
        'annual_diagnostics': annual,
        'direction_supported_both_years': passed,
        'new_candidate_order_evaluated': False,
        'literature_panel_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'v19_only_order_evaluated': False,
        'minimum_rank_order_evaluated': False,
        'weighted_fusion_evaluated': False,
        'nonlinear_fusion_evaluated': False,
        'representative_group_aggregation_evaluated': False,
        'auc_evaluated': False,
        'correlation_evaluated': False,
        'regression_evaluated': False,
        'p_value_evaluated': False,
        'nonzero_threshold_search': False,
        'absolute_gap_search': False,
        'quantile_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'literature_budget_analysis': False,
        'boundary_identity_used': False,
        'v1157_surfaced_missed_identity_used': False,
        'component_quality_topology_rescue': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'metric_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'source_quota_selected': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = output / 'V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('--vector-file', type=Path, required=True)
    f.add_argument('--authorizer-file', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    d = sub.add_parser('diagnose')
    d.add_argument('--split-file', type=Path, required=True)
    d.add_argument('--hdb-root', type=Path, required=True)
    d.add_argument('--truth-root', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'freeze':
        return freeze_mode(a.vector_file, a.authorizer_file, a.output)
    return diagnose_mode(a.split_file, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
