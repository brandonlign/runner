#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1

ANOMALOUS_FOLD = 4
AUTHORITATIVE_RANKGAP_SHA256 = 'e4e09546e17b9a5da7ce12ad9af4bb7129533fd9b5be846ebc859719f01a9758'
EXPECTED = {
    2013: {'candidate_recoverable': 18, 'surfaced': 9, 'missed': 9},
    2014: {'candidate_recoverable': 19, 'surfaced': 9, 'missed': 10},
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--rankgap-result', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(sha256(a.rankgap_result) == AUTHORITATIVE_RANKGAP_SHA256, '#1046 rank-gap result changed')
    src: dict[str, Any] = json.loads(a.rankgap_result.read_text())
    require(src['verdict'] == 'PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC', '#1046 verdict changed')
    require(src['new_rank_evaluated'] is False and src['successor_selected'] is False, '#1046 scientific role changed')
    require(src['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1046 SonotaCo role changed')
    require(src['target_information_access'] is False and src['target_region_events_accessed'] is False, '#1046 target firewall changed')
    require(src['maarsy_scientific_access'] is False and src['dms_scientific_access'] is False, '#1046 survey firewall changed')

    annual: dict[str, Any] = {}
    all_pass = True
    for year in (2013, 2014):
        rows = list(src['annual'][str(year)]['rows'])
        recoverable = [r for r in rows if bool(r['candidate_recoverable'])]
        surfaced = [r for r in recoverable if bool(r['v31_surfaced_recoverable'])]
        missed = [r for r in recoverable if bool(r['recoverable_but_missed'])]
        exp = EXPECTED[year]
        require(len(recoverable) == exp['candidate_recoverable'], f'{year} recoverable count changed')
        require(len(surfaced) == exp['surfaced'], f'{year} surfaced count changed')
        require(len(missed) == exp['missed'], f'{year} missed count changed')
        require(len(surfaced) + len(missed) == len(recoverable), f'{year} recoverable class partition changed')

        def fold_row(row: dict[str, Any]) -> int:
            label = str(row['label'])
            require(label.startswith('MDC_GROUP:'), f'{year} unexpected shower label')
            return int(v1.deterministic_fold('SHOWER/' + label))

        surfaced_folds = [fold_row(r) for r in surfaced]
        missed_folds = [fold_row(r) for r in missed]
        require(all(0 <= f < 5 for f in surfaced_folds + missed_folds), f'{year} invalid fold')
        surfaced_n = sum(f == ANOMALOUS_FOLD for f in surfaced_folds)
        missed_n = sum(f == ANOMALOUS_FOLD for f in missed_folds)
        surfaced_frac = surfaced_n / len(surfaced_folds)
        missed_frac = missed_n / len(missed_folds)
        year_pass = bool(missed_frac > surfaced_frac)
        all_pass = all_pass and year_pass
        annual[str(year)] = {
            'candidate_recoverable_groups': len(recoverable),
            'surfaced_groups': len(surfaced),
            'missed_groups': len(missed),
            'anomalous_fold': ANOMALOUS_FOLD,
            'surfaced_anomalous_fold_count': surfaced_n,
            'surfaced_anomalous_fold_fraction': surfaced_frac,
            'missed_anomalous_fold_count': missed_n,
            'missed_anomalous_fold_fraction': missed_frac,
            'difference_missed_minus_surfaced': missed_frac - surfaced_frac,
            'direction_pass': year_pass,
        }

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V61_ANOMALOUS_FOLD_CONCENTRATION_DIAGNOSTIC_V1',
        'scientific_role': 'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'verdict': 'PASS_V61_ANOMALOUS_FOLD_CONCENTRATION_DIAGNOSTIC' if all_pass else 'FAIL_V61_ANOMALOUS_FOLD_CONCENTRATION_DIAGNOSTIC',
        'authoritative_status_source': '#1046 binding v31 HDB missed-label rank-gap diagnostic',
        'authoritative_status_sha256': AUTHORITATIVE_RANKGAP_SHA256,
        'anomalous_fold': ANOMALOUS_FOLD,
        'anomalous_fold_preselected_from_outcome_free_geometry': True,
        'sole_statistic': 'fraction of fixed #1046 surfaced/missed candidate-recoverable HDB shower groups assigned to inherited deterministic fold 4',
        'pass_rule': 'missed fold-4 fraction strictly greater than surfaced fold-4 fraction in both 2013 and 2014',
        'annual': annual,
        'new_rank_evaluated': False,
        'successor_selected': False,
        'literature_panel_evaluated': False,
        'fold_search': False,
        'alternate_fold_evaluated': False,
        'alternate_representative_used': False,
        'cutoff_selected': False,
        'parameter_search': False,
        'feature_search': False,
        'model_search': False,
        'metric_search': False,
        'k_search': False,
        'scaling_search': False,
        'threshold_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_search': False,
        'post_result_second_diagnostic': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = a.output / 'V61_ANOMALOUS_FOLD_CONCENTRATION_DIAGNOSTIC.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
