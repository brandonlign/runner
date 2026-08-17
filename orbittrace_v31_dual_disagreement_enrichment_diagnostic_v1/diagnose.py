#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HDB_N = 229
SOURCE_RUN = 31455141716
SOURCE_ARTIFACT = 9087743465
SOURCE_DIGEST = 'sha256:8c45c00fd70300efb2f6f32bbb339141f8c34884ee5b1098c1bbb45ccf1a59cc'
SOURCE_COMMIT = 'd43e3407f0e7bfb4b6405842b803817c4445aacf'
GRAPH_SHA = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMP_SHA = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
EXPECTED_HDB = {
    2013: (0.14888037368183737, 9, 11),
    2014: (0.15198123772301594, 9, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_quality(hdb_root: Path) -> tuple[list[str], dict[str, int]]:
    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fam = json.loads((hdb_root / 'family_memberships.json').read_text())
    require(meta['truth_accessed'] is False and fam['truth_accessed'] is False, 'HDB payload not pretruth')
    require(int(meta['feature_dimension']) == 71, 'feature dimension changed')
    ids = list(map(str, meta['family_ids']))
    quality = list(map(str, meta['quality_order']))
    require(len(ids) == HDB_N and len(set(ids)) == HDB_N, 'HDB family universe changed')
    require(len(quality) == HDB_N and set(quality) == set(ids), 'quality-order universe changed')
    require([str(x['family_id']) for x in fam['families']] == ids, 'family membership order changed')
    require(meta['target_information_access'] is False, 'target access flag changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, 'protected survey access flag changed')
    return ids, {fid: i + 1 for i, fid in enumerate(quality)}


def load_source(source_root: Path) -> dict[str, Any]:
    diag_path = source_root / 'diag' / 'V31_CROSSROUTE_COMPONENT_CLOSURE_DIAGNOSTIC.json'
    graph_path = source_root / 'pretruth' / 'CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY.json'
    comp_path = source_root / 'pretruth' / 'CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY.json'
    commit_path = source_root / 'execution_commit.txt'
    require(diag_path.is_file() and graph_path.is_file() and comp_path.is_file() and commit_path.is_file(), '#1072 artifact incomplete')
    require(commit_path.read_text().strip() == SOURCE_COMMIT, '#1072 execution commit changed')
    d = json.loads(diag_path.read_text())
    g = json.loads(graph_path.read_text())
    c = json.loads(comp_path.read_text())
    require(d['verdict'] == 'PASS_V31_CROSSROUTE_COMPONENT_CLOSURE_DIAGNOSTIC', '#1072 verdict changed')
    require(d['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_COMPONENT_SCORE_OR_SELECTOR_EVALUATED', '#1072 role changed')
    require(d['new_rank_or_score_evaluated'] is False and d['component_selector_evaluated'] is False and d['successor_selected'] is False, '#1072 unexpectedly evaluated successor')
    require(d['pretruth_graph_sha256'] == GRAPH_SHA and d['pretruth_component_identity_sha256'] == COMP_SHA, '#1072 frozen identities changed')
    require(g['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY' and g['truth_accessed'] is False, 'graph identity invalid')
    require(c['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_COMPONENT_CLOSURE_IDENTITY' and c['truth_accessed'] is False, 'component identity invalid')
    require(int(g['edge_count']) == 2334 and int(c['component_count']) == 196, 'graph/component counts changed')
    for obj in (d, g, c):
        require(obj['target_information_access'] is False and obj['target_region_events_accessed'] is False, 'protected target access flag changed')
        require(obj['maarsy_scientific_access'] is False and obj['dms_scientific_access'] is False, 'protected survey access flag changed')
        require(obj['blind_exclusion'] == [20.0, 55.0], 'blind exclusion changed')
    got = {}
    for row in d['v31_reproduction']:
        if str(row['comparator']) == 'hdbscan':
            got[int(row['year'])] = (float(row['macro_f1']), int(row['recovered_f1_gt_0_5']), int(row['candidate_used']))
    require(set(got) == set(EXPECTED_HDB), 'HDB v31 controls missing')
    for year, exp in EXPECTED_HDB.items():
        cur = got[year]
        require(abs(cur[0] - exp[0]) < 1e-12 and cur[1] == exp[1] and cur[2] == exp[2], f'HDB v31 control changed {year}')
    return d


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    require(rows, 'empty class')
    q = sum(bool(r['quality_suppressed']) for r in rows)
    c = sum(bool(r['component_supported']) for r in rows)
    both = sum(bool(r['dual_disagreement']) for r in rows)
    n = len(rows)
    return {
        'groups': n,
        'quality_suppressed_count': q,
        'quality_suppressed_fraction': q / n,
        'component_supported_count': c,
        'component_supported_fraction': c / n,
        'dual_disagreement_count': both,
        'dual_disagreement_fraction': both / n,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--hdb-root', type=Path, required=True)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    ids, qrank = load_quality(a.hdb_root)
    idset = set(ids)
    src = load_source(a.source_root)

    annual = {}
    gates = []
    for year in (2013, 2014):
        s = src['annual_diagnostics'][str(year)]
        require(int(s['hdb_budget']) == EXPECTED_HDB[year][2], f'budget changed {year}')
        require(int(s['annual_recoverable_hdb_groups']) == 18, f'recoverable group count changed {year}')
        require(int(s['surfaced_recoverable_hdb_groups']) == 9 and int(s['missed_recoverable_hdb_groups']) == 9, f'class counts changed {year}')
        rows = []
        seen_groups = set()
        for r in s['recoverable_group_rows']:
            fid = str(r['representative_family_id'])
            group = str(r['group'])
            vrank = int(r['representative_hdb_v31_rank'])
            own_p = float(r['representative_hdb_percentile'])
            comp_p = float(r['best_component_normalized_v31_percentile'])
            require(fid in idset and 1 <= vrank <= HDB_N, 'representative outside HDB universe')
            require(group not in seen_groups, 'duplicate recoverable group')
            seen_groups.add(group)
            qr = int(qrank[fid])
            quality_suppressed = bool(qr < vrank)
            component_supported = bool(comp_p < own_p)
            rows.append({
                'group': group,
                'representative_family_id': fid,
                'v31_rank': vrank,
                'quality_rank': qr,
                'quality_suppressed': quality_suppressed,
                'representative_hdb_percentile': own_p,
                'best_component_normalized_v31_percentile': comp_p,
                'component_supported': component_supported,
                'dual_disagreement': bool(quality_suppressed and component_supported),
                'surfaced': bool(r['surfaced_hdb']),
                'component_id': str(r['component_id']),
            })
        require(len(rows) == 18 and len(seen_groups) == 18, 'recoverable rows changed')
        surfaced = [r for r in rows if r['surfaced']]
        missed = [r for r in rows if not r['surfaced']]
        require(len(surfaced) == 9 and len(missed) == 9, 'surface/miss split changed')
        ss = summarize(surfaced)
        ms = summarize(missed)
        gate = bool(ms['dual_disagreement_count'] >= 1 and ms['dual_disagreement_fraction'] > ss['dual_disagreement_fraction'])
        gates.append(gate)
        annual[str(year)] = {
            'hdb_budget': EXPECTED_HDB[year][2],
            'surfaced_summary': ss,
            'missed_summary': ms,
            'missed_minus_surfaced_dual_fraction': ms['dual_disagreement_fraction'] - ss['dual_disagreement_fraction'],
            'dual_disagreement_enrichment_gate': gate,
            'groups': rows,
        }

    supported = bool(all(gates))
    result = {
        'verdict': 'PASS_V31_DUAL_DISAGREEMENT_ENRICHMENT_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_DUAL_DISAGREEMENT_SELECTOR_EVALUATED',
        'source_run_id': SOURCE_RUN,
        'source_artifact_id': SOURCE_ARTIFACT,
        'source_artifact_digest': SOURCE_DIGEST,
        'source_execution_commit': SOURCE_COMMIT,
        'pretruth_graph_sha256': GRAPH_SHA,
        'pretruth_component_sha256': COMP_SHA,
        'hdb_family_count': HDB_N,
        'quality_suppressed_definition': 'quality_rank < exact_v31_rank',
        'component_supported_definition': 'best_component_normalized_v31_percentile < representative_hdb_percentile',
        'dual_disagreement_definition': 'quality_suppressed AND component_supported',
        'annual_diagnostics': annual,
        'dual_disagreement_direction_supported_both_years': supported,
        'interpretation_gate': 'at least one missed dual-disagreement group and missed dual fraction > surfaced dual fraction in both years',
        'new_rank_or_score_evaluated': False,
        'dual_disagreement_selector_evaluated': False,
        'successor_selected': False,
        'or_rule_search': False,
        'quality_magnitude_threshold_search': False,
        'component_gain_threshold_search': False,
        'weighted_combination_search': False,
        'score_product_search': False,
        'score_sum_search': False,
        'quality_fusion_search': False,
        'component_rerank_search': False,
        'rank_window_search': False,
        'top_k_search': False,
        'route_specific_successor': False,
        'year_specific_successor': False,
        'budget_specific_successor': False,
        'candidate_generation_changed': False,
        'candidate_membership_changed': False,
        'feature_search': False,
        'model_search': False,
        'source_quota_selected': False,
        'oracle_identity_used_for_rule': False,
        'post_result_second_rule': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V31_DUAL_DISAGREEMENT_ENRICHMENT_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'dual_disagreement_direction_supported_both_years': supported,
        'annual': {
            y: {
                'surfaced_summary': v['surfaced_summary'],
                'missed_summary': v['missed_summary'],
                'missed_minus_surfaced_dual_fraction': v['missed_minus_surfaced_dual_fraction'],
                'dual_disagreement_enrichment_gate': v['dual_disagreement_enrichment_gate'],
            } for y, v in annual.items()
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
