#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RANK_RUN = 31454523913
RANK_ARTIFACT = 9087524827
RANK_DIGEST = 'sha256:35ce469b2babec1d1790a5e73651e9366a7fa2478718c7547748863e39608466'
QUALITY_RUN = 31456339844
QUALITY_ARTIFACT = 9088169870
QUALITY_DIGEST = 'sha256:b0f9499280f9e8cc4d1f6f8a04d4871a306ea085a8eaee03bba0d002c35d5641'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def source_checks(rank: dict[str, Any], quality: dict[str, Any]) -> None:
    require(rank['verdict'] == 'PASS_V31_CROSSROUTE_RANK_DISAGREEMENT_DIAGNOSTIC', 'rank diagnostic verdict changed')
    require(rank['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CROSSROUTE_RANK_TRANSFER_EVALUATED', 'rank diagnostic role changed')
    require(rank['new_rank_or_score_evaluated'] is False and rank['crossroute_rank_transfer_evaluated'] is False and rank['successor_selected'] is False, 'rank diagnostic evaluated successor')
    require(quality['verdict'] == 'PASS_V31_QUALITY_SUPPRESSION_DIAGNOSTIC', 'quality diagnostic verdict changed')
    require(quality['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_QUALITY_RERANK_OR_SUCCESSOR_EVALUATED', 'quality diagnostic role changed')
    require(quality['new_rank_or_score_evaluated'] is False and quality['quality_rerank_evaluated'] is False and quality['successor_selected'] is False, 'quality diagnostic evaluated successor')
    require(int(rank['hdbscan_family_count']) == 229 and int(quality['hdb_family_count']) == 229, 'HDB family count changed')
    require(rank['rank_gap_definition'] == '((linked_hdb_rank-1)/228)-((best_sugar_neighbor_rank-1)/266)', 'rank gap definition changed')
    require(quality['suppression_definition'] == '((v31_rank-1)/228)-((quality_rank-1)/228)', 'quality suppression definition changed')
    for src in (rank, quality):
        require(src['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'SonotaCo role changed')
        require(src['maarsy_scientific_access'] is False and src['dms_scientific_access'] is False, 'protected survey access changed')
        require(src['target_information_access'] is False and src['target_region_events_accessed'] is False, 'protected target access changed')
        require(src['blind_exclusion'] == [20.0, 55.0], 'blind exclusion changed')
    require(set(rank['annual_diagnostics']) == {'2013', '2014'} and set(quality['annual_diagnostics']) == {'2013', '2014'}, 'annual years changed')


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    require(rows, 'empty surfaced/missed class')
    n = len(rows)
    cr = sum(bool(r['crossroute_positive']) for r in rows)
    qp = sum(bool(r['quality_positive']) for r in rows)
    cp = sum(bool(r['concordant_positive']) for r in rows)
    return {
        'groups': n,
        'crossroute_positive_count': cr,
        'crossroute_positive_fraction': float(cr / n),
        'quality_positive_count': qp,
        'quality_positive_fraction': float(qp / n),
        'concordant_positive_count': cp,
        'concordant_positive_fraction': float(cp / n),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--rank-result', type=Path, required=True)
    p.add_argument('--quality-result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    rank = json.loads(a.rank_result.read_text())
    quality = json.loads(a.quality_result.read_text())
    source_checks(rank, quality)

    annual = {}
    gate_flags = []
    for year in ('2013', '2014'):
        ra = rank['annual_diagnostics'][year]
        qa = quality['annual_diagnostics'][year]
        require(int(ra['annual_recoverable_hdb_groups']) == 18 and int(qa['recoverable_groups']) == 18, f'{year} recoverable count changed')
        require(int(ra['surfaced_hdb_groups']) == 9 and int(ra['missed_hdb_groups']) == 9, f'{year} rank surfaced/missed split changed')
        require(int(qa['surfaced_groups']) == 9 and int(qa['missed_groups']) == 9, f'{year} quality surfaced/missed split changed')
        rrows = {str(r['group']): r for r in ra['groups']}
        qrows = {str(r['group']): r for r in qa['groups']}
        require(len(rrows) == len(qrows) == 18 and set(rrows) == set(qrows), f'{year} group universe mismatch')
        rows = []
        for group in sorted(rrows):
            rr = rrows[group]
            qr = qrows[group]
            rfid = str(rr['hdb_representative_family_id'])
            qfid = str(qr['representative_family_id'])
            rrank = int(rr['hdb_representative_rank'])
            qvrank = int(qr['v31_rank'])
            rsurf = bool(rr['surfaced_hdb'])
            qsurf = bool(qr['surfaced'])
            require(rfid == qfid and rrank == qvrank and rsurf == qsurf, f'{year} frozen representative mismatch for {group}')
            gap = rr.get('crossroute_rank_gap')
            cross_positive = bool(gap is not None and float(gap) > 0.0)
            suppression = float(qr['quality_suppression'])
            quality_positive = bool(suppression > 0.0)
            concordant = bool(cross_positive and quality_positive)
            rows.append({
                'group': group,
                'representative_family_id': rfid,
                'v31_rank': rrank,
                'surfaced': rsurf,
                'crossroute_rank_gap': None if gap is None else float(gap),
                'quality_suppression': suppression,
                'crossroute_positive': cross_positive,
                'quality_positive': quality_positive,
                'concordant_positive': concordant,
            })
        surfaced = [r for r in rows if r['surfaced']]
        missed = [r for r in rows if not r['surfaced']]
        require(len(surfaced) == 9 and len(missed) == 9, f'{year} derived surfaced/missed split changed')
        ss = summarize(surfaced)
        ms = summarize(missed)
        gate = bool(ms['concordant_positive_count'] >= 1 and ms['concordant_positive_fraction'] > ss['concordant_positive_fraction'])
        gate_flags.append(gate)
        annual[year] = {
            'recoverable_groups': 18,
            'surfaced_groups': 9,
            'missed_groups': 9,
            'surfaced_summary': ss,
            'missed_summary': ms,
            'missed_minus_surfaced_concordant_fraction': float(ms['concordant_positive_fraction'] - ss['concordant_positive_fraction']),
            'concordant_direction_gate': gate,
            'groups': rows,
        }

    supported = bool(all(gate_flags))
    result = {
        'verdict': 'PASS_V31_CONCORDANT_INDEPENDENT_SUPPRESSION_DIAGNOSTIC' if supported else 'FAIL_V31_CONCORDANT_INDEPENDENT_SUPPRESSION_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CONCORDANT_SELECTOR_OR_SUCCESSOR_EVALUATED',
        'rank_source_run': RANK_RUN,
        'rank_source_artifact': RANK_ARTIFACT,
        'rank_source_digest': RANK_DIGEST,
        'quality_source_run': QUALITY_RUN,
        'quality_source_artifact': QUALITY_ARTIFACT,
        'quality_source_digest': QUALITY_DIGEST,
        'crossroute_positive_definition': 'crossroute_rank_gap>0; unlinked/no usable Sugar rank is false',
        'quality_positive_definition': 'quality_suppression>0',
        'concordant_positive_definition': 'crossroute_positive AND quality_positive',
        'annual_diagnostics': annual,
        'concordant_independent_suppression_supported_both_years': supported,
        'interpretation_gate': 'in each year >=1 missed concordant-positive group and missed concordant-positive fraction strictly greater than surfaced fraction; no effect-size threshold',
        'new_rank_or_score_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'signal_magnitude_used': False,
        'sum_search': False,
        'product_search': False,
        'ratio_search': False,
        'absolute_value_search': False,
        'coefficient_search': False,
        'nonzero_threshold_search': False,
        'or_logic_search': False,
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
    out = a.output / 'V31_CONCORDANT_INDEPENDENT_SUPPRESSION_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'concordant_independent_suppression_supported_both_years': supported,
        'annual': {
            y: {
                'surfaced_summary': x['surfaced_summary'],
                'missed_summary': x['missed_summary'],
                'missed_minus_surfaced_concordant_fraction': x['missed_minus_surfaced_concordant_fraction'],
                'concordant_direction_gate': x['concordant_direction_gate'],
            } for y, x in annual.items()
        },
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
