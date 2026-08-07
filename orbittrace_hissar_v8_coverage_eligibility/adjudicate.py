#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

E = 0.01671
MEAN_MOTION_DEG_PER_DAY = 360.0 / 365.2422
MAX_ALLOWED_RATE_BOUND = 1.1
DECEMBER_DAYS = 31
BIN_WIDTH_DEG = 10.0
MIN_SCANNABLE_BINS = 24


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--structure-json', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    s = json.loads(a.structure_json.read_text())
    require(s['verdict'] == 'PASS_HISSAR_1968_1969_STRUCTURE_AUDIT', 'Hissar structure did not pass')
    require(all(s['documentation_gates'].values()), 'official documentation gate changed')
    require(s['documentation_gates']['period_1968_1969'] is True, 'official temporal span not established')
    require(s['documentation_gates']['record_count_8916'] is True, 'record-count metadata changed')
    require(s['documentation_gates']['ra_geocentric'] is True, 'RA interface changed')
    require(s['documentation_gates']['dec_geocentric'] is True, 'DEC interface changed')
    require(s['documentation_gates']['vg_geocentric'] is True, 'Vg interface changed')
    require(s['form_submitted'] is False, 'Hissar form already submitted')
    require(s['result_endpoint_contacted'] is False, 'Hissar result endpoint already contacted')
    require(s['scientific_record_access'] is False, 'Hissar scientific record already accessed')
    require(s['scientific_values_inspected'] is False, 'Hissar scientific value already inspected')
    require(s['source_labels_inspected'] is False, 'Hissar source label already inspected')
    require(s['orbittrace_target_information_access'] is False, 'OrbitTrace target information entered prerequisite')

    # Keplerian true-anomaly rate at perihelion:
    # dnu/dt = n * (1+e)^2 / (1-e^2)^(3/2).
    max_rate = MEAN_MOTION_DEG_PER_DAY * (1.0 + E) ** 2 / (1.0 - E * E) ** 1.5
    require(max_rate < MAX_ALLOWED_RATE_BOUND, f'conservative angular-rate bound invalid: {max_rate}')
    max_span = DECEMBER_DAYS * MAX_ALLOWED_RATE_BOUND
    # A continuous interval of length L can intersect at most ceil(L/w)+1 fixed bins.
    max_bins = int(math.ceil(max_span / BIN_WIDTH_DEG) + 1)
    require(max_bins < MIN_SCANNABLE_BINS, 'metadata-only coverage bound did not exclude powered Hissar test')

    result = {
        'verdict': 'INCONCLUSIVE_V8_HISSAR_1968_1969_EXTERNAL_POWER_COVERAGE',
        'candidate': 'Hissar/Hisar 1968-1969',
        'official_record_count': 8916,
        'official_temporal_span': 'December 1968 to October 1969 and in December 1969',
        'year_semantics': 'calendar_years_1968_and_1969_unchanged',
        'frozen_bin_width_deg': BIN_WIDTH_DEG,
        'frozen_min_scannable_bins_per_year': MIN_SCANNABLE_BINS,
        'earth_eccentricity_for_conservative_bound': E,
        'mean_motion_deg_per_day': MEAN_MOTION_DEG_PER_DAY,
        'computed_keplerian_max_rate_deg_per_day': max_rate,
        'conservative_rate_bound_deg_per_day': MAX_ALLOWED_RATE_BOUND,
        'maximum_possible_1968_calendar_days': DECEMBER_DAYS,
        'maximum_possible_1968_solar_longitude_span_deg': max_span,
        'maximum_possible_1968_fixed_10deg_bins_intersected': max_bins,
        'coverage_gate_mathematically_possible': max_bins >= MIN_SCANNABLE_BINS,
        'catalogue_form_submitted': False,
        'result_endpoint_contacted': False,
        'scientific_record_access': False,
        'scientific_values_inspected': False,
        'source_labels_inspected': False,
        'v8_method_changed': False,
        'coverage_floor_lowered': False,
        'year_panels_redefined': False,
        'orbittrace_target_information_access': False,
        'classification': 'external_power_inconclusive_preaccess_not_method_failure',
        'claim_boundary': (
            'Official Hissar metadata restricts calendar 1968 to December. Even granting all 31 December days and a deliberately loose 1.1 deg/day maximum solar-longitude rate, 1968 can intersect at most five fixed 10-degree bins, below the frozen 24-bin/year requirement. Therefore no Hissar catalogue submission is scientifically justified for this v8 external test.'
        ),
    }
    (a.output / 'hissar_v8_coverage_eligibility.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
