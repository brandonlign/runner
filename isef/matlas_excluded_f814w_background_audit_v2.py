#!/usr/bin/env python3
"""Product-format repair wrapper for excluded F814W control audit.

The previous audit correctly resolved MATLAS-1177 from proposal metadata but
stopped because that excluded field has no HAP-prefixed `hst_*` DRC product.
This wrapper keeps the exact frozen excluded targets/filter and allows any
calibrated DRC product attached to the exact F814W observation. HAP products
are preferred when present; otherwise the native association DRC is used.
No published-74 target is queried or opened.
"""
import numpy as np
from astroquery.mast import Observations
import matlas_excluded_f814w_background_audit as p


def choose_product_v2(target):
    rows=[]
    for program in p.PROGRAMS:
        allobs=Observations.query_criteria(obs_collection='HST',proposal_id=program,
            instrument_name='ACS/WFC')
        if not len(allobs):continue
        mask=np.array([(str(r['target_name'])==target and str(r['filters']).upper()=='F814W') for r in allobs],bool)
        obs=allobs[mask]
        if not len(obs):continue
        for r in obs:
            literal=str(r['target_name'])
            if literal in p.PUBLISHED or literal=='MATLAS2019':
                raise RuntimeError(f'BARRIER BREACH target={literal}')
        prod=Observations.get_product_list(obs)
        for r in prod:
            fn=str(r['productFilename']) if 'productFilename' in prod.colnames else ''
            sub=str(r['productSubGroupDescription']) if 'productSubGroupDescription' in prod.colnames else ''
            if sub.upper()!='DRC' or not fn.endswith('_drc.fits') or 'skycell' in fn:continue
            rows.append({'program':program,'filename':fn,'dataURI':str(r['dataURI']),
                'size':int(r['size']) if 'size' in prod.colnames and r['size'] is not None else None})
    if not rows:raise RuntimeError(f'No calibrated F814W DRC for excluded control {target}')
    # Prefer a filter-explicit HAP association when available. Otherwise use
    # the shortest native DRC attached to this already exact F814W observation.
    rows.sort(key=lambda r:(0 if (r['filename'].startswith('hst_') and '_acs_wfc_f814w_' in r['filename']) else 1,
                            len(r['filename']),r['filename']))
    return rows[0],rows

if __name__=='__main__':
    p.choose_product=choose_product_v2
    p.main()
