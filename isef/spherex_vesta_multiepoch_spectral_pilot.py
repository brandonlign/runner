#!/usr/bin/env python3
"""Exploratory SPHEREx/Vesta multi-epoch spectral-photometry feasibility.
Motivated by the first June-only pilot, which had excellent S/N but only four wavelength bins.
This is a new feasibility test, not a rescue of a frozen discovery result and not a discovery search.
"""
from pathlib import Path
import io,json,urllib.request
import numpy as np
from astroquery.ipac.irsa.most import Most
from astropy.io import fits
from astropy.wcs import WCS
OUT=Path('results/spherex_vesta_multiepoch_spectral_pilot.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
MONTHS=[('2025-06-01','2025-06-30'),('2025-07-01','2025-07-31'),('2025-08-01','2025-08-31'),('2026-07-01','2026-07-31')]

def nearest_wave(hdu,x,y):
    r=hdu.data[0]; xs=np.asarray(r['X'],float); ys=np.asarray(r['Y'],float); vals=np.asarray(r['VALUES'],float)
    vv=vals.reshape(len(ys),len(xs),2); ix=int(np.argmin(abs(xs-x))); iy=int(np.argmin(abs(ys-y)))
    return float(vv[iy,ix,0]),float(vv[iy,ix,1])

def one(url,ra,dec):
    cu=f'{url}?center={ra:.8f},{dec:.8f}&size=0.018'
    req=urllib.request.Request(cu,headers={'User-Agent':'ISEF-SPHEREx-Vesta-multiepoch/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: raw=r.read()
    with fits.open(io.BytesIO(raw),memmap=False) as h:
        img=np.asarray(h['IMAGE'].data,float); var=np.asarray(h['VARIANCE'].data,float); flags=np.asarray(h['FLAGS'].data)
        w=WCS(h['IMAGE'].header).celestial; x,y=w.world_to_pixel_values(ra,dec)
        yy,xx=np.indices(img.shape); rr=np.hypot(xx-x,yy-y); ap=rr<=2.0; ann=(rr>=4.0)&(rr<=7.0)
        good=np.isfinite(img)&np.isfinite(var)&(var>=0)
        if np.sum(ap&good)<5 or np.sum(ann&good)<15: raise RuntimeError('insufficient finite aperture/annulus pixels')
        bg=float(np.nanmedian(img[ann&good])); net=float(np.nansum(img[ap&good]-bg)); noise=float(np.sqrt(np.nansum(var[ap&good])))
        area_deg2=abs(np.linalg.det(w.pixel_scale_matrix)); sr=area_deg2*(np.pi/180.)**2
        jy=net*1e6*sr; jyerr=noise*1e6*sr; cw,cb=nearest_wave(h['WCS-WAVE'],x,y)
        return {'wavelength_um':cw,'bandwidth_um':cb,'flux_jy':jy,'flux_err_jy':jyerr,'snr':jy/jyerr if jyerr>0 else None,'flagged_fraction':float(np.mean(np.asarray(flags[ap],dtype=np.int64)!=0))}

def main():
    try:
        selected=[]; monthly={}
        for begin,end in MONTHS:
            q=Most.query_object(output_mode='Regular',obj_name='20000004',obs_begin=begin,obs_end=end,catalog='spherex')
            r=q.get('results') if q else None
            if r is None or len(r)==0: monthly[begin[:7]]=0; continue
            order=np.argsort(np.asarray(r['mjd_obs'],float)); r=r[order]; monthly[begin[:7]]=len(r)
            idx=np.unique(np.linspace(0,len(r)-1,min(30,len(r)),dtype=int))
            for i in idx: selected.append((begin[:7],r[i]))
        rows=[]; failures=[]
        for month,row in selected:
            try:
                p=one(str(row['image_url']),float(row['ra_obj']),float(row['dec_obj']))
                p.update({'month':month,'mjd':float(row['mjd_obs']),'image_id':str(row['Image_ID'])}); rows.append(p)
            except Exception as e: failures.append({'month':month,'error':f'{type(e).__name__}: {e}'})
        good=[x for x in rows if x['wavelength_um'] is not None and x['snr'] is not None and np.isfinite(x['snr'])]
        wav=np.asarray([x['wavelength_um'] for x in good],float); sn=np.asarray([x['snr'] for x in good],float)
        bins=len(set(round(float(x),2) for x in wav)); hi=int(np.sum(sn>=10)); wr=[float(wav.min()),float(wav.max())] if len(wav) else [None,None]
        per_month={m:{'n':sum(x['month']==m for x in good),'wave_bins':len(set(round(float(x['wavelength_um']),2) for x in good if x['month']==m))} for m in monthly}
        status='PASS' if len(good)>=60 and hi>=40 and bins>=12 and wr[1]-wr[0]>=2.0 else 'FAIL'
        out={'success':True,'science_status':status,'monthly_archive_frames':monthly,'attempted':len(selected),'usable':len(good),'snr_ge_10':hi,'unique_wave_bins_0p01um':bins,'wavelength_range_um':wr,'median_snr':float(np.median(sn)) if len(sn) else None,'per_month':per_month,'rows':sorted(good,key=lambda x:(x['wavelength_um'],x['mjd'])),'failures':failures,'interpretation':'Multi-epoch feasibility only. Generic SPHEREx asteroid spectroscopy is acknowledged mission-team territory; any future project needs a distinct science claim.'}
    except Exception as e: out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
