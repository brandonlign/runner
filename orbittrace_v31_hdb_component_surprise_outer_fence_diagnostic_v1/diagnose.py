#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FREEZE_VERDICT = 'PASS_V31_HDB_COMPONENT_SURPRISE_OUTER_FENCE_FREEZE'
CLOSURE_VERDICT = 'PASS_V31_CROSSROUTE_COMPONENT_CLOSURE_DIAGNOSTIC'
GRAPH_SHA = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'


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
    ap.add_argument('--freeze', type=Path, required=True)
    ap.add_argument('--closure-result', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()

    f = json.loads(args.freeze.read_text())
    require(f['verdict'] == FREEZE_VERDICT, 'invalid frozen extreme set')
    require(f['truth_accessed'] is False and f['surfaced_missed_truth_accessed'] is False, 'extreme set was not frozen before truth')
    require(f['pretruth_graph_sha256'] == GRAPH_SHA and f['pretruth_component_sha256'] == COMPONENT_SHA, 'frozen geometry changed')
    require(f['outer_fence_multiplier'] == 3.0 and f['threshold_search'] is False, 'outer-fence rule changed')
    extreme = set(map(str, f['extreme_component_ids']))
    require(len(extreme) == int(f['extreme_component_count']), 'extreme component identity mismatch')

    c = json.loads(args.closure_result.read_text())
    require(c['verdict'] == CLOSURE_VERDICT, 'unexpected #1072 verdict')
    require(c['pretruth_graph_sha256'] == GRAPH_SHA and c['pretruth_component_identity_sha256'] == COMPONENT_SHA, '#1072 geometry changed')
    require(c['component_closure_direction_supported'] is True, '#1072 closure direction not supported')
    require(c['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1072 role changed')
    require(c['target_information_access'] is False and c['target_region_events_accessed'] is False, 'target access in #1072')
    require(c['maarsy_scientific_access'] is False and c['dms_scientific_access'] is False, 'protected external access in #1072')

    annual = {}
    both = True
    for year in ('2013', '2014'):
        rows = list(c['annual_diagnostics'][year]['recoverable_group_rows'])
        surfaced = [r for r in rows if bool(r['surfaced_hdb'])]
        missed = [r for r in rows if not bool(r['surfaced_hdb'])]
        require(len(surfaced) == 9 and len(missed) == 9, f'{year} recoverable split changed')
        surfaced_extreme = [r for r in surfaced if str(r['component_id']) in extreme]
        missed_extreme = [r for r in missed if str(r['component_id']) in extreme]
        sf = len(surfaced_extreme) / len(surfaced)
        mf = len(missed_extreme) / len(missed)
        pass_year = bool(len(missed_extreme) >= 1 and mf > sf)
        both = bool(both and pass_year)
        annual[year] = {
            'surfaced_recoverable_group_count': len(surfaced),
            'missed_recoverable_group_count': len(missed),
            'surfaced_extreme_group_count': len(surfaced_extreme),
            'missed_extreme_group_count': len(missed_extreme),
            'surfaced_extreme_fraction': sf,
            'missed_extreme_fraction': mf,
            'missed_has_at_least_one_extreme': bool(len(missed_extreme) >= 1),
            'missed_extreme_fraction_gt_surfaced': bool(mf > sf),
            'interpretation_gate_pass': pass_year,
        }

    result = {
        'verdict': 'PASS_V31_HDB_COMPONENT_SURPRISE_OUTER_FENCE_DIAGNOSTIC' if both else 'FAIL_V31_HDB_COMPONENT_SURPRISE_OUTER_FENCE_DIAGNOSTIC',
        'scientific_role': 'POST_V40_EXPOSED_DIAGNOSTIC_OF_PREDECLARED_SPARSE_COMPONENT_SURPRISE_EXTREMES',
        'question': 'Are truth-blind Tukey-outer-fence cross-route component-surprise extremes selectively enriched for recoverable-but-missed HDB groups in both years?',
        'freeze_sha256': sha(args.freeze),
        'closure_result_sha256': sha(args.closure_result),
        'pretruth_graph_sha256': GRAPH_SHA,
        'pretruth_component_sha256': COMPONENT_SHA,
        'hdb_route_component_count': int(f['hdb_route_component_count']),
        'extreme_component_count': int(f['extreme_component_count']),
        'outer_fence_multiplier': 3.0,
        'outer_fence_threshold': float(f['outer_fence_threshold']),
        'annual_diagnostics': annual,
        'direction_supported_both_years': bool(both),
        'successor_selected': False,
        'successor_evaluated': False,
        'new_rank_or_score_evaluated': False,
        'replacement_rule_evaluated': False,
        'promotion_position_selected': False,
        'oracle_identity_hardcoded': False,
        'threshold_search': False,
        'alternative_outlier_rule_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'route_specific_rule': False,
        'component_evidence_aggregation_search': False,
        'radius_search': False,
        'metric_search': False,
        'graph_pruning': False,
        'graph_expansion': False,
        'component_definition_search': False,
        'candidate_generation_changed': False,
        'membership_changed': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'annual_combiner_search': False,
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

    args.output.mkdir(parents=True, exist_ok=True)
    p = args.output / 'V31_HDB_COMPONENT_SURPRISE_OUTER_FENCE_DIAGNOSTIC.json'
    p.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
