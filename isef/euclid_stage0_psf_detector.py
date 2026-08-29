#!/usr/bin/env python3
"""Development detector using same-dither PSF-scale variability, not raw aperture excursions.

The Stage-0 aperture series produced large false excursions that changed strongly
with dither/crowding. This detector measures each exposure against the median of
its three same-dither peers using a subpixel-aligned PSF scale. It then calibrates
an empirical source-level null and injects unresolved point-source flux changes
into the real cutouts. Development field only; no survey-wide threshold is frozen.
"""
import json
from pathlib import Path
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b
import euclid_stage0_psf_validation as pv

RES=Path('results/euclid_routed_feasibility.json')
NPZ=Path('results/euclid_routed_stamps.npz')
OUT=Path('results/euclid_stage0_psf_detector.json')
RNG=np.random.default_rng(20260829)


def mad_sigma(x, floor=0.005):
    a=np.asarray(x,float);m=float(np.nanmedian(a));s=float(1.4826*np.nanmedian(np.abs(a-m)))
    return max(s,floor),m


def setup():
    base=json.loads(RES.read_text());cube=np.load(NPZ)['stamps']
    routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes)
    ra0=float(base['target']['ra']);de0=float(base['target']['dec']);orig=[]
    for q in hs:
        x,y=b.pix(q,ra0,de0);orig.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
    return base,cube,hs,orig


def sources(cube,hs,orig):
    _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5)
    tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
    x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[]
    for j in range(len(x)):
        if not (12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12): continue
        d=np.hypot(x-x[j],y-y[j]);d[j]=np.inf
        if np.min(d)>=7: ids.append(j)
    ids=np.asarray(ids,int);ids=ids[np.argsort(peak[ids])[::-1][:80]]
    sx=x[ids]+orig[0][0];sy=y[ids]+orig[0][1];ra,de=hs[0].w.pixel_to_world_values(sx,sy)
    return np.asarray(ra,float),np.asarray(de,float),peak[ids]


def cut(cube,hs,orig,ra,de,e):
    px,py=hs[e].w.world_to_pixel_values(ra,de);x=float(px)-orig[e][0];y=float(py)-orig[e][1]
    if not (10<=x<b.STAMP-10 and 10<=y<b.STAMP-10): return None
    z=pv.aligned_cutout(cube[e],x,y);z,_=pv.bgsub(z);return z


def scale_metric(event,ref):
    scale,off,res,corr,_,_=pv.fit_scale(event,ref)
    return float(scale-1),float(res),float(corr)


def summary(a):
    a=np.asarray(a,float);a=a[np.isfinite(a)]
    if not len(a): return {'n':0}
    return {'n':int(len(a)),'median':float(np.median(a)),'p90':float(np.percentile(a,90)),'p95':float(np.percentile(a,95)),'p99':float(np.percentile(a,99)),'max':float(np.max(a))}


def main():
    base,cube,hs,orig=setup();ra,de,peak=sources(cube,hs,orig)
    stars=[];inj={a:[] for a in (0.05,0.10,0.20,0.50,1.00)}
    for j,(r,d) in enumerate(zip(ra,de)):
        cuts={e:cut(cube,hs,orig,r,d,e) for e in range(16)}
        if any(v is None for v in cuts.values()): continue
        frac=[];shape=[];corr=[]
        for e in range(16):
            peers=[p for p in range(e%4,16,4) if p!=e]
            ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0)
            f,s,c=scale_metric(cuts[e],ref);frac.append(f);shape.append(s);corr.append(c)
        frac=np.asarray(frac);shape=np.asarray(shape);corr=np.asarray(corr)
        sig,med=mad_sigma(frac);z=np.abs(frac-med)/sig
        stars.append({'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'psf_fraction':frac.tolist(),'shape_residual':shape.tolist(),'shape_correlation':corr.tolist(),'robust_sigma':sig,'median_fraction':med,'max_abs_fraction':float(np.max(np.abs(frac))),'max_robust_z':float(np.max(z)),'max_epoch':int(np.argmax(np.abs(frac)))})
        # Inject point-source changes at random real epochs. The source-only template
        # is the same-dither median reference with its annular floor removed.
        for amp in inj:
            for _ in range(16):
                e=int(RNG.integers(0,16));peers=[p for p in range(e%4,16,4) if p!=e]
                ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0)
                yy,xx=np.indices(ref.shape);cc=(np.array(ref.shape)-1)/2;rr=np.hypot(xx-cc[1],yy-cc[0]);floor=float(np.nanmedian(ref[(rr>=5.5)&(rr<=7.5)]));tmpl=ref-floor
                event=cuts[e]+amp*tmpl;f,s,c=scale_metric(event,ref)
                inj[amp].append({'star':j,'epoch':e,'recovered_fraction':f,'abs_error':abs(f-amp),'shape_residual':s,'shape_correlation':c})
    maxima=np.asarray([s['max_abs_fraction'] for s in stars]);zs=np.asarray([s['max_robust_z'] for s in stars])
    # Report thresholds rather than choosing a discovery rule. max-null is useful as
    # a zero-observed-FP development benchmark; q95/q99 show less conservative scales.
    thresholds={'max_abs_fraction_q95':float(np.quantile(maxima,.95)),'max_abs_fraction_q99':float(np.quantile(maxima,.99)),'max_abs_fraction_zero_observed_fp':float(np.max(maxima)),'max_robust_z_q95':float(np.quantile(zs,.95)),'max_robust_z_zero_observed_fp':float(np.max(zs))}
    iout={}
    for amp,rows in inj.items():
        rec=np.asarray([r['recovered_fraction'] for r in rows]);err=np.asarray([r['abs_error'] for r in rows])
        iout[str(amp)]={'trials':len(rows),'recovered_fraction':summary(rec),'abs_error':summary(err),'recovery_gt_q95_null':float(np.mean(np.abs(rec)>=thresholds['max_abs_fraction_q95'])),'recovery_gt_zero_fp_null':float(np.mean(np.abs(rec)>thresholds['max_abs_fraction_zero_observed_fp']))}
    stars.sort(key=lambda x:x['max_abs_fraction'],reverse=True)
    out={'success':True,'note':'development same-dither PSF-scale detector; raw aperture variability is not used for ranking','valid_stars':len(stars),'source_level_max_abs_fraction':summary(maxima),'source_level_max_robust_z':summary(zs),'thresholds':thresholds,'injections':iout,'top_sources':stars[:15]}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
