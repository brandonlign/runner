#!/usr/bin/env python3
"""SQL-backed transport implementation of the already-frozen final anonymous LCO gate.

Scientific selection, visit cuts, Monte Carlo, distance treatments, potentials,
and 0.95 six-way criterion are unchanged. The only substantive transport change
is that visit rows are fetched from DR20 SkyServer `mwm_boss_allvisit` for the
internally selected SDSS IDs instead of downloading the 1.2-GB mwmAllVisit FITS.
No identities or per-source outcomes are emitted.
"""
from pathlib import Path
from collections import defaultdict
import importlib.util, io, json, math, os, time, urllib.parse, urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table

spec=importlib.util.spec_from_file_location('gate','isef/sdss_dr20_lco_final_anonymous_gate.py')
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
SQL='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'


def robust_download(url,p):
    p=Path(p); part=Path(str(p)+'.part'); last=None
    for attempt in range(1,6):
        try:
            if part.exists(): part.unlink()
            req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-FinalAnonymous-SQL/1.0'})
            with urllib.request.urlopen(req,timeout=600) as r, open(part,'wb') as f:
                clen=r.headers.get('Content-Length'); expected=int(clen) if clen and clen.isdigit() else None; n=0
                while True:
                    b=r.read(8<<20)
                    if not b: break
                    f.write(b); n+=len(b)
                f.flush(); os.fsync(f.fileno())
            if expected is not None and n!=expected: raise EOFError('incomplete HTTP body')
            if n<=0: raise EOFError('empty HTTP body')
            part.replace(p); return
        except Exception as e:
            last=e
            try:
                if part.exists(): part.unlink()
            except Exception: pass
            if attempt<5: time.sleep(2**attempt)
    raise last


def tap_gaia(ids):
    fields='source_id,pmra,pmra_error,pmdec,pmdec_error,pmra_pmdec_corr,ruwe,astrometric_params_solved,visibility_periods_used,astrometric_excess_noise,duplicated_source,ipd_frac_multi_peak,ipd_gof_harmonic_amplitude,non_single_star'
    got={}
    for a in range(0,len(ids),250):
        batch=ids[a:a+250]
        q=f"SELECT {fields} FROM gaiadr3.gaia_source WHERE source_id IN ({','.join(str(int(x)) for x in batch)})"
        data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}).encode()
        req=urllib.request.Request(g.GAIA,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-DR20-FinalAnonymous-SQL/1.0'})
        with urllib.request.urlopen(req,timeout=240) as r: raw=r.read()
        t=Table.read(io.BytesIO(raw),format='votable'); cmap={str(n).lower():n for n in t.colnames}; scol=cmap['source_id']
        for row in t:
            sid=int(row[scol]); got[sid]={str(n).lower():row[n] for n in t.colnames if n!=scol}
    return got


def sql_visit_rows(ids):
    by=defaultdict(list); row_count=0
    # 200 IDs keeps GET URLs comfortably below common proxy limits.
    for a in range(0,len(ids),200):
        batch=ids[a:a+200]
        q=("SELECT sdss_id,telescope,xcsao_v_rad,xcsao_e_v_rad,snr,zwarning_flags "
           "FROM mwm_boss_allvisit WHERE telescope='lco25m' AND sdss_id IN ("+
           ','.join(str(int(x)) for x in batch)+")")
        url=SQL+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'})
        last=None
        for attempt in range(1,5):
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-FinalAnonymous-SQL/1.0'})
                with urllib.request.urlopen(req,timeout=180) as r: obj=json.loads(r.read().decode('utf-8','replace'))
                tables=[x for x in obj if isinstance(x,dict) and x.get('TableName')=='Table1']
                rows=tables[0].get('Rows',[]) if tables else []
                for r in rows:
                    try:
                        sid=int(r['sdss_id']); rv=float(r['xcsao_v_rad']); er=float(r['xcsao_e_v_rad']); sn=float(r['snr']); zw=int(r['zwarning_flags'])
                        if np.isfinite(rv) and np.isfinite(er) and np.isfinite(sn) and er<30 and sn>10 and zw==0:
                            by[sid].append(rv); row_count+=1
                    except (TypeError,ValueError,KeyError):
                        continue
                last=None; break
            except Exception as e:
                last=e
                if attempt<4: time.sleep(2**attempt)
        if last is not None: raise last
    return by,row_count


def main():
    o={'success':False,'status':'FINAL_FROZEN_ANONYMOUS_LCO_GATE','identities_emitted':False,'triage_kms':g.TRIAGE,'mc_draws':g.DRAWS,'lco_6d_opened':True,'visit_transport':'SkyServer mwm_boss_allvisit SQL'}
    try:
        models=g.model_setup(); o['potential_api_validated']=True
        sg=Path('/tmp/sql_final_star.gz'); sf=Path('/tmp/sql_final_star.fits'); robust_download(g.STAR,sg); g.ungzip(sg,sf)
        need=['sdss_id','gaia_dr3_source_id','telescope','ra','dec','pmra','e_pmra','pmde','e_pmde','v_rad','e_v_rad','std_v_rad','snr','n_good_rvs','zwarning_flags','nmf_flags','n_associated','r_lo_geo','r_med_geo','r_hi_geo','r_lo_photogeo','r_med_photogeo','r_hi_photogeo']
        with fits.open(sf,memmap=True) as h:
            tabs=[x.data for x in h[1:] if getattr(x,'data',None) is not None and hasattr(x.data,'names') and all(k in x.data.names for k in need)]
            if not tabs: raise RuntimeError('summary table schema mismatch')
            d=max(tabs,key=len); tel=np.char.lower(np.char.strip(np.asarray(d['telescope']).astype(str))); lco=tel=='lco25m'
            v=np.asarray(d['v_rad'],float); ev=np.asarray(d['e_v_rad'],float); sv=np.asarray(d['std_v_rad'],float); sn=np.asarray(d['snr'],float); ng=np.asarray(d['n_good_rvs'],int); zw=np.asarray(d['zwarning_flags'],np.int64); nm=np.asarray(d['nmf_flags'],np.int64)
            rvok=lco&np.isfinite(v)&np.isfinite(ev)&np.isfinite(sv)&np.isfinite(sn)&(sn>10)&(ev<30)&(ng>=2)&(sv<=30)&(zw==0)&(nm==0)
            ra=np.asarray(d['ra'],float); dec=np.asarray(d['dec'],float); pmra=np.asarray(d['pmra'],float); pmde=np.asarray(d['pmde'],float); epmra=np.asarray(d['e_pmra'],float); epmde=np.asarray(d['e_pmde'],float); nass=np.asarray(d['n_associated'],int)
            gl=np.asarray(d['r_lo_geo'],float); gm=np.asarray(d['r_med_geo'],float); gh=np.asarray(d['r_hi_geo'],float); pl=np.asarray(d['r_lo_photogeo'],float); pm=np.asarray(d['r_med_photogeo'],float); ph=np.asarray(d['r_hi_photogeo'],float)
            finite=np.isfinite(ra)&np.isfinite(dec)&np.isfinite(pmra)&np.isfinite(pmde)&np.isfinite(epmra)&np.isfinite(epmde)&(epmra>0)&(epmde>0)&np.isfinite(gl)&np.isfinite(gm)&np.isfinite(gh)&np.isfinite(pl)&np.isfinite(pm)&np.isfinite(ph)&(gl>0)&(gm>0)&(gh>0)&(pl>0)&(pm>0)&(ph>0)&(gl<gm)&(gm<gh)&(pl<pm)&(pm<ph)
            gw=np.full(len(d),np.inf); pw=np.full(len(d),np.inf); pms=np.zeros(len(d)); ratio=np.full(len(d),np.inf); f=np.flatnonzero(finite)
            gw[f]=(gh[f]-gl[f])/(2*gm[f]); pw[f]=(ph[f]-pl[f])/(2*pm[f]); pms[f]=np.sqrt((pmra[f]/epmra[f])**2+(pmde[f]/epmde[f])**2); ratio[f]=np.maximum(gm[f]/pm[f],pm[f]/gm[f])
            reliable=rvok&finite&(gw<=.30)&(pw<=.30)&(pms>=5)&(nass==1)&(ratio<=1.25); ii=np.flatnonzero(reliable)
            o['true_lco_rows']=int(lco.sum()); o['repeat_stable_lco_rows']=int(rvok.sum()); o['summary_reliable_rows']=int(len(ii))
            if len(ii):
                vg,_,_=g.speed(ra[ii],dec[ii],gm[ii],pmra[ii],pmde[ii],v[ii]); vp,_,_=g.speed(ra[ii],dec[ii],pm[ii],pmra[ii],pmde[ii],v[ii]); vmax=np.maximum(vg,vp); keep=vmax>=g.TRIAGE; jj=ii[keep]
                o['compute_triage_rows']=int(len(jj)); o['triage_rejected_rows']=int(len(ii)-len(jj)); o['triage_rejected_max_nominal_kms']=float(np.max(vmax[~keep])) if np.any(~keep) else None
            else:
                jj=np.array([],dtype=int); o['compute_triage_rows']=0; o['triage_rejected_rows']=0; o['triage_rejected_max_nominal_kms']=None
            C=[{'sdss':int(d['sdss_id'][i]),'gaia':int(d['gaia_dr3_source_id'][i]),'ra':float(ra[i]),'dec':float(dec[i]),'v':float(v[i]),'ev':float(ev[i]),'gl':float(gl[i]),'gm':float(gm[i]),'gh':float(gh[i]),'pl':float(pl[i]),'pm':float(pm[i]),'ph':float(ph[i])} for i in jj]
        gids=sorted(set(x['gaia'] for x in C if x['gaia']>0)); gd=tap_gaia(gids) if gids else {}; G=[]; excess=[]
        for x in C:
            gg=gd.get(x['gaia'])
            if gg is None: continue
            ok,a=g.gaia_pass(gg)
            if ok:
                x['g']=a; G.append(x)
                if np.isfinite(a['excess']): excess.append(a['excess'])
        o['gaia_rows_returned']=int(len(gd)); o['gaia_quality_pass_rows']=int(len(G)); o['gaia_excess_noise_diagnostic']=g.quant(excess)
        V=[]
        if G:
            ids=[x['sdss'] for x in G]; by,nrows=sql_visit_rows(ids); o['quality_usable_sql_visit_rows']=int(nrows)
            for x in G:
                a=np.asarray(by.get(x['sdss'],[]),float)
                if len(a)<2: continue
                med=float(np.median(a)); sc=float(1.4826*np.median(np.abs(a-med))); within=int(np.sum(np.abs(a-x['v'])<=50))
                if abs(med-x['v'])<=30 and sc<=30 and within>=2: V.append(x)
        else: o['quality_usable_sql_visit_rows']=0
        o['visit_replication_pass_rows']=int(len(V))
        final=[]; minps=[]; tested=0; fail_stage=defaultdict(int)
        for pos,x in enumerate(V):
            tested+=1; probs={}; rng0=np.random.default_rng(31000000+pos)
            for label,lo,med,hi in [('geo',x['gl'],x['gm'],x['gh']),('photo',x['pl'],x['pm'],x['ph'])]:
                rng=np.random.default_rng(rng0.integers(0,2**63-1)); dist=g.split_draw(rng,lo,med,hi,g.DRAWS); pp=rng.multivariate_normal([x['g']['pmra'],x['g']['pmde']],x['g']['cov'],size=g.DRAWS,check_valid='raise'); rv=rng.normal(x['v'],x['ev'],g.DRAWS)
                sp,R,z=g.speed(np.full(g.DRAWS,x['ra']),np.full(g.DRAWS,x['dec']),dist,pp[:,0],pp[:,1],rv)
                ve=g.escape_array(models['McMillan17'],R,z); pMc=float(np.mean(sp>ve)); probs[(label,'McMillan17')]=pMc
                if pMc<.95: fail_stage[f'{label}_McMillan17']+=1; break
                for mn in ['Cautun20','MWPotential2014']:
                    ve=g.escape_array(models[mn],R,z); probs[(label,mn)]=float(np.mean(sp>ve))
                    if probs[(label,mn)]<.95: break
                if any(probs.get((label,m),0)<.95 for m in ['McMillan17','Cautun20','MWPotential2014']): break
            six=[probs.get((dd,m),0.0) for dd in ['geo','photo'] for m in ['MWPotential2014','Cautun20','McMillan17']]; mp=float(min(six)); minps.append(mp)
            if mp>=.95: final.append(x)
        o['mc_tested_rows']=int(tested); o['anonymous_robust_unbound_survivors']=int(len(final)); o['sixway_min_probability_aggregate']=g.quant(minps); o['computational_short_circuit_counts']=dict(fail_stage)
        o['decision']='ANONYMOUS_ROBUST_UNBOUND_SURVIVORS_EXIST' if final else 'NO_ANONYMOUS_ROBUST_UNBOUND_SURVIVORS'; o['success']=True
        o['note']='Aggregate-only frozen result. SQL is transport only; all frozen scientific criteria unchanged. No identities emitted.'
    except Exception as e:
        o['error_type']=type(e).__name__; o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
    g.OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))

if __name__=='__main__': main()
