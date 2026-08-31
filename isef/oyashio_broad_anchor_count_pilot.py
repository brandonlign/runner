#!/usr/bin/env python3
"""External-only pilot for a disrupting-GC-compatible source-anchor family.

Purpose: quantify whether a broad *pre-morphology* source selection reduces the
trial count enough to make a GC-anchored thin-stream search plausible. The
known Oyashio track is used only after the full source catalog and photometric
anchor lists are generated, for diagnostic nearest-distance reporting.

Allowed pixels: GO-16890 UGC9050-DW1 combined HAP/DRC F814W + F555W only.
Forbidden: every MATLAS Table-A.1 target and both sealed final-null fields.

No ordinary-GC shape/roundness/sharpness/concentration/ellipticity or formal
magnitude-uncertainty cut is applied: Holm et al. report that such cuts reject
the presumed disrupting Oyashio progenitor.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astroquery.mast import Observations
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
import sep
import requests

OUT=Path('results/oyashio_broad_anchor_count_pilot');OUT.mkdir(parents=True,exist_ok=True)
DL=OUT/'download';DL.mkdir(exist_ok=True)
PROGRAM='16890';TARGET='UGC9050-DW1'
FILTERS=('F814W','F555W')
EXPECTED={
 'F814W':'hst_16890_03_acs_wfc_f814w_jesd03_drc.fits',
 'F555W':'hst_16890_03_acs_wfc_f555w_jesd03_drc.fits',
}
BROAD_SIGMA_PX=32.0
DETECT_SIGMA=3.0
MINAREA=5
APER_R_PX=3.0
# External Fielder GC box; a second deliberately wider diagnostic box is fixed
# now to absorb aperture-method / disrupted-profile systematics without any
# morphology veto. Neither box is selected after seeing Oyashio recovery.
STRICT_COLOR=(0.5,1.5)
STRICT_I=(20.35,24.61)
BROAD_COLOR=(0.3,1.7)
BROAD_I=(19.5,25.5)
TRACK_FILE=Path('oyashio_published_truth_track.csv')


def q(filter_name):
    assert TARGET=='UGC9050-DW1' and not TARGET.upper().startswith('MATLAS')
    obs=Observations.query_criteria(obs_collection='HST',proposal_id=PROGRAM,
        instrument_name='ACS/WFC',target_name=TARGET,filters=filter_name)
    if not len(obs): raise RuntimeError(f'No {filter_name} observation')
    prod=Observations.get_product_list(obs);rows=[]
    for r in prod:
        fn=str(r['productFilename']) if 'productFilename' in prod.colnames else ''
        sub=str(r['productSubGroupDescription']) if 'productSubGroupDescription' in prod.colnames else ''
        if sub.upper()!='DRC' or not fn.endswith('_drc.fits'): continue
        if f'_acs_wfc_{filter_name.lower()}_' not in fn: continue
        rows.append({'filename':fn,'dataURI':str(r['dataURI'])})
    uniq=sorted({z['filename']:z for z in rows}.values(),key=lambda z:(len(z['filename']),z['filename']))
    want=EXPECTED[filter_name]
    if want not in {z['filename'] for z in uniq}:
        raise RuntimeError(f'Expected combined {filter_name} missing: {[z["filename"] for z in uniq]}')
    return next(z for z in uniq if z['filename']==want)


def dl(row):
    p=DL/row['filename']
    if p.exists() and p.stat().st_size>0:return p
    url='https://mast.stsci.edu/api/v0.1/Download/file'
    with requests.get(url,params={'uri':row['dataURI']},stream=True,timeout=(20,180)) as rr:
        rr.raise_for_status()
        with p.open('wb') as f:
            for c in rr.iter_content(1024*1024):
                if c:f.write(c)
    return p


def load(path):
    with fits.open(path,memmap=False) as h:
        idx=next(i for i,hd in enumerate(h) if getattr(hd,'data',None) is not None and np.ndim(hd.data)==2)
        arr=np.asarray(h[idx].data,dtype=np.float32);hdr=h[idx].header.copy();ph=h[0].header.copy()
    w=WCS(hdr,relax=True).celestial
    meta={'science_hdu':idx,'shape':list(arr.shape),'exptime_s':float(hdr.get('EXPTIME',ph.get('EXPTIME',np.nan))),
          'bunit':str(hdr.get('BUNIT',ph.get('BUNIT',''))),'date_obs':str(ph.get('DATE-OBS',hdr.get('DATE-OBS',''))),
          'photflam':float(hdr.get('PHOTFLAM',ph.get('PHOTFLAM',np.nan))),
          'photplam':float(hdr.get('PHOTPLAM',ph.get('PHOTPLAM',np.nan)))}
    return arr,w,meta


def robust_sigma(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)];m=np.median(x);mad=np.median(np.abs(x-m));return max(1.4826*mad,1e-12)


def prep_detection(a):
    finite=np.isfinite(a);zero=(a==0)&finite
    if zero.mean()>0.005:finite &= ~zero
    med=float(np.median(a[finite]));fill=np.where(finite,a,med).astype(np.float32)
    resid=(fill-gaussian_filter(fill,BROAD_SIGMA_PX,mode='nearest')).astype(np.float32)
    sig=robust_sigma(resid[finite]);return resid,finite,sig


def ab_zp(meta):
    # Header PHOTFLAM/PHOTPLAM gives a fully local reproducible AB zero point.
    # Colors below are then converted to the broad external GC window by a
    # fixed ACS Vega-AB offset approximation; the pilot reports both raw AB
    # quantities and the converted values so this approximation is auditable.
    f=meta['photflam'];p=meta['photplam']
    if not np.isfinite(f) or not np.isfinite(p) or f<=0 or p<=0: return None
    return -2.5*math.log10(f)-5*math.log10(p)-2.408

# ACS/WFC approximate AB minus VEGAMAG offsets at these filters. Fixed before
# execution; a later production detector must replace these with STScI-date
# zero points, but this count pilot is intentionally tolerant via BROAD box.
AB_MINUS_VEGA={'F555W':0.02,'F814W':0.44}


def mag_from_flux(flux,zp):
    out=np.full(len(flux),np.nan,float);g=np.asarray(flux)>0;out[g]=zp-2.5*np.log10(np.asarray(flux)[g]);return out


def truth_dense():
    pts=[]
    for line in TRACK_FILE.read_text().splitlines():
        if not line.strip() or line.startswith('#') or line.lower().startswith('x,'):continue
        pts.append(tuple(map(float,line.split(','))))
    p=np.asarray(pts,float);d=[]
    for a,b in zip(p[:-1],p[1:]):
        n=max(2,int(np.ceil(np.hypot(*(b-a))))+1)
        d.extend(a*(1-t)+b*t for t in np.linspace(0,1,n,endpoint=False))
    d.append(p[-1]);return p,np.asarray(d,float)


def nearest_reports(x,y,strict,broad):
    raw,dense=truth_dense();allxy=np.c_[x,y];tree=cKDTree(allxy)
    out={}
    for name,mask in [('all_detected',np.ones(len(x),bool)),('strict_photometric',strict),('broad_photometric',broad)]:
        ii=np.where(mask)[0]
        if not len(ii):out[name]={'n':0};continue
        tt=cKDTree(allxy[ii])
        ep=[]
        for k,z in enumerate((raw[0],raw[-1])):
            dd,j=tt.query(z);ep.append({'endpoint_index':k,'distance_px':float(dd),'source_index':int(ii[int(j)])})
        td,_=cKDTree(dense).query(allxy[ii]);j=int(np.argmin(td))
        out[name]={'n':int(len(ii)),'nearest_to_endpoints':ep,
                   'source_nearest_any_clicked_track_point':{'distance_px':float(td[j]),'source_index':int(ii[j])}}
    return out


def main():
    rows={f:q(f) for f in FILTERS};paths={f:dl(rows[f]) for f in FILTERS}
    a814,w814,m814=load(paths['F814W']);a555,w555,m555=load(paths['F555W'])
    r814,finite,sig=prep_detection(a814)
    objs=sep.extract(np.ascontiguousarray(r814,dtype=np.float32),DETECT_SIGMA*sig,minarea=MINAREA,mask=~finite)
    x=np.asarray(objs['x'],float);y=np.asarray(objs['y'],float)
    # F814 residual-aperture flux.
    f814,_,_=sep.sum_circle(np.ascontiguousarray(r814,dtype=np.float32),x,y,APER_R_PX,mask=~finite)
    # WCS-project detection coordinates into F555W, then matched residual aperture.
    sky=w814.pixel_to_world(x,y);x5,y5=w555.world_to_pixel(sky)
    r555,finite5,sig5=prep_detection(a555)
    in5=(x5>=APER_R_PX)&(x5<a555.shape[1]-APER_R_PX)&(y5>=APER_R_PX)&(y5<a555.shape[0]-APER_R_PX)
    f555=np.full(len(x),np.nan,float)
    if np.any(in5):
        vv,_,_=sep.sum_circle(np.ascontiguousarray(r555,dtype=np.float32),x5[in5],y5[in5],APER_R_PX,mask=~finite5)
        f555[in5]=vv
    zp814=ab_zp(m814);zp555=ab_zp(m555)
    if zp814 is None or zp555 is None:raise RuntimeError('Missing PHOTFLAM/PHOTPLAM')
    mab814=mag_from_flux(f814,zp814);mab555=mag_from_flux(f555,zp555)
    # Convert approximate AB to Vega only for this tolerant source-count pilot.
    mi=mab814-AB_MINUS_VEGA['F814W'];mv=mab555-AB_MINUS_VEGA['F555W'];color=mv-mi
    strict=np.isfinite(color)&np.isfinite(mi)&(color>STRICT_COLOR[0])&(color<STRICT_COLOR[1])&(mi>STRICT_I[0])&(mi<STRICT_I[1])
    broad=np.isfinite(color)&np.isfinite(mi)&(color>BROAD_COLOR[0])&(color<BROAD_COLOR[1])&(mi>BROAD_I[0])&(mi<BROAD_I[1])
    near=nearest_reports(x,y,strict,broad)
    # Add photometry for reported nearest source IDs.
    for block in near.values():
        if 'nearest_to_endpoints' in block:
            for z in block['nearest_to_endpoints']:
                j=z['source_index'];z.update({'x_px':float(x[j]),'y_px':float(y[j]),'i_vega_approx':float(mi[j]) if np.isfinite(mi[j]) else None,
                    'v_minus_i_approx':float(color[j]) if np.isfinite(color[j]) else None,'a_px':float(objs['a'][j]),'b_px':float(objs['b'][j])})
        if 'source_nearest_any_clicked_track_point' in block:
            z=block['source_nearest_any_clicked_track_point'];j=z['source_index'];z.update({'x_px':float(x[j]),'y_px':float(y[j]),
                'i_vega_approx':float(mi[j]) if np.isfinite(mi[j]) else None,'v_minus_i_approx':float(color[j]) if np.isfinite(color[j]) else None,
                'a_px':float(objs['a'][j]),'b_px':float(objs['b'][j])})
    rep={'role':'external positive-control broad-anchor count pilot only','matlas_target_science_values_opened':False,
         'final_null_science_values_opened':False,'information_barrier':'Only GO-16890 UGC9050-DW1 F814W+F555W combined DRC opened',
         'detection':{'broad_sigma_px':BROAD_SIGMA_PX,'detect_sigma':DETECT_SIGMA,'minarea':MINAREA,'aperture_radius_px':APER_R_PX,
                      'f814_resid_sigma':sig,'f555_resid_sigma':sig5,'source_n':int(len(objs))},
         'photometric_boxes':{'strict_external':{'color_v_minus_i':STRICT_COLOR,'i_mag':STRICT_I,'n':int(strict.sum())},
                              'broad_external':{'color_v_minus_i':BROAD_COLOR,'i_mag':BROAD_I,'n':int(broad.sum())}},
         'morphology_vetoes_applied':False,'products':{f:{'filename':rows[f]['filename'],**({'meta':m814} if f=='F814W' else {'meta':m555})} for f in FILTERS},
         'photometric_calibration':{'method':'PHOTFLAM/PHOTPLAM AB ZP then fixed approximate ACS AB-minus-Vega offsets for count pilot',
                                    'ab_zp':{'F814W':zp814,'F555W':zp555},'ab_minus_vega':AB_MINUS_VEGA},
         'post_generation_truth_diagnostic':near}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    # Remove control FITS from artifact/state.
    for pth in paths.values():pth.unlink(missing_ok=True)
    print(json.dumps({'source_n':len(objs),'strict_anchor_n':int(strict.sum()),'broad_anchor_n':int(broad.sum()),'truth_diagnostic':near},indent=2))

if __name__=='__main__':main()
