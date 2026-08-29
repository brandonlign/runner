#!/usr/bin/env python3
"""Calibrate same-dither aperture-vs-PSF amplitude consistency on real controls/injections.

A real unresolved stellar flux change should produce a comparable fractional
change in aperture flux and in a fit of the baseline same-dither PSF scale.
This diagnostic targets crowding/background failures where aperture photometry
reports a huge event but the stellar PSF itself barely changes.
Development-only; no survey threshold is frozen.
"""
import json
from pathlib import Path
import numpy as np
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
import euclid_routed_feasibility as b
import euclid_stage0_psf_validation as pv
import euclid_stage0_flag_validation as fv

RES=Path('results/euclid_routed_feasibility.json');NPZ=Path('results/euclid_routed_stamps.npz');AUD=Path('results/euclid_stage0_unflagged_psf_audit.json');OUT=Path('results/euclid_stage0_amplitude_consistency.json')
RNG=np.random.default_rng(20260829)

def cutout_sources(cube,hs,orig):
    _,bg,std=sigma_clipped_stats(cube[0],sigma=3,maxiters=5);tab=DAOStarFinder(fwhm=1.8,threshold=max(6*std,1e-6),exclude_border=True)(cube[0]-bg)
    x=np.asarray(tab['xcentroid'],float);y=np.asarray(tab['ycentroid'],float);peak=np.asarray(tab['peak'],float);ids=[]
    for j in range(len(x)):
        if not(12<x[j]<b.STAMP-12 and 12<y[j]<b.STAMP-12):continue
        d=np.hypot(x-x[j],y-y[j]);d[j]=np.inf
        if np.min(d)>=7:ids.append(j)
    ids=np.asarray(ids,int);ids=ids[np.argsort(peak[ids])[::-1][:80]];sx=x[ids]+orig[0][0];sy=y[ids]+orig[0][1];wr,wd=hs[0].w.pixel_to_world_values(sx,sy);return np.asarray(wr,float),np.asarray(wd,float)
def acut(cube,hs,orig,ra,de,e):
    px,py=hs[e].w.world_to_pixel_values(ra,de);x=float(px)-orig[e][0];y=float(py)-orig[e][1]
    if not(10<=x<b.STAMP-10 and 10<=y<b.STAMP-10):return None
    z=pv.aligned_cutout(cube[e],x,y);z,_=pv.bgsub(z);return z
def apflux(z,r=2.2):
    yy,xx=np.indices(z.shape);c=(np.array(z.shape)-1)/2;rad=np.hypot(xx-c[1],yy-c[0]);return float(np.nansum(z[rad<=r]))
def metric(event,ref):
    scale,_,shape,corr,_,_=pv.fit_scale(event,ref);af=apflux(event)/max(apflux(ref),1e-12);return {'psf_fraction':float(scale-1),'aperture_fraction':float(af-1),'amplitude_disagreement':float(abs((scale-1)-(af-1))),'relative_disagreement':float(abs((scale-1)-(af-1))/max(abs(af-1),0.03)),'shape_residual':float(shape),'shape_correlation':float(corr)}
def summ(v):
    a=np.asarray(v,float);return {'n':len(a),'median':float(np.median(a)),'p90':float(np.percentile(a,90)),'p95':float(np.percentile(a,95)),'p99':float(np.percentile(a,99)),'max':float(np.max(a))}
def main():
    base=json.loads(RES.read_text());cube=np.load(NPZ)['stamps'];ra0=float(base['target']['ra']);de0=float(base['target']['dec']);routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes);orig=[]
    for q in hs:
        x,y=b.pix(q,ra0,de0);orig.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
    wr,wd=cutout_sources(cube,hs,orig);controls=[];inj=[]
    for j,(ra,de) in enumerate(zip(wr,wd)):
        cuts={e:acut(cube,hs,orig,ra,de,e) for e in range(16)}
        if any(z is None for z in cuts.values()):continue
        for e in range(16):
            peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);m=metric(cuts[e],ref);m.update({'star':j,'epoch':e});controls.append(m)
        for amp in (0.05,0.10,0.20,0.50,1.00):
            for rep in range(8):
                e=int(RNG.integers(0,16));peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);yy,xx=np.indices(ref.shape);c=(np.array(ref.shape)-1)/2;r=np.hypot(xx-c[1],yy-c[0]);floor=float(np.nanmedian(ref[(r>=5.5)&(r<=7.5)]));tmpl=ref-floor;event=cuts[e]+amp*tmpl;m=metric(event,ref);m.update({'star':j,'epoch':e,'injected_amplitude':amp});inj.append(m)
    ctrl_rel=[x['relative_disagreement'] for x in controls if abs(x['aperture_fraction'])>=0.05];lim=float(np.quantile(ctrl_rel,0.95)) if ctrl_rel else 1.0
    # Also quantify absolute recovery of PSF-fit amplitude vs true injection.
    injout={}
    for amp in (0.05,0.10,0.20,0.50,1.00):
        z=[x for x in inj if x['injected_amplitude']==amp];err=[abs(x['psf_fraction']-amp) for x in z];agree=[x['relative_disagreement'] for x in z];injout[str(amp)]={'trials':len(z),'psf_amplitude_abs_error':summ(err),'amplitude_consistency':summ(agree),'pass_fraction_at_control95':float(np.mean(np.asarray(agree)<=lim))}
    # Recompute every prior unflagged >20% event using same-dither aperture and PSF amplitudes.
    prior=json.loads(AUD.read_text());cand=[]
    for grp in prior['source_groups']:
      for r0 in grp['rows']:
        ra=float(r0['ra']);de=float(r0['dec']);e=int(r0['epoch']);event=acut(cube,hs,orig,ra,de,e);peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([acut(cube,hs,orig,ra,de,p) for p in peers]),axis=0);m=metric(event,ref);m.update({'ra':ra,'dec':de,'epoch':e,'global_aperture_excursion':float(r0['signed_residual']),'passes_amplitude_consistency':bool(m['relative_disagreement']<=lim)});cand.append(m)
    out={'success':True,'note':'same-dither amplitude-consistency calibration; threshold is development 95th percentile of ordinary controls with >=5% aperture deviation','control_measurements':len(controls),'control_relative_disagreement_ge5pct':summ(ctrl_rel) if ctrl_rel else None,'development_relative_disagreement_limit':lim,'injections':injout,'previous_unflagged_gt20_events':cand}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
