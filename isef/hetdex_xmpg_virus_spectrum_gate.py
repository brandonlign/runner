#!/usr/bin/env python3
"""Frozen HPSC1 native-VIRUS lambda4363 positive-control gate.
Reads only five externally specified pre-2020 controls from HPSC1 spectra.
Never accesses HPSC2.
"""
from pathlib import Path
import json, math
import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.special import ndtr, ndtri
OUT=Path('results/hetdex_xmpg_virus_spectrum_gate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
URL='https://web.corral.tacc.utexas.edu/hetdex/HETDEX/catalogs/hetdex_source_catalog_1/hetdex_sc1_spec_v3.2.fits'
CONTROLS=[
 ('O3ELG2',8.2826,-0.1793),
 ('O3ELG4a',9.8204,-0.0121),
 ('O3ELG9',203.8739,51.0155),
 ('O3ELG11',176.0732,51.1047),
 ('O3ELG15',212.7970,51.2664),
]
TARGET=4363.21
PSEUDO=[4323.21,4343.21,4383.21,4403.21]
OFFSETS=np.arange(-3.0,3.01,1.0)
SIGMA=2.5

def corrected_sigma(snr):
    p=max(1e-300,1.0-float(ndtr(snr)))
    pc=min(1.0,7.0*p)
    return float(ndtri(1.0-pc)) if pc<0.5 else float(ndtri(max(1e-12,1.0-pc)))

def one_obs(wave,flux,err,z,rest,offset):
    cen=rest*(1.0+z)+offset
    finite=np.isfinite(wave)&np.isfinite(flux)&np.isfinite(err)&(err>0)
    if not np.isfinite(cen) or cen<wave[finite].min()+30 or cen>wave[finite].max()-30:return None
    dx=wave-cen
    side=finite&(np.abs(dx)>=8)&(np.abs(dx)<=24)
    core=finite&(np.abs(dx)<=8)
    if side.sum()<10 or core.sum()<5:return None
    X=np.column_stack([np.ones(side.sum()),wave[side]-cen]);ww=1.0/err[side]**2
    try:
        cov=np.linalg.inv(X.T@(ww[:,None]*X));beta=cov@(X.T@(ww*flux[side]))
    except np.linalg.LinAlgError:return None
    cont=beta[0]+beta[1]*(wave[core]-cen);y=flux[core]-cont;e=err[core]
    t=np.exp(-0.5*((wave[core]-cen)/SIGMA)**2)
    wt=1.0/e**2;den=np.sum(wt*t*t)
    if not np.isfinite(den) or den<=0:return None
    amp=float(np.sum(wt*t*y)/den);amp_err=float(den**-0.5)
    # integrated Gaussian flux density*Angstrom
    integ=amp*math.sqrt(2*math.pi)*SIGMA;integ_err=amp_err*math.sqrt(2*math.pi)*SIGMA
    return {'flux':integ,'flux_err':integ_err,'snr':integ/integ_err,'center':cen}

def combine_for_rest(rows,wave,spec,specerr,rest):
    byoff=[]
    for off in OFFSETS:
        ms=[]
        for idx,z in rows:
            m=one_obs(wave,np.asarray(spec[idx],float),np.asarray(specerr[idx],float),z,rest,float(off))
            if m is not None:ms.append(m)
        if not ms:continue
        w=np.array([1/m['flux_err']**2 for m in ms]);f=np.array([m['flux'] for m in ms])
        fc=float(np.sum(w*f)/np.sum(w));ec=float(np.sum(w)**-0.5);sn=fc/ec
        byoff.append({'offset_A':float(off),'combined_flux':fc,'combined_flux_err':ec,'snr':sn,'valid_observations':len(ms)})
    if not byoff:return {'technically_testable':False}
    best=max(byoff,key=lambda x:x['snr']);cs=corrected_sigma(best['snr'])
    return {'technically_testable':True,'best':best,'corrected_sigma':cs,'recovered':bool(cs>=3.0 and best['combined_flux']>0),'all_offsets':byoff}

def main():
    out={'success':False,'status':'FROZEN_HPSC1_CONTROL_GATE','hpsc2_opened':False,'controls':[],
         'freeze':{'target_rest_A':TARGET,'pseudo_rest_A':PSEUDO,'centroid_offsets_A':OFFSETS.tolist(),'gaussian_sigma_A':SIGMA,'corrected_sigma_threshold':3.0}}
    try:
        # fsspec-backed HTTP access permits range reads instead of downloading the 4.5 GB file.
        with fits.open(URL,use_fsspec=True,fsspec_kwargs={'block_size':4*1024*1024,'cache_type':'readahead'},memmap=False,lazy_load_hdus=True) as h:
            info=h['INFO'].data
            names=info.names
            ra=np.asarray(info['RA'],float);dec=np.asarray(info['DEC'],float);z=np.asarray(info['z_hetdex'],float)
            coords=SkyCoord(ra*u.deg,dec*u.deg)
            wave=np.asarray(h['WAVELENGTH'].data,float)
            spec=h['SPEC'].data;specerr=h['SPEC_ERR'].data
            for label,cra,cdec in CONTROLS:
                c=SkyCoord(cra*u.deg,cdec*u.deg);sep=coords.separation(c).arcsec
                idxs=np.where(sep<=3.0)[0]
                rows=[(int(i),float(z[i])) for i in idxs if np.isfinite(z[i])]
                rec={'label':label,'matched_source_observations':len(rows),'nearest_sep_arcsec':float(np.min(sep))}
                rec['lambda4363']=combine_for_rest(rows,wave,spec,specerr,TARGET)
                rec['pseudo_lines']={str(r):combine_for_rest(rows,wave,spec,specerr,r) for r in PSEUDO}
                # Do not emit coordinates/source names/source IDs beyond externally specified control labels.
                out['controls'].append(rec)
        testable=[r for r in out['controls'] if r['lambda4363']['technically_testable']]
        recovered=[r for r in testable if r['lambda4363']['recovered']]
        pseudos=[p for r in out['controls'] for p in r['pseudo_lines'].values() if p.get('technically_testable')]
        p_rec=[p for p in pseudos if p.get('recovered')]
        per_control_counts=[]
        for r in out['controls']:
            ps=[p for p in r['pseudo_lines'].values() if p.get('technically_testable')]
            if ps:per_control_counts.append(sum(p.get('recovered',False) for p in ps))
        out['technically_testable_controls']=len(testable);out['recovered_controls']=len(recovered)
        out['recovery_fraction']=len(recovered)/len(testable) if testable else None
        out['valid_pseudo_tests']=len(pseudos);out['pseudo_recoveries']=len(p_rec)
        out['pseudo_recovery_fraction']=len(p_rec)/len(pseudos) if pseudos else None
        out['median_pseudo_recoveries_per_control']=float(np.median(per_control_counts)) if per_control_counts else None
        conditions={'at_least_4_testable':len(testable)>=4,
                    'control_recovery_ge_075':len(testable)>=4 and len(recovered)/len(testable)>=0.75,
                    'pseudo_median_le_05':bool(per_control_counts and np.median(per_control_counts)<=0.5),
                    'pseudo_fraction_le_025':bool(pseudos and len(p_rec)/len(pseudos)<=0.25)}
        out['gate_conditions']=conditions;out['decision']='VIRUS_SPECTRUM_GATE_PASSED' if all(conditions.values()) else 'VIRUS_SPECTRUM_GATE_FAILED';out['success']=True
    except Exception as e:
        out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
