#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24

SIGNAL_SHA256 = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
GRAPH_SHA256 = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
HDB_N = 229
JOINT_N = 60
ONE_TO_ONE_N = 41
AMBIGUOUS_N = 19
COMPONENT_N = 196
RECOVERY_F1 = 0.5


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256((json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def load_inputs(signal_file: Path, component_file: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    require(sha(signal_file) == SIGNAL_SHA256, '#1098 signal identity changed')
    require(sha(component_file) == COMPONENT_SHA256, 'component identity changed')
    signal = json.loads(signal_file.read_text())
    comp = json.loads(component_file.read_text())
    require(signal['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', '#1098 signal verdict changed')
    require(signal['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', '#1098 signal role changed')
    require(int(signal['family_count']) == HDB_N and len(signal['families']) == HDB_N, '#1098 HDB universe changed')
    require(sum(bool(x['joint_signal']) for x in signal['families']) == JOINT_N, '#1098 joint population changed')
    require(signal['graph_sha256'] == GRAPH_SHA256 and signal['component_sha256'] == COMPONENT_SHA256, '#1098 graph/components changed')
    require(signal['target_information_access'] is False and signal['target_region_events_accessed'] is False, '#1098 target firewall changed')
    require(signal['maarsy_scientific_access'] is False and signal['dms_scientific_access'] is False, '#1098 survey firewall changed')
    require(signal['blind_exclusion'] == [20.0, 55.0], '#1098 blind exclusion changed')
    require(comp['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY', 'component verdict changed')
    require(comp['scientific_role'] == 'PRETRUTH_CONNECTED_COMPONENT_IDENTITY_ONLY', 'component role changed')
    require(comp['truth_accessed'] is False and int(comp['component_count']) == COMPONENT_N, 'component universe changed')
    require(comp['graph_sha256'] == GRAPH_SHA256, 'component graph identity changed')
    require(comp['target_information_access'] is False and comp['target_region_events_accessed'] is False, 'component target firewall changed')
    require(comp['maarsy_scientific_access'] is False and comp['dms_scientific_access'] is False, 'component survey firewall changed')
    require(comp['blind_exclusion'] == [20.0, 55.0], 'component blind exclusion changed')
    return signal, comp


def freeze_mode(signal_file: Path, component_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    signal, comp = load_inputs(signal_file, component_file)
    components = {str(x['component_id']): x for x in comp['components']}
    require(len(components) == COMPONENT_N, 'duplicate component identity')
    ids = [str(x['family_id']) for x in signal['families']]
    require(len(set(ids)) == HDB_N, 'duplicate signal family identity')
    joint = [x for x in signal['families'] if bool(x['joint_signal'])]
    require(len(joint) == JOINT_N, 'joint population changed')

    rows = []
    for r in joint:
        fid = str(r['family_id'])
        cid = str(r['component_id'])
        require(cid in components, f'missing component {cid} for {fid}')
        c = components[cid]
        h = int(c['hdbscan_member_count'])
        s = int(c['sugar_member_count'])
        m = int(c['member_count'])
        require(h >= 1 and s >= 1 and m == h + s, f'invalid component topology for {fid}')
        one = bool(h == 1 and s == 1)
        rows.append({
            'family_id': fid,
            'v31_rank': int(r['v31_rank']),
            'component_id': cid,
            'hdbscan_member_count': h,
            'sugar_member_count': s,
            'component_member_count': m,
            'topology_class': 'ONE_TO_ONE' if one else 'AMBIGUOUS',
        })
    rows.sort(key=lambda x: (int(x['v31_rank']), str(x['family_id'])))
    one_n = sum(x['topology_class'] == 'ONE_TO_ONE' for x in rows)
    amb_n = sum(x['topology_class'] == 'AMBIGUOUS' for x in rows)
    require(one_n == ONE_TO_ONE_N and amb_n == AMBIGUOUS_N, 'frozen topology split changed')

    payload: dict[str, Any] = {
        'verdict': 'PASS_V31_JOINT_COMPONENT_TOPOLOGY_VECTOR_FREEZE',
        'scientific_role': 'EXACT_60_JOINT_FAMILY_COMPONENT_TOPOLOGY_FROZEN_BEFORE_OUTCOME_TRUTH',
        'source_1098_run': 31457923695,
        'source_1098_artifact': 9088724826,
        'source_1098_artifact_digest': 'sha256:11498b73237304f4175f37910596700ed78284bc6106d0c21dcaab66f97b7978',
        'source_signal_sha256': SIGNAL_SHA256,
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'hdb_family_count': HDB_N,
        'joint_family_count': JOINT_N,
        'one_to_one_family_count': one_n,
        'ambiguous_family_count': amb_n,
        'topology_definition': 'ONE_TO_ONE iff frozen component has hdbscan_member_count==1 and sugar_member_count==1; AMBIGUOUS otherwise',
        'families': rows,
        'truth_accessed': False,
        'literature_panel_evaluated': False,
        'candidate_total_order_evaluated': False,
        'selector_evaluated': False,
        'successor_selected': False,
        'component_size_threshold_selected': False,
        'alternate_topology_search': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    payload['canonical_sha256_without_self_field'] = canonical_sha(payload)
    p = output / 'V31_JOINT_COMPONENT_TOPOLOGY_VECTOR.json'
    p.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': payload['verdict'],
        'joint_family_count': JOINT_N,
        'one_to_one_family_count': one_n,
        'ambiguous_family_count': amb_n,
        'file_sha256': sha(p),
        'canonical_sha256_without_self_field': payload['canonical_sha256_without_self_field'],
    }, indent=2, sort_keys=True))
    return 0


def frac(n: int, d: int) -> float:
    require(d > 0, 'empty diagnostic stratum')
    return float(n / d)


def diagnose_mode(vector_file: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    v = json.loads(vector_file.read_text())
    require(v['verdict'] == 'PASS_V31_JOINT_COMPONENT_TOPOLOGY_VECTOR_FREEZE', 'topology vector verdict changed')
    require(v['scientific_role'] == 'EXACT_60_JOINT_FAMILY_COMPONENT_TOPOLOGY_FROZEN_BEFORE_OUTCOME_TRUTH', 'topology vector role changed')
    require(v['source_signal_sha256'] == SIGNAL_SHA256 and v['graph_sha256'] == GRAPH_SHA256 and v['component_sha256'] == COMPONENT_SHA256, 'topology vector provenance changed')
    require(int(v['joint_family_count']) == JOINT_N and len(v['families']) == JOINT_N, 'topology vector population changed')
    require(int(v['one_to_one_family_count']) == ONE_TO_ONE_N and int(v['ambiguous_family_count']) == AMBIGUOUS_N, 'topology vector split changed')
    require(v['truth_accessed'] is False and v['candidate_total_order_evaluated'] is False and v['literature_panel_evaluated'] is False, 'topology vector not diagnostic-only')
    check = dict(v)
    expected = str(check.pop('canonical_sha256_without_self_field'))
    require(canonical_sha(check) == expected, 'topology vector canonical identity changed')

    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fp = json.loads((hdb_root / 'family_memberships.json').read_text())
    ids = list(map(str, meta['family_ids']))
    fams = list(fp['families'])
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, '#950 HDB payload not pretruth')
    require(int(meta['feature_dimension']) == 71 and len(ids) == HDB_N and len(fams) == HDB_N, '#950 HDB universe changed')
    require([str(x['family_id']) for x in fams] == ids, '#950 membership order changed')
    require(meta['target_information_access'] is False and meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, '#950 firewall changed')
    fam_by_id = {str(x['family_id']): x for x in fams}
    vector_rows = list(v['families'])
    vector_ids = [str(x['family_id']) for x in vector_rows]
    require(len(set(vector_ids)) == JOINT_N and set(vector_ids) <= set(ids), 'topology vector family mismatch')

    by_year = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v22.eligible_from_year_truth(by_year)
    hidden: dict[str, Any] = {}
    hidden.update(by_year[2013]); hidden.update(by_year[2014])

    rows = []
    for x in vector_rows:
        fid = str(x['family_id'])
        fam = fam_by_id[fid]
        t = v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v24.annual_f1_for_fixed_label(fam, str(label), by_year))
            group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            group = 'NEG/' + fid
        rows.append({
            **x,
            'diagnostic_group': group,
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY_F1),
            'recoverable_2014': bool(f14 > RECOVERY_F1),
        })

    annual: dict[str, Any] = {}
    pass_flags: list[bool] = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        one = [r for r in rows if r['topology_class'] == 'ONE_TO_ONE']
        amb = [r for r in rows if r['topology_class'] == 'AMBIGUOUS']
        require(len(one) == ONE_TO_ONE_N and len(amb) == AMBIGUOUS_N, 'family topology strata changed after truth attachment')
        one_rec = sum(bool(r[rk]) for r in one)
        amb_rec = sum(bool(r[rk]) for r in amb)
        one_frac = frac(one_rec, len(one)); amb_frac = frac(amb_rec, len(amb))
        family_pass = bool(one_frac > amb_frac)

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in rows:
            grouped[str(r['diagnostic_group'])].append(r)
        groups = []
        for g, rs in sorted(grouped.items()):
            rep = min(rs, key=lambda z: (int(z['v31_rank']), str(z['family_id'])))
            classes = sorted(set(str(z['topology_class']) for z in rs))
            groups.append({
                'diagnostic_group': g,
                'joint_family_count': len(rs),
                'representative_family_id': str(rep['family_id']),
                'representative_v31_rank': int(rep['v31_rank']),
                'representative_topology_class': str(rep['topology_class']),
                'mixed_topology_group': bool(len(classes) > 1),
                'topology_classes_present': classes,
                'recoverable': bool(any(bool(z[rk]) for z in rs)),
            })
        gone = [g for g in groups if g['representative_topology_class'] == 'ONE_TO_ONE']
        gamb = [g for g in groups if g['representative_topology_class'] == 'AMBIGUOUS']
        require(gone and gamb, f'{year} empty representative topology group stratum')
        gone_rec = sum(bool(g['recoverable']) for g in gone)
        gamb_rec = sum(bool(g['recoverable']) for g in gamb)
        gone_frac = frac(gone_rec, len(gone)); gamb_frac = frac(gamb_rec, len(gamb))
        group_pass = bool(gone_frac > gamb_frac)

        annual[str(year)] = {
            'family_level': {
                'one_to_one_family_count': len(one),
                'one_to_one_recoverable_count': one_rec,
                'one_to_one_recoverable_fraction': one_frac,
                'ambiguous_family_count': len(amb),
                'ambiguous_recoverable_count': amb_rec,
                'ambiguous_recoverable_fraction': amb_frac,
                'difference_one_to_one_minus_ambiguous': float(one_frac - amb_frac),
                'direction_pass': family_pass,
            },
            'representative_group_level': {
                'group_count': len(groups),
                'one_to_one_representative_group_count': len(gone),
                'one_to_one_representative_recoverable_count': gone_rec,
                'one_to_one_representative_recoverable_fraction': gone_frac,
                'ambiguous_representative_group_count': len(gamb),
                'ambiguous_representative_recoverable_count': gamb_rec,
                'ambiguous_representative_recoverable_fraction': gamb_frac,
                'mixed_topology_group_count': sum(bool(g['mixed_topology_group']) for g in groups),
                'difference_one_to_one_minus_ambiguous': float(gone_frac - gamb_frac),
                'direction_pass': group_pass,
                'groups': groups,
            },
        }
        pass_flags.extend([family_pass, group_pass])

    passed = bool(all(pass_flags))
    result = {
        'verdict': 'PASS_V31_JOINT_COMPONENT_TOPOLOGY_DIAGNOSTIC' if passed else 'FAIL_V31_JOINT_COMPONENT_TOPOLOGY_DIAGNOSTIC',
        'scientific_role': 'POST_V49_COMPONENT_TOPOLOGY_DIAGNOSTIC_ONLY_NO_SELECTOR_ORDER_OR_PANEL_EVALUATED',
        'question': 'Within the exact 60 #1098 joint-positive HDB families, is unambiguous 1-HDB+1-Sugar component topology more recoverable than ambiguous topology at family and v31-representative diagnostic-group levels in both exposed years?',
        'source_1098_run': 31457923695,
        'source_1098_artifact': 9088724826,
        'source_signal_sha256': SIGNAL_SHA256,
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'vector_file_sha256': sha(vector_file),
        'vector_canonical_sha256': expected,
        'joint_family_count': JOINT_N,
        'one_to_one_family_count': ONE_TO_ONE_N,
        'ambiguous_family_count': AMBIGUOUS_N,
        'recovery_f1_threshold': RECOVERY_F1,
        'annual_diagnostics': annual,
        'direction_supported_both_years_both_levels': passed,
        'candidate_total_order_evaluated': False,
        'literature_panel_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'component_size_threshold_search': False,
        'component_size_transform_search': False,
        'alternate_topology_search': False,
        'route_count_ratio_search': False,
        'component_density_search': False,
        'component_entropy_search': False,
        'graph_or_component_redefinition': False,
        'quality_component_fusion_search': False,
        'coefficient_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'oracle_identity_hardcoded': False,
        'boundary_rescue_list_created': False,
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
    (output / 'V31_JOINT_COMPONENT_TOPOLOGY_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('--signal-file', type=Path, required=True)
    f.add_argument('--component-file', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    d = sub.add_parser('diagnose')
    d.add_argument('--vector-file', type=Path, required=True)
    d.add_argument('--hdb-root', type=Path, required=True)
    d.add_argument('--truth-root', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'freeze':
        return freeze_mode(a.signal_file, a.component_file, a.output)
    return diagnose_mode(a.vector_file, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
