#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

SOURCE_RUN = 31454067856
SOURCE_ARTIFACT = 9087373195
SOURCE_ZIP_SHA256 = '361e6113110dcc58761a458fc842f8c3e613f79d0e13a85c593bad297cd49d7a'
SOURCE_COMMIT = 'b0f9efdafb6c4662fc8ac84bd6201bc54cd3191e'
HDB_N = 229
EXPECTED_HDB = {
    2013: (0.14888037368183737, 9, 11),
    2014: (0.15198123772301594, 9, 9),
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def canonical_order_sha(order: list[str]) -> str:
    return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    require(rows, 'empty diagnostic class')
    x = np.asarray([float(r['quality_suppression']) for r in rows], dtype=float)
    vr = np.asarray([int(r['v31_rank']) for r in rows], dtype=float)
    qr = np.asarray([int(r['quality_rank']) for r in rows], dtype=float)
    require(np.all(np.isfinite(x)), 'nonfinite suppression')
    q25, q75 = np.percentile(x, [25.0, 75.0], method='linear')
    pos = int(np.sum(x > 0.0))
    return {
        'groups': len(rows),
        'median_quality_suppression': float(np.median(x)),
        'mean_quality_suppression': float(np.mean(x)),
        'q25_quality_suppression': float(q25),
        'q75_quality_suppression': float(q75),
        'min_quality_suppression': float(np.min(x)),
        'max_quality_suppression': float(np.max(x)),
        'positive_suppression_count': pos,
        'positive_suppression_fraction': float(pos / len(rows)),
        'median_v31_rank': float(np.median(vr)),
        'median_quality_rank': float(np.median(qr)),
    }


def validate_pretruth(hdb_root: Path) -> tuple[dict[str, Any], list[str], dict[str, int]]:
    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    fam = json.loads((hdb_root / 'family_memberships.json').read_text())
    require(meta['truth_accessed'] is False and fam['truth_accessed'] is False, 'HDB payload not pretruth')
    require(int(meta['feature_dimension']) == 71, 'feature dimension changed')
    ids = list(map(str, meta['family_ids']))
    quality = list(map(str, meta['quality_order']))
    v19 = list(map(str, meta['v19_order']))
    require(len(ids) == HDB_N and len(set(ids)) == HDB_N, 'HDB family universe changed')
    require(len(quality) == HDB_N and set(quality) == set(ids), 'quality order universe changed')
    require(len(v19) == HDB_N and set(v19) == set(ids), 'v19 order universe changed')
    require([str(x['family_id']) for x in fam['families']] == ids, 'membership family order changed')
    require(meta['target_information_access'] is False, 'pretruth target access flag changed')
    require(meta['maarsy_scientific_access'] is False and meta['dms_scientific_access'] is False, 'pretruth protected-survey access flag changed')
    qrank = {fid: i + 1 for i, fid in enumerate(quality)}
    return meta, quality, qrank


def validate_source(source_root: Path) -> dict[str, Any]:
    diag = source_root / 'diag' / 'V31_CROSSROUTE_RADIUS1_CORROBORATION_DIAGNOSTIC.json'
    graph = source_root / 'pretruth' / 'CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY.json'
    commit = source_root / 'execution_commit.txt'
    require(diag.is_file() and graph.is_file() and commit.is_file(), 'authoritative #1064 artifact incomplete')
    require(commit.read_text().strip() == SOURCE_COMMIT, '#1064 execution commit changed')
    d = json.loads(diag.read_text())
    g = json.loads(graph.read_text())
    require(d['verdict'] == 'PASS_V31_CROSSROUTE_RADIUS1_CORROBORATION_DIAGNOSTIC', '#1064 verdict changed')
    require(d['scientific_role'] == 'POST_RESULT_DIAGNOSTIC_ONLY_NO_CROSSROUTE_RANK_EVALUATED', '#1064 role changed')
    require(d['crossroute_score_or_rerank_evaluated'] is False and d['successor_selected'] is False, '#1064 unexpectedly evaluated successor')
    require(g['verdict'] == 'PASS_CROSSROUTE_RADIUS1_PRETRUTH_GRAPH_IDENTITY' and g['truth_accessed'] is False, '#1064 pretruth graph changed')
    require(int(g['edge_count']) == 2334 and len(g['hdbscan_family_ids']) == HDB_N, '#1064 graph identity changed')
    require(d['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1064 SonotaCo role changed')
    for obj in (d, g):
        require(obj['target_information_access'] is False and obj['target_region_events_accessed'] is False, 'protected target access flag changed')
        require(obj['maarsy_scientific_access'] is False and obj['dms_scientific_access'] is False, 'protected survey access flag changed')
        require(obj['blind_exclusion'] == [20.0, 55.0], 'blind exclusion changed')
    got = {}
    for row in d['v31_reproduction']:
        if str(row['comparator']) == 'hdbscan':
            got[int(row['year'])] = (float(row['macro_f1']), int(row['recovered_f1_gt_0_5']), int(row['candidate_used']))
    require(set(got) == set(EXPECTED_HDB), 'HDB parent panels changed')
    for year, exp in EXPECTED_HDB.items():
        cur = got[year]
        require(abs(cur[0] - exp[0]) < 1e-12 and cur[1] == exp[1] and cur[2] == exp[2], f'v31 HDB control changed {year}')
    require(set(d['annual_diagnostics']) == {'2013', '2014'}, 'annual diagnostic years changed')
    return d


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--hdb-root', type=Path, required=True)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    meta, quality_order, qrank = validate_pretruth(a.hdb_root)
    source = validate_source(a.source_root)
    hdb_ids = set(map(str, meta['family_ids']))

    annual = {}
    direction_flags = []
    for year in (2013, 2014):
        src = source['annual_diagnostics'][str(year)]
        budget = EXPECTED_HDB[year][2]
        require(int(src['hdb_budget']) == budget, f'HDB budget changed {year}')
        require(int(src['annual_recoverable_hdb_groups']) == 18, f'recoverable group count changed {year}')
        require(int(src['surfaced_hdb_groups']) == 9 and int(src['missed_hdb_groups']) == 9, f'surfaced/missed split changed {year}')
        rows = []
        seen_groups = set()
        for r in src['groups']:
            fid = str(r['hdb_representative_family_id'])
            group = str(r['group'])
            vrank = int(r['hdb_representative_rank'])
            require(fid in hdb_ids and 1 <= vrank <= HDB_N, 'source representative outside HDB universe')
            require(group not in seen_groups, 'duplicate recoverable group')
            seen_groups.add(group)
            qr = int(qrank[fid])
            pv = float((vrank - 1) / (HDB_N - 1))
            pq = float((qr - 1) / (HDB_N - 1))
            suppression = float(pv - pq)
            rows.append({
                'group': group,
                'representative_family_id': fid,
                'v31_rank': vrank,
                'quality_rank': qr,
                'p_v31': pv,
                'p_quality': pq,
                'quality_suppression': suppression,
                'surfaced': bool(r['surfaced_hdb']),
            })
        require(len(rows) == 18 and len(seen_groups) == 18, 'recoverable group rows changed')
        surfaced = [r for r in rows if r['surfaced']]
        missed = [r for r in rows if not r['surfaced']]
        require(len(surfaced) == 9 and len(missed) == 9, 'derived surfaced/missed split changed')
        ss = summarize(surfaced)
        ms = summarize(missed)
        delta = float(ms['median_quality_suppression'] - ss['median_quality_suppression'])
        direction = bool(ms['median_quality_suppression'] > 0.0 and delta > 0.0)
        direction_flags.append(direction)
        annual[str(year)] = {
            'hdb_budget': budget,
            'recoverable_groups': 18,
            'surfaced_groups': 9,
            'missed_groups': 9,
            'surfaced_summary': ss,
            'missed_summary': ms,
            'missed_minus_surfaced_median_suppression': delta,
            'quality_suppression_direction': direction,
            'groups': rows,
        }

    supported = bool(all(direction_flags))
    result = {
        'verdict': 'PASS_V31_QUALITY_SUPPRESSION_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_QUALITY_RERANK_OR_SUCCESSOR_EVALUATED',
        'source_run_id': SOURCE_RUN,
        'source_artifact_id': SOURCE_ARTIFACT,
        'source_zip_sha256': SOURCE_ZIP_SHA256,
        'source_execution_commit': SOURCE_COMMIT,
        'hdb_family_count': HDB_N,
        'quality_order_sha256': canonical_order_sha(quality_order),
        'quality_order_role': 'immutable pre-SonotaCo #839/#853 quality-diversity order from #950 manifest',
        'suppression_definition': '((v31_rank-1)/228)-((quality_rank-1)/228)',
        'positive_suppression_meaning': 'the frozen pre-SonotaCo quality prior ranks the same HDB candidate better than exact v31',
        'annual_diagnostics': annual,
        'quality_suppression_direction_supported_both_years': supported,
        'interpretation_gate': 'missed median suppression >0 and > surfaced median suppression in both years; no effect-size threshold',
        'new_rank_or_score_evaluated': False,
        'quality_rerank_evaluated': False,
        'quality_v31_fusion_evaluated': False,
        'successor_selected': False,
        'absolute_value_search': False,
        'ratio_search': False,
        'log_transform_search': False,
        'clipping_search': False,
        'coefficient_search': False,
        'threshold_search': False,
        'rank_window_search': False,
        'top_k_search': False,
        'component_aggregation_search': False,
        'consensus_alternative_search': False,
        'v19_alternative_search': False,
        'feature_search': False,
        'model_search': False,
        'target_search': False,
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
    out = a.output / 'V31_QUALITY_SUPPRESSION_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'quality_suppression_direction_supported_both_years': supported,
        'annual': {
            y: {
                'surfaced_summary': x['surfaced_summary'],
                'missed_summary': x['missed_summary'],
                'missed_minus_surfaced_median_suppression': x['missed_minus_surfaced_median_suppression'],
                'quality_suppression_direction': x['quality_suppression_direction'],
            } for y, x in annual.items()
        },
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
