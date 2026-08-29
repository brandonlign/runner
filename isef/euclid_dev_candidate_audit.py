#!/usr/bin/env python3
"""Deep validation of high-amplitude *development* survivors.

This script is intentionally downstream of the frozen population-quality gate.
It does not define thresholds. It re-opens only development sources with a
full-gate corrected PSF excursion >=18% and asks whether each event behaves like
an unresolved stellar flux change rather than a residual image/source-specific
systematic. Checks include all 16 same-dither PSF amplitudes, multi-aperture
amplitude agreement, difference-template morphology, local same-epoch comparison
stars, all-epoch released FLG status, nearest detected-neighbor distance, and a
small-radius Gaia DR3 lookup. Development survivors are never called discoveries.
"""
import io,json,math,urllib.parse,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from astropy.table import Table
import euclid_routed_feasibility as b
import euclid_exact_routing as er
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_validation as pv
import euclid_stage0_psf_flag_gate as fg

MP=Path('results/euclid_stage0_multi_patch.json');OUT=Path('results/euclid_dev_candidate_audit.json')
MIN_EVENT=0.18;GAIA='https://gaia.aip.de/tap/sync'

def gaia_query(adql):
    body=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':adql}).encode();req=urllib.request.Request(GAIA,data=body,headers={'User-Agent':'isef-euclid-candidate-audit/1.0','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=12) as r:raw=r.read()
    txt=raw.decode('utf-8',errors='replace')
    if 'value="ERROR"' in txt[:5000]:raise RuntimeError(txt[:1500])
    t=Table.read(io.BytesIO(raw),format='votable');rows=[]
    for rr in t:
        rows.append({n:(None if np.ma.is_masked(rr[n]) else (rr[n].item() if hasattr(rr[n],'item') else rr[n])) for n in t.colnames})
    return rows

def gaia_lookup(ra,de):
    q=f"SELECT TOP 3 source_id,ra,dec,phot_g_mean_mag,bp_rp,parallax,pmra,pmdec FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra},{de},0.000555556)) ORDER BY phot_g_mean_mag ASC"
    try:
        rows=gaia_query(q)
        if not rows:return {'matched':False}
        for x in rows:
            x['separation_arcsec']=math.hypot((float(x['ra'])-ra)*math.cos(math.radians(de))*3600,(float(x['dec'])-de)*3600)
        best=min(rows,key=lambda x:x['separation_arcsec']);sid=str(best['source_id']);var=None
        try:
            vr=gaia_query(f"SELECT TOP 1 * FROM gaiadr3.vari_classifier_result WHERE source_id={sid}");var=vr[0] if vr else None
        except Exception as e:var={'lookup_error':f'{type(e).__name__}: {e}'}
        return {'matched':True,'best':best,'classifier':var,'all_matches':rows}
    except Exception as e:return {'matched':False,'lookup_error':f'{type(e).__name__}: {e}'}

def patch_cube(p):
    target=(float(p['target']['ra']),float(p['target']['dec']));routes={int(k):int(v) for k,v in p['routes'].items()};hs=b.epoch_headers(routes);ims=[None]*16;meta=[None]*16
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(er.stamp,e,hs[e],target[0],target[1]) for e in range(16)]
        for fut in as_completed(fs):e,z,m=fut.result();ims[e]=z;meta[e]=m
    return np.stack(ims),hs,[(int(m['x0']),int(m['y0'])) for m in meta]

def multi_ap(event,ref):
    out={}
    for rad in (1.5,2.2,3.0,4.0):
        rf=pv.flux(ref,rad);ef=pv.flux(event,rad);out[str(rad)]=float(ef/rf-1) if np.isfinite(rf) and rf!=0 else None
    return out

def all_flag_status(hs,ra,de):
    out=[None]*16
    def one(e):
        try:a,c=fg.flag_artifact(hs[e],e,ra,de);return e,{'artifact':bool(a),'center_flag':int(c)}
        except Exception as x:return e,{'artifact':True,'error':f'{type(x).__name__}: {x}'}
    with ThreadPoolExecutor(max_workers=16) as ex:
        fs=[ex.submit(one,e) for e in range(16)]
        for f in as_completed(fs):e,v=f.result();out[e]=v
    return out

def audit_candidate(c,p,cube,hs,orig,lim):
    ra=float(c['ra']);de=float(c['dec']);event_epoch=int(c['max_epoch']);cuts={e:pd.cut(cube,hs,orig,ra,de,e) for e in range(16)}
    if any(z is None for z in cuts.values()):return {'error':'candidate leaves stamp','ra':ra,'dec':de}
    fractions=[];shapes=[];corrs=[]
    for e in range(16):
        peers=[q for q in range(e%4,16,4) if q!=e];ref=np.nanmedian(np.stack([cuts[q] for q in peers]),axis=0);f,s,co=pd.scale_metric(cuts[e],ref);fractions.append(f);shapes.append(s);corrs.append(co)
    peers=[q for q in range(event_epoch%4,16,4) if q!=event_epoch];ref=np.nanmedian(np.stack([cuts[q] for q in peers]),axis=0);event=cuts[event_epoch];scale,off,res,corr,_,_=pv.fit_scale(event,ref);dt=pv.diff_template(event,ref)
    # local comparison-star distribution at the event epoch
    sra,sde,speak=pd.sources(cube,hs,orig);local=[]
    for j,(r,d) in enumerate(zip(sra,sde)):
        cc={q:pd.cut(cube,hs,orig,float(r),float(d),q) for q in [event_epoch]+peers}
        if any(v is None for v in cc.values()):continue
        rr=np.nanmedian(np.stack([cc[q] for q in peers]),axis=0);f,s,co=pd.scale_metric(cc[event_epoch],rr)
        if pd.morph_ok(s,co,lim):local.append({'star':j,'ra':float(r),'dec':float(d),'peak':float(speak[j]),'fraction':float(f)})
    vals=np.asarray([x['fraction'] for x in local],float);candidate_raw=float(fractions[event_epoch]);cm=float(np.median(vals)) if len(vals) else 0;candidate_corr=fg.common_correct(candidate_raw,cm);rank=float(np.mean(np.abs(vals-cm)<=abs(candidate_raw-cm))) if len(vals) else None
    sep=[]
    for r,d in zip(sra,sde):
        ds=math.hypot((float(r)-ra)*math.cos(math.radians(de))*3600,(float(d)-de)*3600)
        if ds>0.02:sep.append(ds)
    flags=all_flag_status(hs,ra,de)
    return {'ra':ra,'dec':de,'patch':int(p['patch']),'event_epoch':event_epoch,'reported_corrected_fraction':float(c['signed_max_fraction']),'recomputed_raw_psf_fraction':candidate_raw,'recomputed_local_common_mode_fraction':cm,'recomputed_corrected_fraction':candidate_corr,'all_epoch_raw_psf_fraction':[float(x) for x in fractions],'all_epoch_shape_residual':[float(x) for x in shapes],'all_epoch_shape_correlation':[float(x) for x in corrs],'event_morphology_ok':pd.morph_ok(res,corr,lim),'event_shape_residual':float(res),'event_shape_correlation':float(corr),'event_psf_scale':float(scale-1),'event_multi_aperture_fraction':multi_ap(event,ref),'difference_template':dt,'same_dither_peers':peers,'local_morphology_clean_comparisons':len(local),'local_event_fraction_summary':pd.summary(vals),'candidate_abs_deviation_percentile_within_local':rank,'nearest_detected_neighbor_arcsec':float(min(sep)) if sep else None,'all_epoch_flag_status':flags,'event_flag_clean':not bool(flags[event_epoch]['artifact']),'gaia':gaia_lookup(ra,de)}

def main():
    mp=json.loads(MP.read_text());lim=pd.morphology_limits();selected=[]
    for p in mp['patches']:
        for c in p['top_sources']:
            if float(c['max_abs_fraction'])>=MIN_EVENT:selected.append((p,c))
    rows=[];cache={}
    for p,c in selected:
        k=int(p['patch'])
        if k not in cache:cache[k]=patch_cube(p)
        rows.append(audit_candidate(c,p,*cache[k],lim))
    rows.sort(key=lambda x:abs(float(x.get('reported_corrected_fraction',0))),reverse=True)
    out={'success':True,'note':'candidate-specific audit of development survivors only; results cannot define population thresholds','selection_min_abs_corrected_fraction':MIN_EVENT,'candidates':len(rows),'rows':rows}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
