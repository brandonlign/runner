#!/usr/bin/env python3
"""Transport-parallel wrapper for the already frozen Rubin/MPC TNO screen.

Scientific selection criteria and parsers are imported unchanged from
rubin_mpc_tno_extreme_screen.py.  MPC's Orbits API is documented as single-
object only, so independent orbit requests are parallelized to avoid a purely
network-bound serial run.  This is an execution optimization, not a retune.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import rubin_mpc_tno_extreme_screen as p

MAX_WORKERS = 12


def fetch_orbit(desig: str):
    o = p.orbit_for(desig)
    o['screen_classes'] = p.classes(o)
    return o


def fetch_provenance(o: dict):
    o2 = dict(o)
    prov = p.earliest_observation(o['desig'])
    o2['observation_provenance'] = prov
    o2['rubin_discovery_provenance_pass'] = prov.get('first_station') == 'X05'
    return o2


def main():
    designations = sorted(set(p.list_year(2025) + p.list_year(2026)))
    parsed = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(fetch_orbit, d): d for d in designations}
        done = 0
        for f in as_completed(futs):
            done += 1
            d = futs[f]
            try:
                parsed.append(f.result())
            except Exception as exc:
                parsed.append({'desig': d, 'status': 'QUERY_ERROR', 'error': repr(exc), 'screen_classes': []})
            if done % 25 == 0 or done == len(designations):
                print(f'ORBITS {done}/{len(designations)}', flush=True)

    parsed.sort(key=lambda x: x['desig'])
    candidates = [x for x in parsed if x.get('screen_classes')]
    survivors = []
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, len(candidates)))) as ex:
        futs = {ex.submit(fetch_provenance, o): o['desig'] for o in candidates}
        for f in as_completed(futs):
            d = futs[f]
            try:
                survivors.append(f.result())
            except Exception as exc:
                base = next(x for x in candidates if x['desig'] == d)
                z = dict(base)
                z['observation_provenance'] = {'status': 'QUERY_ERROR', 'error': repr(exc)}
                z['rubin_discovery_provenance_pass'] = False
                survivors.append(z)
    survivors.sort(key=lambda x: x['desig'])
    rubin = [x for x in survivors if x['rubin_discovery_provenance_pass']]

    report = {
        'screen_frozen_before_candidate_values': True,
        'execution_note': 'Exact frozen screen, only independent MPC network requests parallelized',
        'screen': p.SCREEN,
        'candidate_years': [2025, 2026],
        'tnos_considered_n': len(designations),
        'orbits_parsed_n': sum(x.get('status') == 'OK' for x in parsed),
        'query_or_parse_failure_n': sum(x.get('status') != 'OK' for x in parsed),
        'all_screen_survivors_n': len(survivors),
        'rubin_first_observation_survivors_n': len(rubin),
        'rubin_first_observation_survivors': rubin,
        'all_screen_survivors': survivors,
        'failures': [x for x in parsed if x.get('status') != 'OK'],
        'guardrail': ('Screen survivors are hypotheses only. Do not claim novelty or dynamical stability '
                      'without designation-specific literature/MPC collision review and covariance-aware integration.'),
    }
    p.OUT.mkdir(parents=True, exist_ok=True)
    (p.OUT/'report.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({
        'tnos_considered_n': report['tnos_considered_n'],
        'orbits_parsed_n': report['orbits_parsed_n'],
        'query_or_parse_failure_n': report['query_or_parse_failure_n'],
        'all_screen_survivors_n': report['all_screen_survivors_n'],
        'rubin_first_observation_survivors_n': report['rubin_first_observation_survivors_n'],
        'rubin_first_observation_survivors': rubin,
    }, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
