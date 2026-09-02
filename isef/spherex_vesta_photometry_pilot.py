#!/usr/bin/env python3
"""Exploratory SPHEREx/Vesta positive-control photometry pilot.
Downloads QR2 cutouts at MOST-predicted positions and performs simple local-background aperture photometry.
This is a feasibility/positive-control test, not a discovery search."""
from pathlib import Path
import io,json,urllib.request
import numpy as np
from astroquery.ipac.irsa.most import Most
from astropy.io import fits
from astropy.wcs import WCS
OUT=Path('results/spherex_vesta_photometry_pilot.json'); OUT.parent.mkdir(parents=True,exist_ok=True)

def nearest_wave(hdu,x,y):
    try:
        r=hdu.data[0]; xs=np.asarray(r['X'],float); ys=np.asarray(r['Y'],float); vals=np.asarray(r['VALUES'],float)
        vv=vals.reshape(len(ys),len(xs),2)
        ix=int(np.argmin(abs(xs-x))); iy=int(np.argmin(abs(ys-y)))
        return float(vv[iy,ix,0]),float(vv[iy,ix,1])
    except Exception:
        return None,None

def one(url,ra,dec):
    cu=f'{url}?center={ra:.8f},{dec:.8f}&size=0.018'
    req=urllib.request.Request(cu,headers={'User-Agent':'ISEF-SPHEREx-Vesta-pilot/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: raw=r.read()
    with fits.open(io.BytesIO(raw),memmap=False) as h:
        img=np.asarray(h['IMAGE'].data,float); var=np.asarray(h['VARIANCE'].data,float); flags=np.asarray(h['FLAGS'].data)
        w=WCS(h['IMAGE'].header).celestial; x,y=w.world_to_pixel_values(ra,dec)
        yy,xx=np.indices(img.shape); rr=np.hypot(xx-x,yy-y)
        ap=rr<=2.0; ann=(rr>=4.0)&(rr<=7.0)
        good=np.isfinite(img)&np.isfinite(var)&(var>=0)
        if np.sum(ap&good)<5 or np.sum(ann&good)<15: raise RuntimeError('insufficient finite aperture/annulus pixels')
        bg=float(np.nanmedian(img[ann&good])); net=float(np.nansum(img[ap&good]-bg)); noise=float(np.sqrt(np.nansum(var[ap&good])))
        # Convert summed MJy/sr to Jy using local WCS pixel solid angle.
        area_deg2=abs(np.linalg.det(w.pixel_scale_matrix)); sr=area_deg2*(np.pi/180.)**2
        jy=net*1e6*sr; jyerr=noise*1e6*sr
        cw,cb=nearest_wave(h['WCS-WAVE'],x,y)
        af=np.asarray(flags[ap],dtype=np.int64); nonzero_frac=float(np.mean(af!=0))
        return {'wavelength_um':cw,'bandwidth_um':cb,'flux_jy':jy,'flux_err_jy':jyerr,'snr':jy/jyerr if jyerr>0 else None,'background_mjysr':bg,'aperture_flagged_fraction':nonzero_frac,'cutout_bytes':len(raw)}

def main():
    try:
        q=Most.query_object(output_mode='Regular',obj_name='20000004',obs_begin='2025-06-01',obs_end='2025-06-30',catalog='spherex')
        r=q['results']; order=np.argsort(np.asarray(r['mjd_obs'],float)); r=r[order]
        # Deterministic evenly spaced subset, max 42 frames.
        idx=np.unique(np.linspace(0,len(r)-1,min(42,len(r)),dtype=int))
        rows=[]; failures=[]
        for i in idx:
            row=r[i]
            try:
                p=one(str(row['image_url']),float(row['ra_obj']),float(row['dec_obj']))
                p.update({'mjd':float(row['mjd_obs']),'image_id':str(row['Image_ID'])})
                rows.append(p)
            except Exception as e: failures.append({'index':int(i),'error':f'{type(e).__name__}: {e}'})
        good=[x for x in rows if x['wavelength_um'] is not None and x['snr'] is not None and np.isfinite(x['snr'])]
        wav=np.array([x['wavelength_um'] for x in good]); sn=np.array([x['snr'] for x in good]); flux=np.array([x['flux_jy'] for x in good])
        # Feasibility gate only: enough wavelength-diverse, positive high-S/N measurements.
        high=int(np.sum(sn>=10)); wrange=[float(np.min(wav)),float(np.max(wav))] if len(wav) else [None,None]
        qtiles=len(set(round(x['wavelength_um'],2) for x in good)) if good else 0
        status='PASS' if len(good)>=20 and high>=12 and qtiles>=12 and wrange[1]-wrange[0]>=0.5 else 'FAIL'
        out={'success':True,'science_status':status,'queried_frames':len(r),'attempted':len(idx),'successful_photometry':len(rows),'usable_with_wave':len(good),'snr_ge_10':high,'unique_wave_bins_0p01um':qtiles,'wavelength_range_um':wrange,'median_snr':float(np.median(sn)) if len(sn) else None,'median_flux_jy':float(np.median(flux)) if len(flux) else None,'rows':sorted(good,key=lambda x:x['wavelength_um']),'failures':failures,'interpretation':'Positive-control feasibility only; no asteroid novelty/discovery claim.'}
    except Exception as e: out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
