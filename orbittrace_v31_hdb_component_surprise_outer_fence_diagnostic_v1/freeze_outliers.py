#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

V40_VERDICT = 'FAIL_V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT'
GRAPH_SHA = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
HDB_V31_SHA = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--v40-result', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()

    r = json.loads(args.v40_result.read_text())
    require(r['verdict'] == V40_VERDICT, 'unexpected v40 verdict')
    require(r['pretruth_graph_sha256'] == GRAPH_SHA, 'v40 graph identity changed')
    require(r['pretruth_component_sha256'] == COMPONENT_SHA, 'v40 component identity changed')
    require(r['order_diagnostics']['hdbscan']['v31_fused_order_sha256'] == HDB_V31_SHA, 'HDB v31 order changed')
    require(r['parent_v31_reproduction_pass'] is True, 'v40 did not reproduce v31 parent')
    require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', 'v40 role changed')
    require(r['target_information_access'] is False and r['target_region_events_accessed'] is False, 'target access in source result')
    require(r['maarsy_scientific_access'] is False and r['dms_scientific_access'] is False, 'protected external access in source result')

    rows = list(r['primary_component_rows']['hdbscan'])
    require(len(rows) == 138, 'HDB route-component representative count changed')
    seen = set()
    vals = []
    frozen_rows = []
    for row in rows:
        cid = str(row['component_id'])
        require(cid not in seen, 'duplicate HDB component')
        seen.add(cid)
        own = float(row['representative_v31_percentile'])
        evidence = float(row['component_evidence'])
        d = own - evidence
        require(np.isfinite(d) and d >= -1e-15, 'invalid component surprise')
        d = max(0.0, d)
        vals.append(d)
        frozen_rows.append({
            'component_id': cid,
            'representative_family_id': str(row['representative_family_id']),
            'representative_v31_rank': int(row['representative_v31_rank']),
            'representative_v31_percentile': own,
            'component_evidence': evidence,
            'component_surprise': d,
            'best_evidence_route': str(row['best_evidence_route']),
        })

    arr = np.asarray(vals, dtype=float)
    q1, q3 = [float(x) for x in np.quantile(arr, [0.25, 0.75], method='linear')]
    iqr = float(q3 - q1)
    threshold = float(q3 + 3.0 * iqr)
    extreme = sorted([x['component_id'] for x in frozen_rows if float(x['component_surprise']) > threshold])

    out = {
        'verdict': 'PASS_V31_HDB_COMPONENT_SURPRISE_OUTER_FENCE_FREEZE',
        'scientific_role': 'TRUTH_BLIND_SPARSE_COMPONENT_SURPRISE_SET_FREEZE_BEFORE_EXPOSED_GROUP_DIAGNOSIS',
        'authoritative_v40_result_sha256': sha(args.v40_result),
        'source_v40_verdict': V40_VERDICT,
        'pretruth_graph_sha256': GRAPH_SHA,
        'pretruth_component_sha256': COMPONENT_SHA,
        'hdb_v31_fused_order_sha256': HDB_V31_SHA,
        'hdb_route_component_count': len(rows),
        'surprise_definition': 'representative_v31_percentile - component_evidence',
        'quantile_method': 'numpy linear',
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'outer_fence_multiplier': 3.0,
        'outer_fence_threshold': threshold,
        'extreme_component_count': len(extreme),
        'extreme_component_ids': extreme,
        'component_rows': frozen_rows,
        'truth_accessed': False,
        'surfaced_missed_truth_accessed': False,
        'threshold_search': False,
        'alternative_outlier_rule_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'route_specific_rule': False,
        'successor_evaluated': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    p = args.output / 'V31_HDB_COMPONENT_SURPRISE_OUTER_FENCE_FREEZE.json'
    p.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': out['verdict'],
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'outer_fence_threshold': threshold,
        'extreme_component_count': len(extreme),
        'freeze_sha256': sha(p),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
