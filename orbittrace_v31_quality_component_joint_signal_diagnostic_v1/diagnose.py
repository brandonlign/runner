#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

QUALITY_SHA = 'b7b1acc48472deb4faa0867a8414260c52b87378d20f380d824272de7b36b9ec'
COMPONENT_SHA = 'a886977139074a1c2e8beaca54c065fd16fed5bce4c00e888ac2081dabed7222'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def index_quality(q: dict[str, Any], year: str) -> dict[str, dict[str, Any]]:
    rows = q['annual_diagnostics'][year]['groups']
    out = {}
    for r in rows:
        g = str(r['group'])
        require(g not in out, 'duplicate quality group')
        out[g] = r
    require(len(out) == 18, 'quality recoverable group count changed')
    return out


def index_component(c: dict[str, Any], year: str) -> dict[str, dict[str, Any]]:
    rows = c['annual_diagnostics'][year]['recoverable_group_rows']
    out = {}
    for r in rows:
        g = str(r['group'])
        require(g not in out, 'duplicate component group')
        out[g] = r
    require(len(out) == 18, 'component recoverable group count changed')
    return out


def summarize(rows: list[dict[str, Any]], surfaced: bool) -> dict[str, Any]:
    cls = [r for r in rows if bool(r['surfaced']) is surfaced]
    require(len(cls) == 9, 'surfaced/missed class size changed')
    hits = [r for r in cls if bool(r['joint_signal'])]
    return {
        'groups': 9,
        'joint_signal_count': len(hits),
        'joint_signal_fraction': float(len(hits) / 9.0),
        'positive_quality_suppression_count': sum(bool(r['positive_quality_suppression']) for r in cls),
        'component_closure_opportunity_count': sum(bool(r['component_closure_opportunity']) for r in cls),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--quality-result', type=Path, required=True)
    p.add_argument('--component-result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()

    require(sha(a.quality_result) == QUALITY_SHA, '#1086 result identity changed')
    require(sha(a.component_result) == COMPONENT_SHA, '#1072 result identity changed')
    q = json.loads(a.quality_result.read_text())
    c = json.loads(a.component_result.read_text())

    require(q['verdict'] == 'PASS_V31_QUALITY_SUPPRESSION_DIAGNOSTIC', '#1086 verdict changed')
    require(q['quality_suppression_direction_supported_both_years'] is True, '#1086 direction not supported')
    require(q['new_rank_or_score_evaluated'] is False and q['successor_selected'] is False, '#1086 not diagnostic-only')
    require(c['verdict'] == 'PASS_V31_CROSSROUTE_COMPONENT_CLOSURE_DIAGNOSTIC', '#1072 verdict changed')
    require(c['component_closure_direction_supported'] is True, '#1072 direction not supported')
    require(c['new_rank_or_score_evaluated'] is False and c['successor_selected'] is False, '#1072 not diagnostic-only')
    for obj in (q, c):
        require(obj['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'SonotaCo role changed')
        require(obj['target_information_access'] is False and obj['target_region_events_accessed'] is False, 'target access changed')
        require(obj['maarsy_scientific_access'] is False and obj['dms_scientific_access'] is False, 'protected survey access changed')
        require(obj['blind_exclusion'] == [20.0, 55.0], 'blind exclusion changed')

    annual = {}
    pass_flags = []
    for year in ('2013', '2014'):
        qi = index_quality(q, year)
        ci = index_component(c, year)
        require(set(qi) == set(ci), f'{year} recoverable group universe mismatch')
        rows = []
        for group in sorted(qi):
            qr = qi[group]
            cr = ci[group]
            qfid = str(qr['representative_family_id'])
            cfid = str(cr['representative_family_id'])
            require(qfid == cfid, f'{year} representative family mismatch')
            require(int(qr['v31_rank']) == int(cr['representative_hdb_v31_rank']), f'{year} v31 rank mismatch')
            require(bool(qr['surfaced']) == bool(cr['surfaced_hdb']), f'{year} surfaced status mismatch')
            positive = bool(float(qr['quality_suppression']) > 0.0)
            opportunity = bool(cr['component_closure_opportunity'])
            rows.append({
                'group': group,
                'representative_family_id': qfid,
                'v31_rank': int(qr['v31_rank']),
                'quality_rank': int(qr['quality_rank']),
                'quality_suppression': float(qr['quality_suppression']),
                'positive_quality_suppression': positive,
                'component_id': str(cr['component_id']),
                'component_closure_opportunity': opportunity,
                'joint_signal': bool(positive and opportunity),
                'surfaced': bool(qr['surfaced']),
            })
        surfaced = summarize(rows, True)
        missed = summarize(rows, False)
        gate = bool(
            missed['joint_signal_count'] >= 1
            and missed['joint_signal_fraction'] > surfaced['joint_signal_fraction']
        )
        pass_flags.append(gate)
        annual[year] = {
            'recoverable_groups': 18,
            'surfaced': surfaced,
            'missed': missed,
            'missed_minus_surfaced_joint_fraction': float(missed['joint_signal_fraction'] - surfaced['joint_signal_fraction']),
            'interpretation_gate_pass': gate,
            'rows': rows,
        }

    supported = bool(all(pass_flags))
    result = {
        'verdict': 'PASS_V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC' if supported else 'FAIL_V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_OF_PREDECLARED_AND_INTERSECTION_NO_SUCCESSOR_EVALUATED',
        'question': 'Is positive frozen quality suppression AND frozen component-closure opportunity selectively enriched among recoverable-but-missed HDB groups in both years?',
        'quality_result_sha256': QUALITY_SHA,
        'component_result_sha256': COMPONENT_SHA,
        'joint_signal_definition': '(quality_suppression > 0) AND component_closure_opportunity',
        'annual_diagnostics': annual,
        'joint_direction_supported_both_years': supported,
        'interpretation_gate': 'in each year missed joint count >=1 and missed joint fraction > surfaced joint fraction',
        'new_rank_or_score_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'oracle_identity_hardcoded': False,
        'threshold_search': False,
        'effect_size_threshold_selected': False,
        'boolean_combination_search': False,
        'alternate_or_rule_evaluated': False,
        'suppression_transform_search': False,
        'component_size_rule_search': False,
        'component_score_rule_search': False,
        'rank_window_search': False,
        'top_k_search': False,
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
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    a.output.mkdir(parents=True, exist_ok=True)
    out = a.output / 'V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'joint_direction_supported_both_years': supported,
        'annual': {
            y: {
                'surfaced': x['surfaced'],
                'missed': x['missed'],
                'missed_minus_surfaced_joint_fraction': x['missed_minus_surfaced_joint_fraction'],
                'interpretation_gate_pass': x['interpretation_gate_pass'],
            } for y, x in annual.items()
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
