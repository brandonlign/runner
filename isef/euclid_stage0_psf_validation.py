#!/usr/bin/env python3
"""Same-dither PSF-shape validation for Euclid Stage-0 survivor events.

For each strict morphology-clean large excursion, align the event and the three
other exposures at the same dither position on the candidate sky coordinate.
A genuine unresolved stellar brightening should be well described by a scaled
version of the same-dither baseline PSF and its difference image should be
PSF-shaped. A cosmic ray/hot pixel generally produces a much sharper or
otherwise incoherent residual.

Development diagnostic only; it is not a discovery classifier.
"""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates
import euclid_routed_feasibility as b

RES=Path('results/euclid_routed_feasibility.json')
NPZ=Path('results/euclid_routed_stamps.npz')
SURV=Path('results/euclid_stage0_survivors.json')
OUT=Path('results/euclid_stage0_psf_validation.json')
SIZE=17; HALF=SIZE//2


def aligned_cutout(im,x,y,size=SIZE):
    h=size//2
    yy,xx=np.mgrid[-h:h+1,-h:h+1].astype(float)
    return map_coordinates(im,[y+yy,x+xx],order=3,mode='constant',cval=np.nan,prefilter=True)

def bgsub(z):
    yy,xx=np.indices(z.shape); c=(np.array(z.shape)-1)/2; r=np.hypot(xx-c[1],yy-c[0])
    ann=(r>=5.5)&(r<=7.5)&np.isfinite(z)
    bg=float(np.nanmedian(z[ann])); return z-bg,bg

def flux(z,rmax):
    yy,xx=np.indices(z.shape); c=(np.array(z.shape)-1)/2; r=np.hypot(xx-c[1],yy-c[0]); m=(r<=rmax)&np.isfinite(z)
    return float(np.nansum(z[m]))

def fit_scale(event,ref,rmax=4.2):
    yy,xx=np.indices(event.shape); c=(np.array(event.shape)-1)/2; r=np.hypot(xx-c[1],yy-c[0]); m=(r<=rmax)&np.isfinite(event)&np.isfinite(ref)
    X=np.column_stack([ref[m],np.ones(np.sum(m))]); y=event[m]; coef=np.linalg.lstsq(X,y,rcond=None)[0]; pred=coef[0]*ref+coef[1]
    resid=event-pred
    # normalized shape residual relative to event source signal, not per-pixel noise
    denom=max(np.sqrt(np.nansum((event[m]-np.nanmedian(event[m]))**2)),1e-12)
    nr=float(np.sqrt(np.nansum(resid[m]**2))/denom)
    corr=float(np.corrcoef(event[m],ref[m])[0,1]) if np.std(event[m])>0 and np.std(ref[m])>0 else np.nan
    return float(coef[0]),float(coef[1]),nr,corr,resid,m

def diff_template(event,ref,rmax=4.2):
    diff=event-ref; yy,xx=np.indices(event.shape); c=(np.array(event.shape)-1)/2; r=np.hypot(xx-c[1],yy-c[0]); m=(r<=rmax)&np.isfinite(diff)&np.isfinite(ref)
    # baseline source shape after removing a local core median floor
    t=ref.copy(); outer=(r>=4.5)&(r<=6.5)&np.isfinite(ref); floor=float(np.nanmedian(ref[outer])); t=t-floor
    den=float(np.sum(t[m]*t[m])); beta=float(np.sum(diff[m]*t[m])/den) if den>0 else np.nan
    model=beta*t; rem=diff-model
    norm=float(np.sqrt(np.sum(rem[m]**2))/max(np.sqrt(np.sum(diff[m]**2)),1e-12))
    corr=float(np.corrcoef(diff[m],t[m])[0,1]) if np.std(diff[m])>0 and np.std(t[m])>0 else np.nan
    # cosmic-ray diagnostic: how much of positive difference flux sits in brightest pixel / central 1px region
    pos=np.clip(diff,0,None); core=(r<=4.2)&np.isfinite(pos); pos_sum=float(np.sum(pos[core])); maxfrac=float(np.max(pos[core])/pos_sum) if pos_sum>0 else np.nan
    return {'difference_template_scale':beta,'difference_template_residual_fraction':norm,'difference_template_correlation':corr,'positive_difference_brightest_pixel_fraction':maxfrac}

def main():
    base=json.loads(RES.read_text()); cube=np.load(NPZ)['stamps']; survivors=json.loads(SURV.read_text())['survivors']
    ra0=float(base['target']['ra']); de0=float(base['target']['dec']); routes={int(g):int(v['k']) for g,v in base['routes'].items()}; hs=b.epoch_headers(routes)
    origins=[]
    for q in hs:
        x,y=b.pix(q,ra0,de0); origins.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
    rows=[]
    for s in survivors:
        ra=float(s['ra']); dec=float(s['dec']); e=int(s['event_epoch']); g=e%4; peers=[p for p in range(g,16,4) if p!=e]
        cuts={}; bgs={}
        for p in [e]+peers:
            px,py=hs[p].w.world_to_pixel_values(ra,dec); x=float(px)-origins[p][0]; y=float(py)-origins[p][1]
            z=aligned_cutout(cube[p],x,y); z,bg=bgsub(z); cuts[p]=z; bgs[p]=bg
        ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0); event=cuts[e]
        scale,offset,nres,corr,resid,mask=fit_scale(event,ref)
        conc_event=flux(event,1.5)/max(flux(event,4.0),1e-12); conc_ref=flux(ref,1.5)/max(flux(ref,4.0),1e-12)
        # estimate ordinary same-dither shape mismatch by fitting each peer to median of the other two
        peer_tests=[]
        for p in peers:
            others=[q for q in peers if q!=p]; pref=np.nanmedian(np.stack([cuts[q] for q in others]),axis=0)
            a,c,nr,co,_,_=fit_scale(cuts[p],pref)
            peer_tests.append({'epoch':p,'scale':a,'normalized_residual':nr,'correlation':co})
        peer_res=np.array([q['normalized_residual'] for q in peer_tests],float); med=float(np.nanmedian(peer_res)); mad=float(1.4826*np.nanmedian(np.abs(peer_res-med))); zshape=float((nres-med)/max(mad,0.01))
        row={'ra':ra,'dec':dec,'event_epoch':e,'dither_group':g,'peer_epochs':peers,'event_background':bgs[e],
             'event_to_reference_scale':scale,'event_fit_offset':offset,'event_normalized_shape_residual':nres,'event_reference_correlation':corr,
             'event_shape_residual_z_vs_peers':zshape,'event_core_concentration_r1p5_over_r4':float(conc_event),'reference_core_concentration_r1p5_over_r4':float(conc_ref),
             'core_concentration_ratio_event_over_ref':float(conc_event/conc_ref) if conc_ref!=0 else None,'peer_shape_tests':peer_tests}
        row.update(diff_template(event,ref)); rows.append(row)
    out={'success':True,'note':'same-dither subpixel-aligned science-pixel PSF diagnostic; lower residual and high correlation support, but do not prove, astrophysical point-source variability','events':rows}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
