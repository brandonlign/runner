#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

import orbittrace_v40_component_best_evidence_representative_v1.train_evaluate as v40

GRAPH_SHA256 = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
RECOVERY = 0.5
EXPECTED_V31 = {
    ('sugar', 2013): (0.2719801488280529, 16),
    ('sugar', 2014): (0.31529041952487225, 17),
    ('hdbscan', 2013): (0.14888037368183737, 9),
    ('hdbscan', 2014): (0.15198123772301594, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256((json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    return int(v40.pretruth_mode(sugar_root, hdbscan_root, output))


def fraction(n: int, d: int) -> float:
    require(d > 0, 'empty diagnostic stratum')
    return float(n / d)


def risk_ratio(pos_n: int, pos_d: int, neg_n: int, neg_d: int) -> float | None:
    p = fraction(pos_n, pos_d)
    q = fraction(neg_n, neg_d)
    if q == 0.0:
        return None
    return float(p / q)


def diagnose_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    require(v40.v22.sha(graph_file) == GRAPH_SHA256, 'graph identity changed')
    require(v40.v22.sha(component_file) == COMPONENT_SHA256, 'component identity changed')
    comp = json.loads(component_file.read_text())
    require(comp['truth_accessed'] is False and int(comp['component_count']) == 196, 'invalid frozen components')

    captured_orders: dict[str, list[str]] = {}
    captured_rank_maps: dict[str, dict[str, int]] = {}
    original_builder = v40.build_v40_order

    def capture_no_reorder(route: str, base_order: list[str], components: list[dict[str, Any]], rank_maps: dict[str, dict[str, int]]):
        captured_orders[route] = list(map(str, base_order))
        for rr, mapping in rank_maps.items():
            captured_rank_maps[rr] = {str(k): int(v) for k, v in mapping.items()}
        # Return exact v31 unchanged. Minimal rows satisfy frozen engine diagnostics only.
        rows = [{'representative_family_id': str(fid)} for fid in base_order]
        return list(map(str, base_order)), rows

    v40.build_v40_order = capture_no_reorder
    try:
        engine_out = output / '_v31_capture_engine'
        v40.evaluate_mode(sugar_root, hdbscan_root, truth_root, ranker_source, graph_file, component_file, engine_out)
    finally:
        v40.build_v40_order = original_builder

    require(set(captured_orders) == {'sugar', 'hdbscan'}, 'failed to capture both exact v31 orders')
    require(len(captured_orders['sugar']) == 267 and len(captured_orders['hdbscan']) == 229, 'captured rank universe changed')
    require(set(captured_rank_maps) == {'sugar', 'hdbscan'}, 'failed to capture rank maps')

    engine = json.loads((engine_out / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_RESULT.json').read_text())
    require(engine['parent_v31_reproduction_pass'] is True, 'exact v31 parent reproduction failed')
    controls = {(str(r['comparator']), int(r['year'])): (float(r['macro_f1']), int(r['recovered_f1_gt_0_5'])) for r in engine['parent_v31_controls']}
    for key, exp in EXPECTED_V31.items():
        require(key in controls and abs(controls[key][0] - exp[0]) < 1e-12 and controls[key][1] == exp[1], f'v31 control mismatch {key}')
    # The capture wrapper returns exact v31 unchanged, so the engine's diagnostic successor panels must equal parent controls.
    for row in engine['panels']:
        key = (str(row['comparator']), int(row['year']))
        require(abs(float(row['candidate_macro_f1']) - EXPECTED_V31[key][0]) < 1e-12 and int(row['candidate_recovered_f1_gt_0_5']) == EXPECTED_V31[key][1], f'capture wrapper changed order {key}')

    hmeta = json.loads((hdbscan_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    hfp = json.loads((hdbscan_root / 'family_memberships.json').read_text())
    require(hmeta['truth_accessed'] is False and hfp['truth_accessed'] is False, 'HDB pretruth payload changed')
    hids = list(map(str, hmeta['family_ids']))
    require(len(hids) == 229 and set(hids) == set(captured_orders['hdbscan']), 'HDB family identity changed')
    quality_order = list(map(str, hmeta['quality_order']))
    require(len(quality_order) == 229 and set(quality_order) == set(hids), 'quality order identity changed')
    quality_rank = {fid: i + 1 for i, fid in enumerate(quality_order)}

    token_to_component = {str(k): str(v) for k, v in comp['token_to_component'].items()}
    components = {str(c['component_id']): c for c in comp['components']}
    signal_rows = []
    for fid in hids:
        vr = int(captured_rank_maps['hdbscan'][fid])
        qr = int(quality_rank[fid])
        p_hdb = float((vr - 1) / 228.0)
        p_quality = float((qr - 1) / 228.0)
        cid = token_to_component[f'hdbscan/{fid}']
        c = components[cid]
        member_ps = []
        for sfid in map(str, c['sugar_family_ids']):
            member_ps.append(float((captured_rank_maps['sugar'][sfid] - 1) / 266.0))
        for hfid in map(str, c['hdbscan_family_ids']):
            member_ps.append(float((captured_rank_maps['hdbscan'][hfid] - 1) / 228.0))
        require(member_ps, f'empty component {cid}')
        best_p = float(min(member_ps))
        qs = bool(p_hdb > p_quality)
        closure = bool(best_p < p_hdb)
        signal_rows.append({
            'family_id': fid,
            'v31_rank': vr,
            'quality_rank': qr,
            'v31_percentile': p_hdb,
            'quality_percentile': p_quality,
            'quality_suppression': float(p_hdb - p_quality),
            'positive_quality_suppression': qs,
            'component_id': cid,
            'component_member_count': int(c['member_count']),
            'component_best_v31_percentile': best_p,
            'component_closure_opportunity': closure,
            'joint_signal': bool(qs and closure),
        })

    signal_payload = {
        'verdict': 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE',
        'scientific_role': 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION',
        'family_count': 229,
        'joint_signal_definition': '(v31_percentile > quality_percentile) AND (component_best_v31_percentile < v31_percentile)',
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'families': signal_rows,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'alternate_boolean_rule_evaluated': False,
        'oracle_identity_hardcoded': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    signal_sha = canonical_sha(signal_payload)
    signal_payload['canonical_sha256_without_self_field'] = signal_sha
    signal_path = output / 'V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL.json'
    signal_path.write_text(json.dumps(signal_payload, indent=2, sort_keys=True, allow_nan=False) + '\n')

    # Truth-aware selectivity begins only after the complete signal vector above is fixed.
    by_year = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v40.v22.eligible_from_year_truth(by_year)
    hidden: dict[str, str] = {}
    hidden.update(by_year[2013]); hidden.update(by_year[2014])
    fams = hfp['families']
    require([str(f['family_id']) for f in fams] == hids, 'membership family order changed')
    signal_by_id = {str(r['family_id']): bool(r['joint_signal']) for r in signal_rows}

    truth_rows = []
    for fam in fams:
        fid = str(fam['family_id'])
        t = v40.v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v40.v24.annual_f1_for_fixed_label(fam, str(label), by_year))
            group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            group = 'NEG/' + fid
        truth_rows.append({
            'family_id': fid,
            'diagnostic_group': group,
            'joint_signal': signal_by_id[fid],
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        })

    annual = {}
    gates = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        joint_f = [r for r in truth_rows if r['joint_signal']]
        non_f = [r for r in truth_rows if not r['joint_signal']]
        jf_rec = sum(bool(r[rk]) for r in joint_f); nf_rec = sum(bool(r[rk]) for r in non_f)
        jf_frac = fraction(jf_rec, len(joint_f)); nf_frac = fraction(nf_rec, len(non_f))
        jf_rr = risk_ratio(jf_rec, len(joint_f), nf_rec, len(non_f))

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in truth_rows:
            grouped[str(r['diagnostic_group'])].append(r)
        group_rows = []
        for g, rows in sorted(grouped.items()):
            group_rows.append({
                'diagnostic_group': g,
                'family_count': len(rows),
                'joint_signal': bool(any(r['joint_signal'] for r in rows)),
                'recoverable': bool(any(r[rk] for r in rows)),
            })
        joint_g = [r for r in group_rows if r['joint_signal']]
        non_g = [r for r in group_rows if not r['joint_signal']]
        jg_rec = sum(bool(r['recoverable']) for r in joint_g); ng_rec = sum(bool(r['recoverable']) for r in non_g)
        jg_frac = fraction(jg_rec, len(joint_g)); ng_frac = fraction(ng_rec, len(non_g))
        jg_rr = risk_ratio(jg_rec, len(joint_g), ng_rec, len(non_g))

        gate = bool(jf_frac > nf_frac and jf_rr is not None and jf_rr > 1.0 and jg_frac > ng_frac and jg_rr is not None and jg_rr > 1.0)
        gates.append(gate)
        annual[str(year)] = {
            'interpretation_gate_pass': gate,
            'family_level': {
                'joint_count': len(joint_f),
                'nonjoint_count': len(non_f),
                'joint_recoverable_count': jf_rec,
                'nonjoint_recoverable_count': nf_rec,
                'joint_recoverable_fraction': jf_frac,
                'nonjoint_recoverable_fraction': nf_frac,
                'joint_vs_nonjoint_risk_ratio': jf_rr,
            },
            'diagnostic_group_level': {
                'joint_count': len(joint_g),
                'nonjoint_count': len(non_g),
                'joint_recoverable_count': jg_rec,
                'nonjoint_recoverable_count': ng_rec,
                'joint_recoverable_fraction': jg_frac,
                'nonjoint_recoverable_fraction': ng_frac,
                'joint_vs_nonjoint_risk_ratio': jg_rr,
            },
        }

    passed = bool(all(gates))
    joint_count = sum(bool(r['joint_signal']) for r in signal_rows)
    result = {
        'verdict': 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SELECTIVITY_DIAGNOSTIC' if passed else 'FAIL_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SELECTIVITY_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_FULL_UNIVERSE_SELECTIVITY_DIAGNOSTIC_NO_SUCCESSOR_OR_ORDER_EVALUATED',
        'joint_direction_supported_both_years': passed,
        'signal_vector_sha256': signal_sha,
        'family_count': 229,
        'joint_signal_family_count': joint_count,
        'joint_signal_family_fraction': float(joint_count / 229.0),
        'annual_diagnostics': annual,
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': engine['parent_v31_controls'],
        'new_rank_or_score_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'boolean_combination_search': False,
        'component_size_rule_search': False,
        'component_score_rule_search': False,
        'route_specific_rule': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'oracle_identity_hardcoded': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SELECTIVITY_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    a = sub.add_parser('pretruth')
    a.add_argument('--sugar-root', type=Path, required=True); a.add_argument('--hdbscan-root', type=Path, required=True); a.add_argument('--output', type=Path, required=True)
    b = sub.add_parser('diagnose')
    b.add_argument('--sugar-root', type=Path, required=True); b.add_argument('--hdbscan-root', type=Path, required=True); b.add_argument('--truth-root', type=Path, required=True); b.add_argument('--ranker-source', type=Path, required=True); b.add_argument('--graph-file', type=Path, required=True); b.add_argument('--component-file', type=Path, required=True); b.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.mode == 'pretruth':
        return pretruth_mode(args.sugar_root, args.hdbscan_root, args.output)
    return diagnose_mode(args.sugar_root, args.hdbscan_root, args.truth_root, args.ranker_source, args.graph_file, args.component_file, args.output)


if __name__ == '__main__':
    raise SystemExit(main())