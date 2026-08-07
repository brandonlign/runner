#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--freshness-json', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    fresh = json.loads(a.freshness_json.read_text())
    require(fresh['verdict'] == 'PASS_FRIPON_2018_2019_REPO_SCIENTIFIC_FRESHNESS_AUDIT', 'freshness prerequisite changed')
    require(fresh['reserved_years'] == [2018, 2019], 'reserved years changed')
    require(fresh['potential_exposure_hit_count'] == 0, 'prior repository freshness changed')
    require(all(fresh['positive_controls'].values()), 'freshness positive control failed')
    require(fresh['fripon_web_or_api_contacted'] is False, 'freshness itself contacted FRIPON')
    require(fresh['scientific_value_access_this_audit'] is False, 'freshness itself inspected science')
    require(fresh['orbittrace_target_information_access'] is False, 'freshness itself accessed target')

    result = {
        'verdict': 'FAIL_FRIPON_2018_2019_EXTERNAL_INTEGRITY_PREPROTOCOL_EXPOSURE',
        'reserved_years': [2018, 2019],
        'prior_repo_freshness_verdict_preserved': fresh['verdict'],
        'prior_repo_freshness_run_id': 31227452342,
        'prior_repo_freshness_artifact_id': 9012594819,
        'first_structure_run_id': 31227702721,
        'first_structure_outcome': 'STATIC_WORKFLOW_GUARD_FAILURE_BEFORE_FRIPON_CONTACT',
        'corrected_structure_run_id': 31227857678,
        'corrected_structure_outcome': 'NONRESERVED_PUBLIC_INTERFACE_CONNECT_TIMEOUT_ON_FIRST_FIXED_PAGE',
        'unintended_reserved_year_web_search_exposure': True,
        'exposure_year': 2019,
        'exposure_categories': [
            'specific_event_identity_or_date_context',
            'pipeline_or_orbital_scientific_fields',
        ],
        'numeric_exposed_values_copied_into_repository': False,
        'exposed_values_used_for_method_or_parser_decisions': False,
        'alternate_FRIPON_year_pair_authorized': False,
        'reserved_FRIPON_scientific_protocol_frozen_before_exposure': False,
        'v8_scientific_evaluation_performed_on_FRIPON': False,
        'v8_method_changed': False,
        'orbittrace_target_information_access': False,
        'classification': 'external_panel_integrity_failure_not_method_failure',
        'claim_boundary': (
            'FRIPON 2018/2019 was clean in repository history, but an external web-search response unintentionally surfaced 2019 event-level scientific information before the full reserved-year scientific protocol was frozen. The panel is therefore permanently disqualified as a pristine external validation. No exposed numeric value is reproduced here or used for any scientific decision. The two structure attempts are separately preserved as pre-contact static-guard failure and non-reserved transport timeout.'
        ),
    }
    (a.output / 'fripon_2018_2019_integrity_stop.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
