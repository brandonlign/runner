#!/usr/bin/env python3
"""Robustness audit for asteroid 12523, surfaced by the failed Stage-1 null gate.

This is candidate follow-up, not a change to the null gate. It opens only the
historical public TSSYS-DR1 12523 products and JPL metadata; no Year-8 TESS
science value is accessed.
"""
from __future__ import annotations
import hashlib,json,math,io
from pathlib import Path
import numpy as np,requests
import tess_binary_stage0_detector as s0
import tess_binary_stage1_detector as s1

OUT=Path('results/tess_binary_12523_candidate_audit');OUT.mkdir(parents=True,exist_ok=True)
LC='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/12523.lc'
SPEC='https://archive.konkoly.hu/pub/tssys/dr1/lightcurves_spectra/12523.f'
MERGE='https://archive.konkoly.hu/pub/tssys/dr1/release.merge'

def clean(x):
    if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
    if isinstance(x,(int,np.integer)):return int(x)
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    return x

def robust_effect(a,b):
    # median(a)-median(b) in units of robust sigma of b
    a=np.asarray(a,float);b=np.asarray(b,float);sb=s0.robust_sigma(b)
    return float((np.nanmedian(a)-np.nanmedian(b))/sb) if np.isfinite(sb) and sb>0 else None

def fixed_event_mask(t,z):
    b=z['final_bls'];sel=z['selected_interpretation'];D=b['duration_d'];T0=b['transit_time'];P=sel['orbital_period_d']
    ph=((t-T0+0.5*P)%P)-0.5*P
    if sel['name']=='H2_ALTERNATING_TWO_EVENT':
        return (np.abs(ph)<=D/2)|(np.abs(np.abs(ph)-P/2)<=D/2)
    return np.abs(ph)<=D/2

def run_subset(a,mask):
    q=a[mask]
    return s1.detect(q[:,1],q[:,4],q[:,5],q[:,9].astype(int))

def main():
    r=requests.get(LC,timeout=120,headers={'User-Agent':'ISEF-12523-audit/1.0'});r.raise_for_status();a=np.loadtxt(io.BytesIO(r.content))
    full=s1.detect(a[:,1],a[:,4],a[:,5],a[:,9].astype(int))
    good=np.isfinite(a[:,1])&np.isfinite(a[:,4])&np.isfinite(a[:,5])&(a[:,5]>0)&(a[:,9].astype(int)==0)
    ag=a[good];t=ag[:,1];order=np.argsort(t);ag=ag[order];t=ag[:,1]
    # Independent time partitions defined without candidate phase.
    med=np.median(t);halves={'early':t<=med,'late':t>med}
    halfres={k:run_subset(ag,m) for k,m in halves.items()}
    qedges=np.quantile(t,[0,.25,.5,.75,1.0]);
    # Fixed full-data ephemeris diagnostic by time quartile; not a discovery test.
    em=fixed_event_mask(t,full);quart=[]
    for j in range(4):
        qm=(t>=qedges[j])&(t<qedges[j+1] if j<3 else t<=qedges[j+1]);ein=qm&em;eout=qm&~em
        quart.append({'quarter':j+1,'n':int(qm.sum()),'event_n_cadences':int(ein.sum()),'non_event_n':int(eout.sum()),
          'event_minus_non_event_mag':float(np.median(ag[ein,4])-np.median(ag[eout,4])) if ein.any() and eout.any() else None,
          'event_effect_sigma':robust_effect(ag[ein,4],ag[eout,4]) if ein.any() and eout.any() else None})
    # Instrument/background covariates under the fixed event mask.
    cov={}
    for col,name in [(2,'x_ccd'),(3,'y_ccd'),(6,'background'),(7,'background_rms'),(10,'tess_distance_au'),(11,'sun_distance_au'),(12,'phase_angle_deg')]:
        cov[name]={'event_median':float(np.median(ag[em,col])),'non_event_median':float(np.median(ag[~em,col])),
                   'event_minus_non_event_robust_sigma':robust_effect(ag[em,col],ag[~em,col])}
    # TSSYS published residual spectrum: rank candidate orbital and half-event frequencies.
    sr=requests.get(SPEC,timeout=120,headers={'User-Agent':'ISEF-12523-audit/1.0'});sr.raise_for_status();sp=np.loadtxt(io.BytesIO(sr.content))
    sel=full['selected_interpretation'];Porb=sel['orbital_period_d'];P0=full['final_bls']['period_d']
    specdiag={}
    for name,f in [('full_orbit_cpd',1/Porb),('half_event_cpd',1/P0)]:
        i=int(np.argmin(np.abs(sp[:,0]-f)));val=float(sp[i,1]);rank=int(1+np.sum(sp[:,1]>val));specdiag[name]={'target_frequency_cpd':float(f),'nearest_frequency_cpd':float(sp[i,0]),'residual_mag':val,'descending_rank':rank,'spectrum_n':int(len(sp)),'percentile':float(np.mean(sp[:,1]<=val))}
    # Metadata row from TSSYS merge and current JPL SBDB identity/rotation metadata.
    mr=requests.get(MERGE,timeout=120,headers={'User-Agent':'ISEF-12523-audit/1.0'});mr.raise_for_status();mline=None
    for line in mr.text.splitlines():
        if line.split() and line.split()[0]=='12523':mline=line;break
    jr=requests.get('https://ssd-api.jpl.nasa.gov/sbdb.api',params={'sstr':'12523','phys-par':'true','sat':'true'},timeout=120);jr.raise_for_status();jpl=jr.json()
    rep={'role':'post-null-gate candidate robustness audit; Stage-1 null gate remains failed','target':'(12523) 1998 HH100','year8_values_opened':False,
      'lc_sha256':hashlib.sha256(r.content).hexdigest(),'spectrum_sha256':hashlib.sha256(sr.content).hexdigest(),'full_stage1':full,
      'time_halves_stage1':halfres,'fixed_ephemeris_quarters':quart,'fixed_event_instrument_covariates':cov,'published_residual_spectrum':specdiag,
      'tssys_release_merge_line':mline,'jpl_sbdb':jpl}
    (OUT/'report.json').write_text(json.dumps(clean(rep),indent=2,sort_keys=True,allow_nan=False)+'\n')
    summary={'full':{'hard_pass':full.get('hard_pass'),'score':full.get('score'),'selected':full.get('selected_interpretation'),'bls':full.get('final_bls'),'masked_rotation':full.get('masked_rotation')},
      'halves':{k:{'hard_pass':v.get('hard_pass'),'score':v.get('score'),'selected':v.get('selected_interpretation'),'bls':v.get('final_bls')} for k,v in halfres.items()},
      'quarters':quart,'covariates':cov,'spectrum':specdiag,'merge_line':mline,
      'jpl_object':jpl.get('object'),'jpl_phys_par':jpl.get('phys_par')}
    print(json.dumps(clean(summary),indent=2,allow_nan=False))

if __name__=='__main__':main()
