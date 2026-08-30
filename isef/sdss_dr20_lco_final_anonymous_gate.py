#!/usr/bin/env python3
"""Frozen final anonymous SDSS DR20 BOSS-LCO robust-unbound gate.

Implements research/SDSS_DR20_LCO_FINAL_ANONYMOUS_GATE_FREEZE.md and the
compute-only 250 km/s triage freeze. Emits aggregate counts only: never source
IDs, Gaia IDs, coordinates, row indices, spectra, or per-source kinematics.
"""
from pathlib import Path
import csv, gzip, io, json, math, shutil, urllib.parse, urllib.request
from collections import defaultdict
import numpy as np
from astropy.io import fits
import astropy.units as u
from astropy.coordinates import SkyCoord, Galactocentric, CartesianDifferential, ICRS
from astropy.table import Table
from galpy.potential import MWPotential2014, evaluatePotentials
from galpy.potential.mwpotentials import McMillan17, Cautun20
from galpy.util.conversion import get_physical

OUT=Path('results/sdss_dr20_lco_final_anonymous_gate.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
STAR='https://dr20.sdss.org/sas/dr20/spectro/astra/0.8.1/summary/mwmAllStar-0.8.1.fits.gz'
VISIT='https://dr20.sdss.org/sas/dr20/spectro/astra/0.8.1/summary/mwmAllVisit-0.8.1.fits.gz'
GAIA='https://gea.esac.esa.int/tap-server/tap/sync'
TRIAGE=250.0; DRAWS=2048
GC=Galactocentric(galcen_coord=ICRS(ra=266.4051*u.deg,dec=-28.936175*u.deg),galcen_distance=8.122*u.kpc,galcen_v_sun=CartesianDifferential([12.9,245.6,7.78]*u.km/u.s),z_sun=20.8*u.pc,roll=0*u.deg)

def download(url,p):
    req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-FinalAnonymous/1.0'})
    with urllib.request.urlopen(req,timeout=360) as r, open(p,'wb') as f:
        while True:
            b=r.read(8<<20)
            if not b: break
            f.write(b)

def ungzip(src,dst):
    with gzip.open(src,'rb') as a, open(dst,'wb') as b: shutil.copyfileobj(a,b,length=8<<20)

def speed(ra,dec,dist_pc,pmra,pmde,rv):
    c=SkyCoord(ra=np.asarray(ra)*u.deg,dec=np.asarray(dec)*u.deg,distance=np.asarray(dist_pc)*u.pc,pm_ra_cosdec=np.asarray(pmra)*u.mas/u.yr,pm_dec=np.asarray(pmde)*u.mas/u.yr,radial_velocity=np.asarray(rv)*u.km/u.s,frame='icrs')
    g=c.transform_to(GC)
    s=np.sqrt(g.v_x.to_value(u.km/u.s)**2+g.v_y.to_value(u.km/u.s)**2+g.v_z.to_value(u.km/u.s)**2)
    R=np.hypot(g.x.to_value(u.kpc),g.y.to_value(u.kpc)); z=np.abs(g.z.to_value(u.kpc))
    return np.asarray(s,float),np.asarray(R,float),np.asarray(z,float)

def tap_gaia(ids):
    fields='source_id,pmra,pmra_error,pmdec,pmdec_error,pmra_pmdec_corr,ruwe,astrometric_params_solved,visibility_periods_used,astrometric_excess_noise,duplicated_source,ipd_frac_multi_peak,ipd_gof_harmonic_amplitude,non_single_star'
    got={}
    for a in range(0,len(ids),250):
        batch=ids[a:a+250]
        q=f"SELECT {fields} FROM gaiadr3.gaia_source WHERE source_id IN ({','.join(str(int(x)) for x in batch)})"
        data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}).encode()
        req=urllib.request.Request(GAIA,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-DR20-FinalAnonymous/1.0'})
        with urllib.request.urlopen(req,timeout=240) as r: raw=r.read()
        t=Table.read(io.BytesIO(raw),format='votable')
        for row in t:
            sid=int(row['source_id']); got[sid]={n:row[n] for n in t.colnames if n!='source_id'}
    return got

def val(x):
    if np.ma.is_masked(x): return None
    try:
        if hasattr(x,'item'): return x.item()
    except: pass
    return x

def gaia_pass(g):
    try:
        pmra=float(val(g['pmra'])); epmra=float(val(g['pmra_error'])); pmde=float(val(g['pmdec'])); epmde=float(val(g['pmdec_error'])); corr=float(val(g['pmra_pmdec_corr']))
        ruwe=float(val(g['ruwe'])); solved=int(val(g['astrometric_params_solved'])); vis=int(val(g['visibility_periods_used'])); ex=float(val(g['astrometric_excess_noise']))
        dup=bool(val(g['duplicated_source'])); ipdm=float(val(g['ipd_frac_multi_peak'])); ipdg=float(val(g['ipd_gof_harmonic_amplitude'])); nss=int(val(g['non_single_star']))
        if not all(np.isfinite([pmra,epmra,pmde,epmde,corr,ruwe,ipdm,ipdg])): return False,None
        if epmra<=0 or epmde<=0 or abs(corr)>1: return False,None
        cov=np.array([[epmra**2,corr*epmra*epmde],[corr*epmra*epmde,epmde**2]],float)
        if np.min(np.linalg.eigvalsh(cov)) < -1e-10: return False,None
        ok=(solved==31 and ruwe<1.4 and vis>=8 and (not dup) and ipdm<2 and ipdg<0.1 and nss==0)
        return bool(ok),{'pmra':pmra,'pmde':pmde,'cov':cov,'excess':ex}
    except Exception:
        return False,None

def split_draw(rng,lo,med,hi,n):
    z=rng.normal(size=n); sig=np.where(z<0,med-lo,hi-med)
    return np.maximum(1.0,med+z*sig)

def model_setup():
    models={
      'MWPotential2014':(MWPotential2014,8.0,220.0),
      'Cautun20':(Cautun20,float(get_physical(Cautun20)['ro']),float(get_physical(Cautun20)['vo'])),
      'McMillan17':(McMillan17,float(get_physical(McMillan17)['ro']),float(get_physical(McMillan17)['vo']))}
    out={}
    for n,(p,ro,vo) in models.items():
        pinf=float(evaluatePotentials(p,1e5,0.0,use_physical=False))
        phi=float(evaluatePotentials(p,1.0,0.0,use_physical=False)); formula=math.sqrt(max(0,2*(pinf-phi)))*vo
        from galpy.potential import vesc
        builtin=float(vesc(p,1.0,use_physical=False)*vo)
        if abs(formula-builtin)/builtin>=0.01: raise RuntimeError('potential validation failed')
        out[n]=(p,ro,vo,pinf)
    return out

def escape_array(spec,R,z):
    p,ro,vo,pinf=spec
    phi=np.asarray(evaluatePotentials(p,np.asarray(R)/ro,np.asarray(z)/ro,use_physical=False),float)
    return np.sqrt(np.maximum(0.0,2*(pinf-phi)))*vo

def quant(x):
    x=np.asarray(x,float); x=x[np.isfinite(x)]
    return {'min':float(np.min(x)),'median':float(np.median(x)),'max':float(np.max(x))} if len(x) else None

def main():
    o={'success':False,'status':'FINAL_FROZEN_ANONYMOUS_LCO_GATE','identities_emitted':False,'triage_kms':TRIAGE,'mc_draws':DRAWS,'lco_6d_opened':True}
    try:
        # Validate potential implementation before source outcomes.
        models=model_setup(); o['potential_api_validated']=True
        sg=Path('/tmp/final_star.gz'); sf=Path('/tmp/final_star.fits'); download(STAR,sg); ungzip(sg,sf)
        need=['sdss_id','gaia_dr3_source_id','telescope','ra','dec','pmra','e_pmra','pmde','e_pmde','v_rad','e_v_rad','std_v_rad','snr','n_good_rvs','zwarning_flags','nmf_flags','n_associated','r_lo_geo','r_med_geo','r_hi_geo','r_lo_photogeo','r_med_photogeo','r_hi_photogeo']
        with fits.open(sf,memmap=True) as h:
            tabs=[x.data for x in h[1:] if getattr(x,'data',None) is not None and hasattr(x.data,'names') and all(k in x.data.names for k in need)]
            if not tabs: raise RuntimeError('summary table schema mismatch')
            d=max(tabs,key=len)
            tel=np.char.lower(np.char.strip(np.asarray(d['telescope']).astype(str))); lco=tel=='lco25m'
            v=np.asarray(d['v_rad'],float); ev=np.asarray(d['e_v_rad'],float); sv=np.asarray(d['std_v_rad'],float); sn=np.asarray(d['snr'],float); ng=np.asarray(d['n_good_rvs'],int); zw=np.asarray(d['zwarning_flags'],np.int64); nm=np.asarray(d['nmf_flags'],np.int64)
            rvok=lco&np.isfinite(v)&np.isfinite(ev)&np.isfinite(sv)&np.isfinite(sn)&(sn>10)&(ev<30)&(ng>=2)&(sv<=30)&(zw==0)&(nm==0)
            ra=np.asarray(d['ra'],float); dec=np.asarray(d['dec'],float); pmra=np.asarray(d['pmra'],float); pmde=np.asarray(d['pmde'],float); epmra=np.asarray(d['e_pmra'],float); epmde=np.asarray(d['e_pmde'],float); nass=np.asarray(d['n_associated'],int)
            gl=np.asarray(d['r_lo_geo'],float); gm=np.asarray(d['r_med_geo'],float); gh=np.asarray(d['r_hi_geo'],float); pl=np.asarray(d['r_lo_photogeo'],float); pm=np.asarray(d['r_med_photogeo'],float); ph=np.asarray(d['r_hi_photogeo'],float)
            finite=np.isfinite(ra)&np.isfinite(dec)&np.isfinite(pmra)&np.isfinite(pmde)&np.isfinite(epmra)&np.isfinite(epmde)&(epmra>0)&(epmde>0)&np.isfinite(gl)&np.isfinite(gm)&np.isfinite(gh)&np.isfinite(pl)&np.isfinite(pm)&np.isfinite(ph)&(gl>0)&(gm>0)&(gh>0)&(pl>0)&(pm>0)&(ph>0)&(gl<gm)&(gm<gh)&(pl<pm)&(pm<ph)
            gw=np.full(len(d),np.inf); pw=np.full(len(d),np.inf); pms=np.zeros(len(d)); ratio=np.full(len(d),np.inf)
            f=np.flatnonzero(finite); gw[f]=(gh[f]-gl[f])/(2*gm[f]);pw[f]=(ph[f]-pl[f])/(2*pm[f]);pms[f]=np.sqrt((pmra[f]/epmra[f])**2+(pmde[f]/epmde[f])**2);ratio[f]=np.maximum(gm[f]/pm[f],pm[f]/gm[f])
            reliable=rvok&finite&(gw<=.30)&(pw<=.30)&(pms>=5)&(nass==1)&(ratio<=1.25)
            ii=np.flatnonzero(reliable)
            o['true_lco_rows']=int(lco.sum());o['repeat_stable_lco_rows']=int(rvok.sum());o['summary_reliable_rows']=int(len(ii))
            if len(ii):
                vg,_,_=speed(ra[ii],dec[ii],gm[ii],pmra[ii],pmde[ii],v[ii]);vp,_,_=speed(ra[ii],dec[ii],pm[ii],pmra[ii],pmde[ii],v[ii]); vmax=np.maximum(vg,vp); keep=vmax>=TRIAGE
                jj=ii[keep];o['compute_triage_rows']=int(len(jj));o['triage_rejected_rows']=int(len(ii)-len(jj));o['triage_rejected_max_nominal_kms']=float(np.max(vmax[~keep])) if np.any(~keep) else None
            else: jj=np.array([],dtype=int);o['compute_triage_rows']=0;o['triage_rejected_rows']=0;o['triage_rejected_max_nominal_kms']=None
            # Copy only internally necessary rows before closing FITS.
            C=[]
            for idx in jj:
                C.append({'sdss':int(d['sdss_id'][idx]),'gaia':int(d['gaia_dr3_source_id'][idx]),'ra':float(ra[idx]),'dec':float(dec[idx]),'v':float(v[idx]),'ev':float(ev[idx]),'gl':float(gl[idx]),'gm':float(gm[idx]),'gh':float(gh[idx]),'pl':float(pl[idx]),'pm':float(pm[idx]),'ph':float(ph[idx])})
        # Full Gaia quality, internal IDs only.
        gids=sorted(set(x['gaia'] for x in C if x['gaia']>0)); gd=tap_gaia(gids) if gids else {}
        G=[]; excess=[]
        for x in C:
            g=gd.get(x['gaia']);
            if g is None: continue
            ok,a=gaia_pass(g)
            if ok:
                x['g']=a;G.append(x)
                if np.isfinite(a['excess']): excess.append(a['excess'])
        o['gaia_rows_returned']=int(len(gd));o['gaia_quality_pass_rows']=int(len(G));o['gaia_excess_noise_diagnostic']=quant(excess)
        # Direct visit replication.
        V=[]
        if G:
            vg=Path('/tmp/final_visit.gz'); vf=Path('/tmp/final_visit.fits');download(VISIT,vg);ungzip(vg,vf)
            ids=np.array([x['sdss'] for x in G],dtype=np.int64); idset=set(map(int,ids)); by=defaultdict(list)
            with fits.open(vf,memmap=True) as h:
                tabs=[x.data for x in h[1:] if getattr(x,'data',None) is not None and hasattr(x.data,'names') and all(k in x.data.names for k in ['sdss_id','telescope','xcsao_v_rad','xcsao_e_v_rad','snr','zwarning_flags'])]
                if not tabs: raise RuntimeError('visit table schema mismatch')
                d=max(tabs,key=len); tel=np.char.lower(np.char.strip(np.asarray(d['telescope']).astype(str))); sid=np.asarray(d['sdss_id'],np.int64)
                m=(tel=='lco25m')&np.isin(sid,ids); kk=np.flatnonzero(m)
                r=np.asarray(d['xcsao_v_rad'],float);e=np.asarray(d['xcsao_e_v_rad'],float);s=np.asarray(d['snr'],float);z=np.asarray(d['zwarning_flags'],np.int64)
                for k in kk:
                    if np.isfinite(r[k]) and np.isfinite(e[k]) and np.isfinite(s[k]) and e[k]<30 and s[k]>10 and z[k]==0: by[int(sid[k])].append(float(r[k]))
            for x in G:
                a=np.asarray(by.get(x['sdss'],[]),float)
                if len(a)<2: continue
                med=float(np.median(a)); sc=float(1.4826*np.median(np.abs(a-med))); within=int(np.sum(np.abs(a-x['v'])<=50))
                if abs(med-x['v'])<=30 and sc<=30 and within>=2: V.append(x)
        o['visit_replication_pass_rows']=int(len(V))
        # Full frozen MC. McMillan17 is evaluated first as a safe computational short-circuit;
        # a failure of either McMillan distance condition makes all-model survival impossible.
        final=[]; minps=[]; tested=0; fail_stage=defaultdict(int)
        for pos,x in enumerate(V):
            tested+=1; probs={}
            rng0=np.random.default_rng(31000000+pos)
            for label,lo,med,hi in [('geo',x['gl'],x['gm'],x['gh']),('photo',x['pl'],x['pm'],x['ph'])]:
                # independent deterministic stream per distance treatment
                rng=np.random.default_rng(rng0.integers(0,2**63-1)); dist=split_draw(rng,lo,med,hi,DRAWS)
                pp=rng.multivariate_normal([x['g']['pmra'],x['g']['pmde']],x['g']['cov'],size=DRAWS,check_valid='raise'); rv=rng.normal(x['v'],x['ev'],DRAWS)
                sp,R,z=speed(np.full(DRAWS,x['ra']),np.full(DRAWS,x['dec']),dist,pp[:,0],pp[:,1],rv)
                # Highest-escape model first.
                ve=escape_array(models['McMillan17'],R,z); pMc=float(np.mean(sp>ve)); probs[(label,'McMillan17')]=pMc
                if pMc<.95:
                    fail_stage[f'{label}_McMillan17']+=1; break
                for mn in ['Cautun20','MWPotential2014']:
                    ve=escape_array(models[mn],R,z); probs[(label,mn)]=float(np.mean(sp>ve))
                    if probs[(label,mn)]<.95: break
                if any(probs.get((label,m),0)<.95 for m in ['McMillan17','Cautun20','MWPotential2014']): break
            six=[probs.get((d,m),0.0) for d in ['geo','photo'] for m in ['MWPotential2014','Cautun20','McMillan17']]
            mp=float(min(six));minps.append(mp)
            if mp>=.95: final.append(x)
        o['mc_tested_rows']=int(tested);o['anonymous_robust_unbound_survivors']=int(len(final));o['sixway_min_probability_aggregate']=quant(minps);o['computational_short_circuit_counts']=dict(fail_stage)
        o['decision']='ANONYMOUS_ROBUST_UNBOUND_SURVIVORS_EXIST' if final else 'NO_ANONYMOUS_ROBUST_UNBOUND_SURVIVORS';o['success']=True
        o['note']='Aggregate-only frozen result. No source identity, coordinate, row index, per-source velocity, or per-source probability emitted.'
    except Exception as e:
        # Never include query strings/IDs in errors.
        o['error_type']=type(e).__name__;o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
    OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__': main()
