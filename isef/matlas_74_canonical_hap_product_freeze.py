#!/usr/bin/env python3
"""Freeze exact HAP/DRC files for the sealed 74-galaxy MATLAS experiment.

Metadata only: no FITS byte is downloaded or decoded.

Primary discovery representation:
- F814W only;
- for a target with multiple observation epochs/programs, choose the earliest
  observation by MAST t_min (ties: program, obsid);
- within that chosen observation, choose the shortest HAP non-skycell DRC root
  matching ACS/WFC + filter (ties lexicographic).

F606W is frozen by the same rule but is secondary confirmation only and cannot
create/rescue a primary candidate. Any later repeat observation is replication
only and cannot be coadded into discovery.
"""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import numpy as np
from astroquery.mast import Observations
from matlas_hst_sample_manifest_metadata import PUBLISHED_74,ALIASES,PROGRAMS

OUT=Path('results/matlas_74_canonical_hap_product_freeze');OUT.mkdir(parents=True,exist_ok=True)
FILTERS=('F814W','F606W')

def safe(x):
    try:
        if hasattr(x,'item'):x=x.item()
    except Exception:pass
    if x is None:return None
    return str(x)

def all_observations():
    by_program={}
    for program in PROGRAMS:
        by_program[program]=Observations.query_criteria(obs_collection='HST',proposal_id=program,instrument_name='ACS/WFC')
    return by_program

def exact_obs(rows,target,filt):
    out=[]
    for program,t in rows.items():
        for r in t:
            if str(r['target_name'])!=target or str(r['filters']).upper()!=filt:continue
            out.append({'program':program,'obsid':safe(r['obsid']) if 'obsid' in t.colnames else None,
                        'obs_id':safe(r['obs_id']) if 'obs_id' in t.colnames else None,
                        't_min':float(r['t_min']) if 't_min' in t.colnames and r['t_min'] is not None else float('inf'),
                        't_exptime':float(r['t_exptime']) if 't_exptime' in t.colnames and r['t_exptime'] is not None else None,
                        '_row':r})
    return out

def products_for_obs(obsmeta,program_table,filt):
    # Rebuild a one-row table by exact obsid from the already-fetched program metadata.
    t=program_table
    mask=np.array([safe(r['obsid'])==obsmeta['obsid'] for r in t],bool)
    one=t[mask]
    if not len(one):raise RuntimeError(f"Cannot recover obsid {obsmeta['obsid']}")
    p=Observations.get_product_list(one)
    rows=[]
    for r in p:
        fn=str(r['productFilename']) if 'productFilename' in p.colnames else ''
        sub=str(r['productSubGroupDescription']) if 'productSubGroupDescription' in p.colnames else ''
        uri=str(r['dataURI']) if 'dataURI' in p.colnames else ''
        size=int(r['size']) if 'size' in p.colnames and r['size'] is not None else None
        # HAP association DRC only; exact filter encoded in filename. Exclude skycell products.
        if sub.upper()!='DRC' or not fn.endswith('_drc.fits') or not fn.startswith('hst_') or 'skycell' in fn:continue
        if f'_acs_wfc_{filt.lower()}_' not in fn.lower():continue
        rows.append({'filename':fn,'dataURI':uri,'size':size})
    uniq={x['filename']:x for x in rows}
    return sorted(uniq.values(),key=lambda x:(len(x['filename']),x['filename']))

def main():
    tabs=all_observations()
    order=sorted(PUBLISHED_74,key=lambda n:(hashlib.sha256(n.encode()).hexdigest(),n));primary=set(order[:50]);hold=set(order[50:])
    rows=[];fail=[]
    for canonical in PUBLISHED_74:
        target=ALIASES.get(canonical,canonical)
        for filt in FILTERS:
            obs=exact_obs(tabs,target,filt)
            if not obs:
                fail.append({'canonical':canonical,'filter':filt,'reason':'NO_OBSERVATION'});continue
            obs_sorted=sorted(obs,key=lambda x:(x['t_min'],x['program'],x['obsid'] or ''))
            chosen_obs=obs_sorted[0]
            products=products_for_obs(chosen_obs,tabs[chosen_obs['program']],filt)
            if not products:
                fail.append({'canonical':canonical,'filter':filt,'reason':'NO_HAP_DRC','chosen_obs':{k:v for k,v in chosen_obs.items() if k!='_row'}});continue
            chosen=products[0]
            later=[]
            for z in obs_sorted[1:]:
                pp=products_for_obs(z,tabs[z['program']],filt)
                later.append({'program':z['program'],'obsid':z['obsid'],'t_min':z['t_min'],'t_exptime':z['t_exptime'],
                              'hap_drc_candidates':pp})
            rows.append({'canonical_name':canonical,'mast_target_name':target,'split':'PRIMARY_50' if canonical in primary else 'REPLICATION_HOLDOUT_24',
                         'filter':filt,'role':'PRIMARY_DISCOVERY' if filt=='F814W' else 'SECONDARY_CONFIRMATION_ONLY',
                         'chosen_program':chosen_obs['program'],'chosen_obsid':chosen_obs['obsid'],'chosen_t_min_mjd':chosen_obs['t_min'],
                         'chosen_t_exptime_s':chosen_obs['t_exptime'],'chosen_filename':chosen['filename'],'chosen_dataURI':chosen['dataURI'],
                         'chosen_size_bytes':chosen['size'],'chosen_observation_hap_drc_candidates':' ; '.join(x['filename'] for x in products),
                         'later_repeat_observation_count':len(later),'later_repeats_json':json.dumps(later,sort_keys=True)})
    f814=[r for r in rows if r['filter']=='F814W'];f606=[r for r in rows if r['filter']=='F606W']
    rep={'information_barrier':'MAST metadata/product tables only; zero published-74 FITS bytes downloaded or decoded',
         'science_values_opened':False,'selection_rule':'earliest exact target/filter observation by t_min, then shortest non-skycell HAP ACS/WFC DRC filename; tie lexicographic',
         'discovery_filter':'F814W','secondary_filter':'F606W confirmation only','later_repeat_rule':'replication only; never coadd into discovery or use for candidate creation',
         'sample_n':74,'primary_n':50,'holdout_n':24,'f814_frozen_n':len(f814),'f606_frozen_n':len(f606),'failures':fail,
         'rows':rows,'gate':'PASS' if len(f814)==74 and len(f606)==74 and not fail else 'FAIL'}
    (OUT/'manifest.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    if rows:
        with (OUT/'manifest.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    print(json.dumps({'gate':rep['gate'],'f814_frozen_n':len(f814),'f606_frozen_n':len(f606),'failures':fail,
                      'f814_repeat_targets':[r['canonical_name'] for r in f814 if r['later_repeat_observation_count']>0]},indent=2,sort_keys=True))
    raise SystemExit(0 if rep['gate']=='PASS' else 3)
if __name__=='__main__':main()
