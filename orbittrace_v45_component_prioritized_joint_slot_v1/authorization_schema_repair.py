#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from orbittrace_v45_component_prioritized_joint_slot_v1 import train_evaluate as v45


def validate_placement_diagnostic(path: Path) -> None:
    v45.require(v45.v40.v22.sha(path) == v45.PLACEMENT_RESULT_SHA, '#1113 placement result identity changed')
    r = json.loads(path.read_text())
    v45.require(r['verdict'] == 'PASS_V42_JOINT_COMPONENT_PLACEMENT_DIAGNOSTIC', '#1113 verdict changed')
    v45.require(r['scientific_role'] == 'POST_V42_DIAGNOSTIC_ONLY_CONDITIONAL_COMPONENT_PLACEMENT_NO_SUCCESSOR_EVALUATED', '#1113 role changed')
    v45.require(int(r['joint_family_count']) == v45.JOINT_N, '#1113 joint family count changed')
    v45.require(r['placement_statistic'] == 'component_best_v31_percentile', '#1113 placement statistic changed')
    v45.require(r['placement_direction_supported_both_years_both_levels'] is True, '#1113 direction not supported')
    v45.require(r['graph_sha256'] == v45.v40.GRAPH_SHA256 and r['component_sha256'] == v45.v40.COMPONENT_SHA256, '#1113 geometry identity changed')
    v45.require(set(r['annual_diagnostics']) == {'2013', '2014'}, '#1113 annual universe changed')
    v45.require(r['new_rank_or_score_evaluated'] is False and r['selector_evaluated'] is False, '#1113 was not diagnostic-only')
    v45.require(r['replacement_rule_evaluated'] is False and r['successor_selected'] is False, '#1113 selected a successor')
    v45.require(r['sonotaco_role'] == 'EXPOSED_DEVELOPMENT_ONLY', '#1113 SonotaCo role changed')
    v45.require(r['target_information_access'] is False and r['target_region_events_accessed'] is False, '#1113 target firewall changed')
    v45.require(r['maarsy_scientific_access'] is False and r['dms_scientific_access'] is False, '#1113 survey firewall changed')
    v45.require(r['blind_exclusion'] == [20.0, 55.0], '#1113 blind exclusion changed')


v45.validate_placement_diagnostic = validate_placement_diagnostic

if __name__ == '__main__':
    raise SystemExit(v45.main())
