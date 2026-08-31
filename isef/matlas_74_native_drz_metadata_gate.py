#!/usr/bin/env python3
"""Metadata-only gate: exact published 74 must each have one native F814W DRZ.

No FITS is downloaded. This establishes a uniform archive representation shared
with all 13 prospectively excluded control fields before any published-74 pixel
is opened.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from astroquery.mast import Observations
from matlas_hst_sample_manifest_metadata import PUBLISHED_74,ALIASES,PROGRAMS

OUT=Path('results/matlas_74_native_drz_metadata_gate');OUT.mkdir(parents=True,exist_ok=True)

def main():
    rows=[]
    for canonical in PUBLISHED_74:
        name=ALIASES.get(canonical,canonical); matches=[]
        for program in PROGRAMS:
            allobs=Observations.query_criteria(obs_collection='HST',proposal_id=program,instrument_name='ACS/WFC')
            mask=np.array([(str(r['target_name'])==name and str(r['filters']).upper()=='F814W') for r in allobs],bool)
            obs=allobs[mask]
            if not len(obs):continue
            p=Observations.get_product_list(obs)
            for r in p:
                fn=str(r['productFilename']) if 'productFilename' in p.colnames else ''
                sub=str(r['productSubGroupDescription']) if 'productSubGroupDescription' in p.colnames else ''
                # Native association DRZ roots are short instrument roots, not HAP hst_* products.
                if sub.upper()=='DRZ' and fn.endswith('_drz.fits') and not fn.startswith('hst_') and 'skycell' not in fn:
                    matches.append({'program':program,'filename':fn,'dataURI':str(r['dataURI']),
                        'size':int(r['size']) if 'size' in p.colnames and r['size'] is not None else None})
        uniq={m['filename']:m for m in matches}
        rows.append({'canonical_name':canonical,'mast_target_name':name,'native_f814w_drz_n':len(uniq),
                     'native_f814w_drz':sorted(uniq.values(),key=lambda x:x['filename'])})
    bad=[r for r in rows if r['native_f814w_drz_n']!=1]
    rep={'information_barrier':'MAST product metadata only; no published-74 FITS bytes downloaded or decoded',
         'science_values_opened':False,'sample_n':74,'exactly_one_native_f814w_drz_n':sum(r['native_f814w_drz_n']==1 for r in rows),
         'bad':bad,'rows':rows,'gate':'PASS' if not bad else 'FAIL'}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'gate':rep['gate'],'sample_n':74,'exactly_one_native_f814w_drz_n':rep['exactly_one_native_f814w_drz_n'],'bad':bad},indent=2,sort_keys=True))
    raise SystemExit(0 if not bad else 3)
if __name__=='__main__':main()
