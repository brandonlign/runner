#!/usr/bin/env python3
"""Prospective public-MPC screen for dynamically unusual Rubin TNOs.

This is a candidate-discovery screen, not a claim of a new dynamical class.
The selection rules below are frozen before inspecting the current Rubin/MPC
candidate values. They use only public MPC orbital solutions and observation
provenance. Surviving objects require later covariance/clone integration,
independent-archive checks, and a designation-specific collision audit.

Frozen screen classes (union):
  A. detached/extreme: q >= 40 au and a >= 150 au
  B. very-large-a:     q >= 30 au and a >= 250 au
  C. high-inclination: q >= 30 au and i >= 60 deg

Rubin provenance for a survivor requires its chronologically earliest public
MPC astrometric observation to use observatory code X05. This avoids treating
objects merely reobserved by Rubin as Rubin-discovered candidates.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import requests

OUT = Path('results/rubin_mpc_tno_extreme_screen')
OUT.mkdir(parents=True, exist_ok=True)
LIST_API = 'https://data.minorplanetcenter.net/api/list'
ORB_API = 'https://data.minorplanetcenter.net/api/get-orb'
OBS_API = 'https://data.minorplanetcenter.net/api/get-obs'

SCREEN = {
    'A_detached_extreme': {'q_min_au': 40.0, 'a_min_au': 150.0},
    'B_very_large_a': {'q_min_au': 30.0, 'a_min_au': 250.0},
    'C_high_inclination': {'q_min_au': 30.0, 'i_min_deg': 60.0},
}


def req(url: str, payload: dict, retries: int = 5):
    last = None
    for k in range(retries):
        try:
            r = requests.get(url, json=payload, timeout=(15, 90))
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last = exc
            time.sleep(2 * (k + 1))
    raise RuntimeError(f'API failed: {url} {payload}') from last


def norm_key(k: str) -> str:
    return ''.join(ch for ch in str(k).lower() if ch.isalnum())


def numeric(v: Any):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)) and math.isfinite(float(v)):
        return float(v)
    if isinstance(v, str):
        try:
            x = float(v)
            return x if math.isfinite(x) else None
        except Exception:
            return None
    return None


def flatten(obj: Any, prefix=''):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f'{prefix}.{k}' if prefix else str(k)
            out.append((p, k, v))
            out.extend(flatten(v, p))
    elif isinstance(obj, list):
        for j, v in enumerate(obj):
            out.extend(flatten(v, f'{prefix}[{j}]'))
    return out


def extract_by_alias(obj: Any, aliases):
    """Fallback parser for scalar-key representations."""
    aliases = {norm_key(x) for x in aliases}
    hits = []
    for path, key, value in flatten(obj):
        if norm_key(key) in aliases:
            x = numeric(value)
            if x is not None:
                hits.append((path, x))
    if not hits:
        return None, []
    rank_words = ('kepler', 'element', 'orbit')
    hits.sort(key=lambda z: (0 if any(w in z[0].lower() for w in rank_words) else 1,
                             len(z[0]), z[0]))
    return hits[0][1], hits


def coefficient_map(block: Any):
    """Decode documented mpc_orb COM/KEP coefficient arrays.

    MPC's current public schema stores orbital coordinates as parallel
    coefficient_names / coefficient_values arrays.  This is a schema adapter
    only; it does not alter the frozen scientific screen.
    """
    if not isinstance(block, dict):
        return {}, {}
    names = block.get('coefficient_names') or []
    values = block.get('coefficient_values') or []
    uncs = block.get('coefficient_uncertainties') or []
    vals = {}
    uncmap = {}
    for j, name in enumerate(names):
        key = norm_key(name)
        if j < len(values):
            x = numeric(values[j])
            if x is not None:
                vals[key] = x
        if j < len(uncs):
            u = numeric(uncs[j])
            if u is not None:
                uncmap[key] = u
    return vals, uncmap


def first_coeff(maps, aliases):
    for label, values in maps:
        for alias in aliases:
            k = norm_key(alias)
            if k in values:
                return values[k], f'{label}.coefficient_values[{k}]'
    return None, None


def orbit_for(desig: str):
    raw = req(ORB_API, {'desig': desig})
    try:
        orb = raw[0]['mpc_orb'][0]
    except Exception as exc:
        raise RuntimeError(f'no mpc_orb for {desig}: {raw!r}') from exc

    kep, kep_unc = coefficient_map(orb.get('KEP'))
    com, com_unc = coefficient_map(orb.get('COM'))
    maps = [('KEP', kep), ('COM', com)]

    a, ap = first_coeff(maps, ['a', 'semimajor_axis', 'semimajoraxis'])
    e, ep = first_coeff(maps, ['e', 'eccentricity'])
    inc, ip = first_coeff(maps, ['i', 'inclination'])
    q, qp = first_coeff(maps, ['q', 'perihelion_distance', 'periheliondistance'])

    # Documented COM commonly provides q/e rather than a; derive a exactly
    # from q/(1-e).  Conversely derive q from a/e when KEP is available.
    if a is None and q is not None and e is not None and e < 1.0:
        a = q / (1.0 - e)
        ap = 'derived q/(1-e)'
    if q is None and a is not None and e is not None:
        q = a * (1.0 - e)
        qp = 'derived a*(1-e)'

    # Retain old scalar-key parser only as a backwards-compatible fallback.
    if a is None:
        a, ah = extract_by_alias(orb, ['a', 'semimajor_axis', 'semimajoraxis'])
        if a is not None: ap = ah[0][0]
    if e is None:
        e, eh = extract_by_alias(orb, ['e', 'eccentricity'])
        if e is not None: ep = eh[0][0]
    if inc is None:
        inc, ih = extract_by_alias(orb, ['i', 'inclination'])
        if inc is not None: ip = ih[0][0]
    if q is None:
        q, qh = extract_by_alias(orb, ['q', 'perihelion_distance', 'periheliondistance'])
        if q is not None: qp = qh[0][0]
    if a is None and q is not None and e is not None and e < 1.0:
        a = q / (1.0 - e); ap = 'derived q/(1-e)'
    if q is None and a is not None and e is not None:
        q = a * (1.0 - e); qp = 'derived a*(1-e)'

    if a is None or e is None or inc is None or q is None:
        return {
            'desig': desig, 'status': 'UNPARSED_ORBIT',
            'raw_top_keys': sorted(orb.keys()),
            'structured_blocks': {
                'KEP_names': list((orb.get('KEP') or {}).get('coefficient_names') or []),
                'COM_names': list((orb.get('COM') or {}).get('coefficient_names') or []),
            },
        }
    return {
        'desig': desig, 'status': 'OK', 'a_au': a, 'e': e,
        'i_deg': inc, 'q_au': q,
        'parse_paths': {'a': ap, 'e': ep, 'i': ip, 'q': qp},
        'coefficient_uncertainties_if_supplied': {
            'KEP': kep_unc, 'COM': com_unc,
        },
    }


def classes(o):
    if o.get('status') != 'OK':
        return []
    a, q, i = o['a_au'], o['q_au'], o['i_deg']
    out = []
    if q >= 40.0 and a >= 150.0:
        out.append('A_detached_extreme')
    if q >= 30.0 and a >= 250.0:
        out.append('B_very_large_a')
    if q >= 30.0 and i >= 60.0:
        out.append('C_high_inclination')
    return out


def list_year(year: int):
    data = req(LIST_API, {'list': 'tnos', 'limit': 50000, 'like': f'{year}%'})
    return [x['unpacked_primary_provisional_designation'] for x in data.get('items', [])
            if x.get('unpacked_primary_provisional_designation')]


def earliest_observation(desig: str):
    raw = req(OBS_API, {'desigs': [desig], 'output_format': ['ADES_DF']})
    rows = raw[0].get('ADES_DF', []) if raw else []
    if not rows:
        return {'status': 'NO_OBSERVATIONS'}

    def key(r):
        for k in ('obsTime', 'obstime', 'obs_time'):
            if r.get(k): return str(r[k])
        for k in ('jd', 'mjd'):
            if r.get(k) is not None: return str(r[k])
        return '9999'
    rows = sorted(rows, key=key)
    first = rows[0]
    stations = [str(r.get('stn') or r.get('observatory_code') or r.get('obsCode') or '') for r in rows]
    return {
        'status': 'OK',
        'n_observations': len(rows),
        'first_time': key(first),
        'first_station': str(first.get('stn') or first.get('observatory_code') or first.get('obsCode') or ''),
        'stations': sorted(set(stations)),
        'x05_observation_count': sum(s == 'X05' for s in stations),
    }


def main():
    designations = sorted(set(list_year(2025) + list_year(2026)))
    parsed = []
    survivors = []
    for j, desig in enumerate(designations, 1):
        print(f'ORBIT {j}/{len(designations)} {desig}', flush=True)
        o = orbit_for(desig)
        o['screen_classes'] = classes(o)
        parsed.append(o)
        if o['screen_classes']:
            prov = earliest_observation(desig)
            o2 = dict(o)
            o2['observation_provenance'] = prov
            o2['rubin_discovery_provenance_pass'] = prov.get('first_station') == 'X05'
            survivors.append(o2)

    rubin = [x for x in survivors if x['rubin_discovery_provenance_pass']]
    report = {
        'screen_frozen_before_candidate_values': True,
        'screen': SCREEN,
        'candidate_years': [2025, 2026],
        'tnos_considered_n': len(designations),
        'orbits_parsed_n': sum(x.get('status') == 'OK' for x in parsed),
        'unparsed_n': sum(x.get('status') != 'OK' for x in parsed),
        'all_screen_survivors_n': len(survivors),
        'rubin_first_observation_survivors_n': len(rubin),
        'rubin_first_observation_survivors': rubin,
        'all_screen_survivors': survivors,
        'unparsed': [x for x in parsed if x.get('status') != 'OK'],
        'guardrail': ('Screen survivors are hypotheses only. Do not claim novelty or dynamical stability '
                      'without designation-specific literature/MPC collision review and covariance-aware integration.'),
    }
    (OUT/'report.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({
        'tnos_considered_n': report['tnos_considered_n'],
        'orbits_parsed_n': report['orbits_parsed_n'],
        'unparsed_n': report['unparsed_n'],
        'all_screen_survivors_n': report['all_screen_survivors_n'],
        'rubin_first_observation_survivors_n': report['rubin_first_observation_survivors_n'],
        'rubin_first_observation_survivors': rubin,
    }, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
