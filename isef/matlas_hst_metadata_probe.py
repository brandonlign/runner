#!/usr/bin/env python3
"""Target-blind MAST metadata probe for the MATLAS 74-UDG HST stream lead.

This stage must not download or open any MATLAS science image. It inventories
only MAST observation/product metadata for the three published MATLAS HST
programs and the external Oyashio positive-control program.

MATLAS programs from Marleau et al. (2024): GO-16257, GO-16711, GO-16082.
Oyashio external positive control: GO-16890.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from astroquery.mast import Observations

OUT = Path('results/matlas_hst_metadata_probe')
OUT.mkdir(parents=True, exist_ok=True)
MATLAS_PROGRAMS = ('16257', '16711', '16082')
OYASHIO_PROGRAM = '16890'


def scalar(x):
    try:
        if hasattr(x, 'item'):
            x = x.item()
    except Exception:
        pass
    if x is None:
        return None
    if isinstance(x, (str, int, float, bool)):
        return x
    return str(x)


def rows_to_dicts(tab, keep):
    rows = []
    for r in tab:
        d = {}
        for k in keep:
            if k in tab.colnames:
                try:
                    d[k] = scalar(r[k])
                except Exception:
                    d[k] = None
        rows.append(d)
    return rows


def query_program(program):
    tab = Observations.query_criteria(
        obs_collection='HST',
        proposal_id=str(program),
        instrument_name='ACS/WFC',
    )
    keep = [
        'obs_id','obsid','proposal_id','target_name','filters','t_exptime',
        't_min','t_max','s_ra','s_dec','calib_level','dataRights','intentType',
        'dataproduct_type','instrument_name','obs_collection'
    ]
    rows = rows_to_dicts(tab, keep)

    # Product metadata only. No download call is permitted in this script.
    products = Observations.get_product_list(tab) if len(tab) else None
    prod_keep = [
        'obsID','obs_id','productFilename','productType','productSubGroupDescription',
        'calib_level','size','dataURI','dataRights','description'
    ]
    prows = rows_to_dicts(products, prod_keep) if products is not None else []

    return rows, prows


def summarize(program, rows, products):
    targets = sorted({str(r.get('target_name')) for r in rows if r.get('target_name') not in (None, '')})
    filters = Counter(str(r.get('filters')) for r in rows if r.get('filters') not in (None, ''))
    exp_by_target_filter = defaultdict(float)
    nobs_by_target_filter = Counter()
    for r in rows:
        t = str(r.get('target_name'))
        f = str(r.get('filters'))
        try:
            ex = float(r.get('t_exptime'))
        except Exception:
            ex = 0.0
        if t and f and t != 'None' and f != 'None':
            exp_by_target_filter[f'{t}|{f}'] += ex
            nobs_by_target_filter[f'{t}|{f}'] += 1

    drc = [p for p in products if str(p.get('productSubGroupDescription','')).upper() == 'DRC']
    drz = [p for p in products if str(p.get('productSubGroupDescription','')).upper() == 'DRZ']
    return {
        'program': str(program),
        'observation_rows_n': len(rows),
        'unique_targets_n': len(targets),
        'unique_targets': targets,
        'filter_row_counts': dict(sorted(filters.items())),
        'exposure_seconds_by_target_filter': dict(sorted(exp_by_target_filter.items())),
        'observation_rows_by_target_filter': dict(sorted(nobs_by_target_filter.items())),
        'product_rows_n': len(products),
        'drc_product_rows_n': len(drc),
        'drz_product_rows_n': len(drz),
        'drc_product_filenames': sorted({str(p.get('productFilename')) for p in drc if p.get('productFilename')}),
        'data_rights': sorted({str(r.get('dataRights')) for r in rows if r.get('dataRights') not in (None,'')}),
    }


def main():
    report = {
        'information_barrier': (
            'MAST observation/product metadata only. No MATLAS or Oyashio science '
            'image bytes downloaded or decoded in this stage.'
        ),
        'science_values_opened': False,
        'matlas_programs': list(MATLAS_PROGRAMS),
        'oyashio_positive_control_program': OYASHIO_PROGRAM,
        'programs': {},
    }

    all_matlas_targets = set()
    for program in MATLAS_PROGRAMS + (OYASHIO_PROGRAM,):
        rows, products = query_program(program)
        s = summarize(program, rows, products)
        report['programs'][program] = s
        if program in MATLAS_PROGRAMS:
            all_matlas_targets.update(s['unique_targets'])

    report['matlas_all_program_unique_targets_n'] = len(all_matlas_targets)
    report['matlas_all_program_unique_targets'] = sorted(all_matlas_targets)
    report['published_expected_matlas_sample_n'] = 74
    report['target_count_matches_published_74'] = len(all_matlas_targets) == 74

    # Published exposure design is two 412 s dithers per filter. MAST may expose
    # association rows rather than raw exposure rows, so report metadata rather
    # than forcing a pass/fail from a particular row representation.
    (OUT/'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'science_values_opened': False,
        'matlas_all_program_unique_targets_n': report['matlas_all_program_unique_targets_n'],
        'target_count_matches_published_74': report['target_count_matches_published_74'],
        'per_program': {
            p: {
                'unique_targets_n': report['programs'][p]['unique_targets_n'],
                'observation_rows_n': report['programs'][p]['observation_rows_n'],
                'drc_product_rows_n': report['programs'][p]['drc_product_rows_n'],
                'filters': report['programs'][p]['filter_row_counts'],
            } for p in report['programs']
        },
    }, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
