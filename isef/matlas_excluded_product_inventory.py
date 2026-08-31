#!/usr/bin/env python3
"""Metadata-only product inventory for the 13 excluded MATLAS proposal fields.
No FITS bytes are downloaded. Published Table-A.1 targets are never selected.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
import numpy as np
from astroquery.mast import Observations
from matlas_excluded_f814w_background_audit import PROGRAMS,EXCLUDED,PUBLISHED

OUT=Path('results/matlas_excluded_product_inventory');OUT.mkdir(parents=True,exist_ok=True)

def main():
    rep={'science_values_opened':False,'targets':[]}
    for target in EXCLUDED:
        products=[]; obsrows=[]
        for program in PROGRAMS:
            allobs=Observations.query_criteria(obs_collection='HST',proposal_id=program,instrument_name='ACS/WFC')
            if not len(allobs):continue
            mask=np.array([(str(r['target_name'])==target and str(r['filters']).upper()=='F814W') for r in allobs],bool)
            obs=allobs[mask]
            if not len(obs):continue
            for r in obs:
                if str(r['target_name']) in PUBLISHED or str(r['target_name'])=='MATLAS2019':raise RuntimeError('barrier breach')
                obsrows.append({'program':program,'obsid':str(r['obsid']),'obs_id':str(r['obs_id']),
                    'target_name':str(r['target_name']),'filter':str(r['filters']),'t_exptime':float(r['t_exptime'])})
            p=Observations.get_product_list(obs)
            for r in p:
                products.append({'program':program,
                    'filename':str(r['productFilename']) if 'productFilename' in p.colnames else '',
                    'subgroup':str(r['productSubGroupDescription']) if 'productSubGroupDescription' in p.colnames else '',
                    'productType':str(r['productType']) if 'productType' in p.colnames else '',
                    'calib_level':str(r['calib_level']) if 'calib_level' in p.colnames else '',
                    'size':int(r['size']) if 'size' in p.colnames and r['size'] is not None else None})
        rep['targets'].append({'target':target,'observations':obsrows,'subgroup_counts':dict(Counter(x['subgroup'] for x in products)),
            'fits_products':[x for x in products if x['filename'].lower().endswith('.fits')]})
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({x['target']:x['subgroup_counts'] for x in rep['targets']},indent=2,sort_keys=True))
if __name__=='__main__':main()
