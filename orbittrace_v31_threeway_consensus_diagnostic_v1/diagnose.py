#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JOINT_RUN = 31456963941
JOINT_ARTIFACT = 9088402091
JOINT_RESULT_SHA = '2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842'
CROSS_RUN = 31457199102
CROSS_ARTIFACT = 9088482597
CROSS_RESULT_SHA = '62ed82eeb4f10b4371ec2072af7de527482ab070866693a2230be564ebf6af35'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    require(rows, 'empty surfaced/missed class')
    n = len(rows)
    joint = sum(bool(r['quality_component_joint']) for r in rows)
    cross = sum(bool(r['crossroute_positive']) for r in rows)
    triple = sum(bool(r['threeway_positive']) for r in rows)
    return {
        'groups': n,
        'quality_component_joint_count': joint,
        'quality_component_joint_fraction': float(joint / n),
        'crossroute_positive_count': cross,
        'crossroute_positive_fraction': float(cross / n),
        'threeway_positive_count': triple,
        'threeway_positive_fraction': float(triple / n),
    }


def source_checks(joint: dict[str, Any], cross: dict[str, Any]) -> None:
    require(joint['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_SIGNAL_DIAGNOSTIC', '#1091 verdict changed')
    require(joint['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_OF_PREDECLARED_AND_INTERSECTION_NO_SUCCESSOR_EVALUATED', '#1091 role changed')
    require(joint['joint_signal_definition'] == '(quality_suppression > 0) AND component_closure_opportunity', '#1091 joint definition changed')
    require(joint['new_rank_or_score_evaluated'] is False and joint['selector_evaluated'] is False and joint['replacement_rule_evaluated'] is False and joint['successor_selected'] is False, '#1091 not diagnostic-only')

    require(cross['verdict'] == 'PASS_V31_CONCORDANT_INDEPENDENT_SUPPRESSION_DIAGNOSTIC', '#1093 verdict changed')
    require(cross['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CONCORDANT_SELECTOR_OR_SUCCESSOR_EVALUATED', '#1093 role changed')
    require(cross['crossroute_positive_definition'] == 'crossroute_rank_gap>0; unlinked/no usable Sugar rank is false', '#1093 cross-route sign changed')
    require(cross['quality_positive_definition'] == 'quality_suppression>0', '#1093 quality sign changed')
    require(cross['new_rank_or_score_evaluated'] is False and cross['selector_evaluated'] is False and cross['replacement_rule_evaluated'] is False and cross['successor_selected'] is False, '#1093 not diagnostic-only')

    for src in (joint, cross):
        require(src['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'SonotaCo role changed')
        require(src['target_information_access'] is False and src['target_region_events_accessed'] is False, 'protected target access changed')
        require(src['maarsy_scientific_access'] is False and src['dms_scientific_access'] is False, 'protected survey access changed')
        require(src['blind_exclusion'] == [20.0, 55.0], 'blind exclusion changed')
    require(set(joint['annual_diagnostics']) == {'2013', '2014'}, '#1091 years changed')
    require(set(cross['annual_diagnostics']) == {'2013', '2014'}, '#1093 years changed')


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--joint-result', type=Path, required=True)
    p.add_argument('--cross-result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    joint = json.loads(a.joint_result.read_text())
    cross = json.loads(a.cross_result.read_text())
    source_checks(joint, cross)

    annual: dict[str, Any] = {}
    gates: list[bool] = []
    for year in ('2013', '2014'):
        ja = joint['annual_diagnostics'][year]
        ca = cross['annual_diagnostics'][year]
        require(int(ja['recoverable_groups']) == 18 and int(ca['recoverable_groups']) == 18, f'{year} recoverable count changed')
        require(len(ja['rows']) == 18 and len(ca['groups']) == 18, f'{year} row count changed')

        jrows = {str(r['group']): r for r in ja['rows']}
        crows = {str(r['group']): r for r in ca['groups']}
        require(set(jrows) == set(crows) and len(jrows) == 18, f'{year} group universe mismatch')

        rows: list[dict[str, Any]] = []
        for group in sorted(jrows):
            jr = jrows[group]
            cr = crows[group]
            jfid = str(jr['representative_family_id'])
            cfid = str(cr['representative_family_id'])
            jrank = int(jr['v31_rank'])
            crank = int(cr['v31_rank'])
            jsurf = bool(jr['surfaced'])
            csurf = bool(cr['surfaced'])
            require(jfid == cfid and jrank == crank and jsurf == csurf, f'{year} representative alignment changed for {group}')

            jq = bool(jr['positive_quality_suppression'])
            cq = bool(cr['quality_positive'])
            require(jq == cq, f'{year} quality sign mismatch for {group}')
            jsupp = float(jr['quality_suppression'])
            csupp = float(cr['quality_suppression'])
            require(abs(jsupp - csupp) < 1e-15, f'{year} quality suppression mismatch for {group}')
            component = bool(jr['component_closure_opportunity'])
            quality_component_joint = bool(jr['joint_signal'])
            require(quality_component_joint == bool(jq and component), f'{year} #1091 joint mismatch for {group}')
            cross_positive = bool(cr['crossroute_positive'])
            triple = bool(jq and component and cross_positive)

            rows.append({
                'group': group,
                'representative_family_id': jfid,
                'v31_rank': jrank,
                'surfaced': jsurf,
                'positive_quality_suppression': jq,
                'quality_suppression': jsupp,
                'component_closure_opportunity': component,
                'quality_component_joint': quality_component_joint,
                'crossroute_positive': cross_positive,
                'crossroute_rank_gap': None if cr['crossroute_rank_gap'] is None else float(cr['crossroute_rank_gap']),
                'threeway_positive': triple,
            })

        surfaced = [r for r in rows if r['surfaced']]
        missed = [r for r in rows if not r['surfaced']]
        require(len(surfaced) == 9 and len(missed) == 9, f'{year} surfaced/missed split changed')
        ss = summarize(surfaced)
        ms = summarize(missed)
        gate = bool(ms['threeway_positive_count'] >= 1 and ms['threeway_positive_fraction'] > ss['threeway_positive_fraction'])
        gates.append(gate)
        annual[year] = {
            'recoverable_groups': 18,
            'surfaced_groups': 9,
            'missed_groups': 9,
            'surfaced_summary': ss,
            'missed_summary': ms,
            'missed_minus_surfaced_threeway_fraction': float(ms['threeway_positive_fraction'] - ss['threeway_positive_fraction']),
            'threeway_direction_gate': gate,
            'rows': rows,
        }

    supported = bool(all(gates))
    result = {
        'verdict': 'PASS_V31_THREEWAY_CONSENSUS_DIAGNOSTIC' if supported else 'FAIL_V31_THREEWAY_CONSENSUS_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_THREEWAY_SELECTOR_ORDER_OR_SUCCESSOR_EVALUATED',
        'joint_source_run': JOINT_RUN,
        'joint_source_artifact': JOINT_ARTIFACT,
        'joint_source_result_sha256': JOINT_RESULT_SHA,
        'cross_source_run': CROSS_RUN,
        'cross_source_artifact': CROSS_ARTIFACT,
        'cross_source_result_sha256': CROSS_RESULT_SHA,
        'threeway_definition': 'positive_quality_suppression AND component_closure_opportunity AND crossroute_positive',
        'annual_diagnostics': annual,
        'threeway_direction_supported_both_years': supported,
        'interpretation_gate': 'in each year >=1 missed threeway-positive recoverable group and missed threeway-positive fraction strictly greater than surfaced fraction; no effect-size/cardinality threshold',
        'new_rank_or_score_evaluated': False,
        'selector_order_evaluated': False,
        'replacement_rule_evaluated': False,
        'promotion_position_evaluated': False,
        'literature_panel_evaluated': False,
        'successor_selected': False,
        'signal_magnitude_used': False,
        'threshold_search': False,
        'effect_size_threshold_selected': False,
        'boolean_combination_search': False,
        'pairwise_fallback_evaluated': False,
        'or_logic_search': False,
        'xor_logic_search': False,
        'rank_window_search': False,
        'top_k_search': False,
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
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V31_THREEWAY_CONSENSUS_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'threeway_direction_supported_both_years': supported,
        'annual': {
            y: {
                'surfaced_summary': x['surfaced_summary'],
                'missed_summary': x['missed_summary'],
                'missed_minus_surfaced_threeway_fraction': x['missed_minus_surfaced_threeway_fraction'],
                'threeway_direction_gate': x['threeway_direction_gate'],
            }
            for y, x in annual.items()
        },
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
