#!/usr/bin/env python3
"""Freeze the exact published 74-galaxy MATLAS HST sample using metadata only.

The science sample is the 74 names in Marleau et al. 2024 Table A.1, not the
union of every target present in the HST proposal IDs. MAST contains additional
proposal targets and spells MATLAS-2019 as MATLAS2019; neither fact changes the
published sample.

No science image is downloaded or decoded here. A deterministic 50/24 split is
created by SHA-256 ordering of canonical target names before any MATLAS target
pixel is opened. The 24-object set is a replication holdout, not a rescue set.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from astroquery.mast import Observations

OUT = Path('results/matlas_hst_sample_manifest_metadata')
OUT.mkdir(parents=True, exist_ok=True)
PROGRAMS = ('16257','16711','16082')

PUBLISHED_74 = """
MATLAS-42 MATLAS-49 MATLAS-138 MATLAS-141 MATLAS-149 MATLAS-177 MATLAS-203 MATLAS-207 MATLAS-262 MATLAS-290
MATLAS-342 MATLAS-347 MATLAS-365 MATLAS-368 MATLAS-401 MATLAS-405 MATLAS-478 MATLAS-524 MATLAS-585 MATLAS-627
MATLAS-658 MATLAS-682 MATLAS-787 MATLAS-791 MATLAS-799 MATLAS-898 MATLAS-976 MATLAS-984 MATLAS-987 MATLAS-1059
MATLAS-1154 MATLAS-1174 MATLAS-1216 MATLAS-1225 MATLAS-1262 MATLAS-1302 MATLAS-1321 MATLAS-1332 MATLAS-1400 MATLAS-1408
MATLAS-1412 MATLAS-1413 MATLAS-1437 MATLAS-1470 MATLAS-1485 MATLAS-1530 MATLAS-1534 MATLAS-1539 MATLAS-1545 MATLAS-1550
MATLAS-1558 MATLAS-1577 MATLAS-1589 MATLAS-1616 MATLAS-1618 MATLAS-1630 MATLAS-1647 MATLAS-1662 MATLAS-1667 MATLAS-1740
MATLAS-1779 MATLAS-1794 MATLAS-1801 MATLAS-1865 MATLAS-1888 MATLAS-1907 MATLAS-1938 MATLAS-1975 MATLAS-1985 MATLAS-2019
MATLAS-2021 MATLAS-2069 MATLAS-2176 MATLAS-2184
""".split()
assert len(PUBLISHED_74) == 74 and len(set(PUBLISHED_74)) == 74

ALIASES = {'MATLAS-2019': 'MATLAS2019'}


def sval(x):
    try:
        if hasattr(x,'item'): x=x.item()
    except Exception: pass
    if x is None: return None
    return str(x)


def query_all():
    obs=[]; products=[]
    for program in PROGRAMS:
        t=Observations.query_criteria(obs_collection='HST', proposal_id=program, instrument_name='ACS/WFC')
        for r in t:
            obs.append({
                'program':program,
                'obsid':sval(r['obsid']) if 'obsid' in t.colnames else None,
                'obs_id':sval(r['obs_id']) if 'obs_id' in t.colnames else None,
                'target_name':sval(r['target_name']) if 'target_name' in t.colnames else None,
                'filter':sval(r['filters']) if 'filters' in t.colnames else None,
                't_exptime':float(r['t_exptime']) if 't_exptime' in t.colnames and r['t_exptime'] is not None else None,
                'data_rights':sval(r['dataRights']) if 'dataRights' in t.colnames else None,
                's_ra':float(r['s_ra']) if 's_ra' in t.colnames and r['s_ra'] is not None else None,
                's_dec':float(r['s_dec']) if 's_dec' in t.colnames and r['s_dec'] is not None else None,
            })
        p=Observations.get_product_list(t)
        for r in p:
            products.append({
                'program':program,
                'obsID':sval(r['obsID']) if 'obsID' in p.colnames else None,
                'productFilename':sval(r['productFilename']) if 'productFilename' in p.colnames else None,
                'productSubGroupDescription':sval(r['productSubGroupDescription']) if 'productSubGroupDescription' in p.colnames else None,
                'dataURI':sval(r['dataURI']) if 'dataURI' in p.colnames else None,
                'dataRights':sval(r['dataRights']) if 'dataRights' in p.colnames else None,
            })
    return obs,products


def main():
    obs,products=query_all()
    p_by_obs=defaultdict(list)
    for p in products:
        if (p.get('productSubGroupDescription') or '').upper() == 'DRC':
            p_by_obs[p.get('obsID')].append(p)

    rows=[]
    missing=[]
    for canonical in PUBLISHED_74:
        mast_name=ALIASES.get(canonical,canonical)
        matched=[r for r in obs if r.get('target_name')==mast_name and r.get('filter') in ('F606W','F814W')]
        by_filter={f:[r for r in matched if r.get('filter')==f] for f in ('F606W','F814W')}
        if any(not by_filter[f] for f in by_filter):
            missing.append({'canonical':canonical,'mast_name':mast_name,'filters_found':sorted({r.get('filter') for r in matched})})
            continue
        for f in ('F606W','F814W'):
            rs=by_filter[f]
            drc={}
            for r in rs:
                for p in p_by_obs.get(r.get('obsid'),[]):
                    fn=p.get('productFilename')
                    if fn: drc[fn]=p
            rows.append({
                'canonical_name':canonical,
                'mast_target_name':mast_name,
                'programs':';'.join(sorted({r['program'] for r in rs})),
                'filter':f,
                'mast_observation_rows_n':len(rs),
                'mast_t_exptime_values_s':';'.join(str(x) for x in sorted({r['t_exptime'] for r in rs if r['t_exptime'] is not None})),
                'mast_obsids':';'.join(sorted({str(r['obsid']) for r in rs if r['obsid']})),
                'drc_product_filenames':';'.join(sorted(drc)),
                'drc_product_count':len(drc),
                'data_rights':';'.join(sorted({str(r['data_rights']) for r in rs if r['data_rights']})),
                'metadata_ra_deg':next((r['s_ra'] for r in rs if r['s_ra'] is not None),None),
                'metadata_dec_deg':next((r['s_dec'] for r in rs if r['s_dec'] is not None),None),
            })

    # Stable outcome-independent split: rank by SHA256(canonical name), first 50 primary.
    order=sorted(PUBLISHED_74,key=lambda n:(hashlib.sha256(n.encode()).hexdigest(),n))
    primary=set(order[:50]); holdout=set(order[50:])
    for r in rows:
        r['split']='PRIMARY_50' if r['canonical_name'] in primary else 'REPLICATION_HOLDOUT_24'

    resolved=sorted({r['canonical_name'] for r in rows})
    drc_missing=[r for r in rows if r['drc_product_count']==0]
    report={
        'information_barrier':'MAST metadata only; zero MATLAS science-image bytes downloaded or decoded',
        'science_values_opened':False,
        'sample_source':'Marleau et al. 2024 Table A.1 exact 74 names',
        'published_sample_n':74,
        'resolved_sample_n':len(resolved),
        'missing_targets':missing,
        'drc_missing_rows':drc_missing,
        'primary_n':len(primary),
        'replication_holdout_n':len(holdout),
        'split_rule':'sort exact 74 canonical names by SHA256(name), first 50 PRIMARY_50, remaining 24 REPLICATION_HOLDOUT_24',
        'primary_names':sorted(primary),
        'replication_holdout_names':sorted(holdout),
        'archive_extra_target_names':sorted(set(r['target_name'] for r in obs if r.get('target_name')) - {ALIASES.get(n,n) for n in PUBLISHED_74}),
        'rows':rows,
        'gate':'PASS' if len(resolved)==74 and not missing and not drc_missing and len(primary)==50 and len(holdout)==24 else 'FAIL',
    }
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    with (OUT/'manifest.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    print(json.dumps({k:report[k] for k in ('gate','resolved_sample_n','primary_n','replication_holdout_n','missing_targets','drc_missing_rows','archive_extra_target_names')},indent=2,sort_keys=True))
    raise SystemExit(0 if report['gate']=='PASS' else 3)

if __name__=='__main__':main()
