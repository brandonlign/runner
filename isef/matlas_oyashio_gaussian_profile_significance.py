#!/usr/bin/env python3
"""Paper-motivated Gaussian transverse-profile external-control diagnostic.

Allowed image data: only published Oyashio UGC9050-Dw1 GO-16890 F814W combined
HAP/DRC. No MATLAS Table-A.1 science target and no MATLAS null-control image is
queried/opened.

Holm et al. (2026) measure Oyashio with a Gaussian transverse profile plus local
background. This diagnostic tests that *pre-existing physical model*, not an
arbitrary detector sweep. The source-frozen Gaussian scales are derived from
published w_{+-sigma}=72.3 +/- 8.9 pc, distance 35.2 Mpc, 0.05 arcsec/pixel,
and ~0.1 arcsec HST PSF FWHM. The labelled track is compared with deterministic
translated copies of the identical curved track across the usable field.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates, binary_dilation
from skimage.morphology import disk
import matlas_oyashio_blind_detector_pilot as p

OUT=Path('results/matlas_oyashio_gaussian_profile_significance');OUT.mkdir(parents=True,exist_ok=True)
DIST_MPC=35.2
PIX_ARCSEC=0.05
PSF_FWHM_ARCSEC=0.10
W_PM_SIGMA_PC=72.3
W_PM_SIGMA_ERR_PC=8.9
TRACK_STEP_PX=2.0
TRANSVERSE_MAX_PX=25
NULL_TRANSLATIONS_N=1200
MIN_GEOMETRY_VALID_FRACTION=0.90
MIN_OFFSET_LONGITUDINAL_VALID_FRACTION=0.80
RNG_SEED=20260831

PC_PER_PX=0.242406840554768 * DIST_MPC
PSF_SIGMA_PX=(PSF_FWHM_ARCSEC/PIX_ARCSEC)/2.354820045
# Published width is full mu-sigma to mu+sigma = 2 intrinsic Gaussian sigma.
def observed_sigma_px(full_width_pc):
    intrinsic=(full_width_pc/2.0)/PC_PER_PX
    return math.sqrt(intrinsic*intrinsic+PSF_SIGMA_PX*PSF_SIGMA_PX)
SIGMA_GRID_PX=(
    observed_sigma_px(W_PM_SIGMA_PC-W_PM_SIGMA_ERR_PC),
    observed_sigma_px(W_PM_SIGMA_PC),
    observed_sigma_px(W_PM_SIGMA_PC+W_PM_SIGMA_ERR_PC),
)
OFFSETS=np.arange(-TRANSVERSE_MAX_PX,TRANSVERSE_MAX_PX+1,dtype=float)


def preprocess(arr):
    finite=np.isfinite(arr);zero=(arr==0)&finite
    if zero.mean()>0.005:finite &= ~zero
    med=float(np.median(arr[finite]));fill=np.where(finite,arr,med).astype(np.float32)
    broad=gaussian_filter(fill,p.BROAD_SIGMA_PX,mode='nearest');resid=(fill-broad).astype(np.float32)
    sig=p.robust_sigma(resid[finite]);norm=(resid/sig).astype(np.float32)
    small=gaussian_filter(norm,1.0,mode='nearest');bright=small>p.BRIGHT_MASK_SIGMA
    bright=binary_dilation(bright,structure=disk(p.BRIGHT_MASK_DILATE_PX));valid=finite&~bright
    e=p.EDGE_PX;valid[:e,:]=False;valid[-e:,:]=False;valid[:,:e]=False;valid[:,-e:]=False
    return norm,valid,{'resid_sigma_native':sig,'analysis_valid_fraction':float(valid.mean()),'bright_mask_fraction':float(bright.mean())}


def track_geometry():
    raw,_=p.truth_points_dense();d=np.sqrt(np.sum(np.diff(raw,axis=0)**2,axis=1));ss0=np.r_[0,np.cumsum(d)]
    ss=np.arange(0,ss0[-1]+1e-9,TRACK_STEP_PX);x=np.interp(ss,ss0,raw[:,0]);y=np.interp(ss,ss0,raw[:,1])
    dx=np.gradient(x);dy=np.gradient(y);nn=np.maximum(np.hypot(dx,dy),1e-9);nx=-dy/nn;ny=dx/nn
    return np.c_[x,y],np.c_[nx,ny],float(ss0[-1])


def sample_mean_profile(img,valid,track,normals,dx=0,dy=0):
    xx=track[:,0,None]+dx+normals[:,0,None]*OFFSETS[None,:]
    yy=track[:,1,None]+dy+normals[:,1,None]*OFFSETS[None,:]
    vals=map_coordinates(img,[yy.ravel(),xx.ravel()],order=1,mode='constant',cval=np.nan).reshape(xx.shape)
    vm=map_coordinates(valid.astype(np.float32),[yy.ravel(),xx.ravel()],order=0,mode='constant',cval=0).reshape(xx.shape)>0.5
    vals[~vm]=np.nan
    total_valid=float(vm.mean())
    if total_valid<MIN_GEOMETRY_VALID_FRACTION:return None
    n=np.sum(np.isfinite(vals),axis=0);good=n>=MIN_OFFSET_LONGITUDINAL_VALID_FRACTION*len(track)
    if good.mean()<0.85:return None
    prof=np.full(len(OFFSETS),np.nan,float);prof[good]=np.nanmean(vals[:,good],axis=0)
    return prof,total_valid,n


def fit_profile(profile,sigma):
    good=np.isfinite(profile);x=OFFSETS[good];y=profile[good]
    g=np.exp(-0.5*(x/sigma)**2)
    # Gaussian amplitude plus local linear nuisance background, matching the
    # published transverse-profile model class. Center is fixed at zero because
    # the labelled positive track / translated null track defines the center.
    X=np.c_[np.ones(len(x)),x,g]
    beta=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@beta;dof=max(len(y)-X.shape[1],1)
    s2=float(np.sum(res*res)/dof);cov=s2*np.linalg.inv(X.T@X);ase=math.sqrt(max(float(cov[2,2]),1e-30))
    amp=float(beta[2]);return {'amplitude':amp,'formal_amp_se':ase,'formal_amp_snr':amp/ase,
                              'intercept':float(beta[0]),'linear_slope':float(beta[1]),'resid_rms':math.sqrt(s2),'offset_n':int(len(y))}


def translation_bounds(track,img_shape):
    # Runtime-only repair: use the actual loaded image dimensions. The original
    # source incorrectly referenced nonexistent p.NX/p.NY constants. This does
    # not alter any science grid, statistic, mask, random seed, or null rule.
    ny,nx=img_shape
    m=TRANSVERSE_MAX_PX+3;xmin=track[:,0].min();xmax=track[:,0].max();ymin=track[:,1].min();ymax=track[:,1].max()
    return int(math.ceil(m-xmin)),int(math.floor(nx-1-m-xmax)),int(math.ceil(m-ymin)),int(math.floor(ny-1-m-ymax))


def robust_z(v,a):
    a=np.asarray(a,float);med=float(np.median(a));mad=float(np.median(np.abs(a-med)));scale=max(1.4826*mad,1e-12)
    return (float(v)-med)/scale,med,scale


def main():
    rows=p.query_products();row=next(r for r in rows if r['filename']==p.EXPECTED_COMBINED)
    path=p.download_one(row);arr,hdr=p.load_sci(path);img,valid,meta=preprocess(arr);track,normals,length=track_geometry()
    truth_prof=sample_mean_profile(img,valid,track,normals)
    if truth_prof is None:raise RuntimeError('Published track has insufficient valid geometry')
    truth={str(i):fit_profile(truth_prof[0],s) for i,s in enumerate(SIGMA_GRID_PX)}
    dxlo,dxhi,dylo,dyhi=translation_bounds(track,img.shape);rng=np.random.default_rng(RNG_SEED);nullfits=[];attempts=0
    while len(nullfits)<NULL_TRANSLATIONS_N and attempts<NULL_TRANSLATIONS_N*80:
        attempts+=1;dx=int(rng.integers(dxlo,dxhi+1));dy=int(rng.integers(dylo,dyhi+1))
        if abs(dx)<=50 and abs(dy)<=50:continue
        sp=sample_mean_profile(img,valid,track,normals,dx,dy)
        if sp is None:continue
        nullfits.append({'dx':dx,'dy':dy,'fits':{str(i):fit_profile(sp[0],s) for i,s in enumerate(SIGMA_GRID_PX)}})
    if len(nullfits)<NULL_TRANSLATIONS_N:raise RuntimeError(f'Only {len(nullfits)} usable translations')
    results=[]
    for i,s in enumerate(SIGMA_GRID_PX):
        k=str(i);ta=truth[k]['amplitude'];ts=truth[k]['formal_amp_snr'];amps=[z['fits'][k]['amplitude'] for z in nullfits];snrs=[z['fits'][k]['formal_amp_snr'] for z in nullfits]
        za,amed,asc=robust_z(ta,amps);zs,smed,ssc=robust_z(ts,snrs)
        results.append({'sigma_px':s,'corresponding_intrinsic_full_pm_sigma_width_pc':(W_PM_SIGMA_PC-W_PM_SIGMA_ERR_PC,W_PM_SIGMA_PC,W_PM_SIGMA_ERR_PC+W_PM_SIGMA_PC)[i],
                        'truth_fit':truth[k],
                        'amplitude_null':{'median':amed,'robust_sigma':asc,'empirical_ge_fraction':float(np.mean(np.asarray(amps)>=ta)),'truth_robust_z':float(za)},
                        'formal_snr_null':{'median':smed,'robust_sigma':ssc,'empirical_ge_fraction':float(np.mean(np.asarray(snrs)>=ts)),'truth_robust_z':float(zs)}})
    rep={'role':'external positive-control Gaussian-profile diagnostic only','matlas_target_science_values_opened':False,'matlas_null_control_science_values_opened':False,
         'information_barrier':'Only GO-16890 UGC9050-DW1 F814W combined DRC opened',
         'physical_inputs':{'distance_mpc':DIST_MPC,'pixel_arcsec':PIX_ARCSEC,'psf_fwhm_arcsec':PSF_FWHM_ARCSEC,'published_full_pm_sigma_width_pc':W_PM_SIGMA_PC,'published_width_err_pc':W_PM_SIGMA_ERR_PC,'pc_per_px':PC_PER_PX,'psf_sigma_px':PSF_SIGMA_PX},
         'frozen_grid':{'observed_gaussian_sigma_px':list(SIGMA_GRID_PX),'transverse_offsets_px':[int(OFFSETS[0]),int(OFFSETS[-1])],'track_step_px':TRACK_STEP_PX,'null_translations_n':NULL_TRANSLATIONS_N,'local_nuisance_background':'constant + linear slope'},
         'image':{'filename':row['filename'],'header':hdr,'preprocess':meta},'track_length_px':length,'translation_attempts':attempts,'results':results}
    path.unlink(missing_ok=True);(OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps([{'sigma_px':x['sigma_px'],'amp_z':x['amplitude_null']['truth_robust_z'],'amp_p':x['amplitude_null']['empirical_ge_fraction'],'snr':x['truth_fit']['formal_amp_snr'],'snr_z':x['formal_snr_null']['truth_robust_z'],'snr_p':x['formal_snr_null']['empirical_ge_fraction']} for x in results],indent=2))
if __name__=='__main__':main()
