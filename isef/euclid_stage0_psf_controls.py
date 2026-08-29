#!/usr/bin/env python3
"""Empirical same-dither PSF null + pixel-level point-source injection pilot.

Builds a candidate-independent distribution of shape diagnostics from ordinary
star x epoch measurements in the Stage-0 patch, then injects PSF-shaped
brightenings into real noisy cutouts. This asks whether a morphology gate can
reject pixel artifacts while preserving astrophysically plausible unresolved
point-source variability.

Development-only. No discovery thresholds are frozen here.
"""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b
import euclid_stage0_psf_validation as pv

RES=Path('results/euclid_routed_feasibility.json'); NPZ=Path('results/euclid_routed_stamps.npz'); OUT=Path('results/euclid_stage0_psf_controls.json')
RNG=np.random.default_rng(20260829)


def sources(cube,hs,origins):
    _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5)
    tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
    x=np.asarray(tab['xcentroid'],float); y=np.asarray(tab['ycentroid'],float); peak=np.asarray(tab['peak'],float); ids=[]
    for j in range(len(x)):
        if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12):continue
        dd=np.hypot(x-x[j],y-y[j]);dd[j]=np.inf
        if np.min(dd)>=7:ids.append(j)
    ids=np.asarray(ids,int);ids=ids[np.argsort(peak[ids])[::-1][:80]]
    sx=x[ids]+origins[0][0];sy=y[ids]+origins[0][1];wr,wd=hs[0].w.pixel_to_world_values(sx,sy)
    return np.asarray(wr,float),np.asarray(wd,float),peak[ids]

def cut(cube,hs,origins,jra,jde,e):
    px,py=hs[e].w.world_to_pixel_values(jra,jde);x=float(px)-origins[e][0];y=float(py)-origins[e][1]
    if not(10<=x<b.STAMP-10 and 10<=y<b.STAMP-10):return None
    z=pv.aligned_cutout(cube[e],x,y);z,_=pv.bgsub(z);return z

def metrics(event,ref):
    scale,off,nres,corr,_,_=pv.fit_scale(event,ref)
    dt=pv.diff_template(event,ref)
    return {'scale':scale,'shape_residual':nres,'shape_correlation':corr,
            'diff_template_correlation':dt['difference_template_correlation'],
            'diff_template_residual':dt['difference_template_residual_fraction'],
            'brightest_positive_pixel_fraction':dt['positive_difference_brightest_pixel_fraction']}

def finite(v):return [float(x) for x in v if np.isfinite(x)]
def summary(v):
    a=np.asarray(finite(v));
    if not len(a):return {'n':0}
    return {'n':int(len(a)),'median':float(np.median(a)),'p90':float(np.percentile(a,90)),'p95':float(np.percentile(a,95)),'p99':float(np.percentile(a,99)),'max':float(np.max(a))}

def main():
    base=json.loads(RES.read_text());cube=np.load(NPZ)['stamps'];routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes);ra0=float(base['target']['ra']);de0=float(base['target']['dec'])
    origins=[]
    for q in hs:
        x,y=b.pix(q,ra0,de0);origins.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
    wr,wd,peak=sources(cube,hs,origins);controls=[];injections=[];valid_stars=0
    for j,(ra,de) in enumerate(zip(wr,wd)):
        cuts={e:cut(cube,hs,origins,ra,de,e) for e in range(16)}
        if any(v is None for v in cuts.values()):continue
        valid_stars+=1
        for e in range(16):
            g=e%4;peers=[q for q in range(g,16,4) if q!=e];ref=np.nanmedian(np.stack([cuts[q] for q in peers]),axis=0);m=metrics(cuts[e],ref);m.update({'star':j,'epoch':e,'peak':float(peak[j])});controls.append(m)
        # Pixel-level injections use a real exposure as noisy base, adding the
        # same-dither reference PSF signal. Start epochs are deterministic RNG draws.
        for amp in (0.05,0.10,0.20,0.50,1.00):
            for rep in range(8):
                e=int(RNG.integers(0,16));g=e%4;peers=[q for q in range(g,16,4) if q!=e];ref=np.nanmedian(np.stack([cuts[q] for q in peers]),axis=0)
                # source-only template: remove local annular floor from reference,
                # then add amplitude times that template to an actual noisy exposure.
                yy,xx=np.indices(ref.shape);c=(np.array(ref.shape)-1)/2;r=np.hypot(xx-c[1],yy-c[0]);ann=(r>=5.5)&(r<=7.5);floor=float(np.nanmedian(ref[ann]));tmpl=ref-floor
                injected=cuts[e]+amp*tmpl
                m=metrics(injected,ref);m.update({'star':j,'epoch':e,'peak':float(peak[j]),'amplitude':amp});injections.append(m)
    keys=['shape_residual','shape_correlation','diff_template_correlation','diff_template_residual','brightest_positive_pixel_fraction']
    out={'success':True,'note':'candidate-independent same-dither empirical PSF null and PSF-shaped pixel injection pilot on real Stage-0 cutouts','valid_stars':valid_stars,'control_measurements':len(controls),'injections':len(injections),'control_summary':{k:summary([q[k] for q in controls]) for k in keys},'injection_summary':{}}
    for amp in (0.05,0.10,0.20,0.50,1.00):
        rows=[q for q in injections if q['amplitude']==amp];out['injection_summary'][str(amp)]={k:summary([q[k] for q in rows]) for k in keys}
    # Evaluate simple candidate-independent morphology grids based on control quantiles.
    # For correlations higher is better; residual and bright-pixel concentration lower is better.
    grids=[]
    cshape=np.asarray(finite([q['shape_residual'] for q in controls]));ccorr=np.asarray(finite([q['shape_correlation'] for q in controls]));dcor=np.asarray(finite([q['diff_template_correlation'] for q in controls]));bp=np.asarray(finite([q['brightest_positive_pixel_fraction'] for q in controls]))
    for qtile in (0.90,0.95,0.975):
        limits={'shape_residual_max':float(np.quantile(cshape,qtile)),'shape_correlation_min':float(np.quantile(ccorr,1-qtile)),'brightest_positive_pixel_fraction_max':float(np.quantile(bp,qtile))}
        def passrow(r):return np.isfinite(r['shape_residual']) and np.isfinite(r['shape_correlation']) and np.isfinite(r['brightest_positive_pixel_fraction']) and r['shape_residual']<=limits['shape_residual_max'] and r['shape_correlation']>=limits['shape_correlation_min'] and r['brightest_positive_pixel_fraction']<=limits['brightest_positive_pixel_fraction_max']
        row={'control_quantile':qtile,**limits,'control_acceptance':float(np.mean([passrow(r) for r in controls]))}
        for amp in (0.05,0.10,0.20,0.50,1.00): row[f'injection_acceptance_{amp}']=float(np.mean([passrow(r) for r in injections if r['amplitude']==amp]))
        grids.append(row)
    out['morphology_grids']=grids
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
