#!/usr/bin/env python3
"""SPHEREx/Vesta flag-semantics quality probe.
Checks whether the earlier nonzero FLAGS values are merely SOURCE/background-mask flags or include bits the SPHEREx pipeline excludes from photometric fitting. This is a calibration/quality diagnostic only.
"""
from pathlib import Path
import io,json,urllib.request
import numpy as np
from astroquery.ipac.irsa.most import Most
from astropy.io import fits
from astropy.wcs import WCS
OUT=Path('results/spherex_vesta_flag_quality_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
# SPHEREx Explanatory Supplement: photometry-fit bad bits.
BITS={'TRANSIENT':0,'OVERFLOW':1,'SUR_ERROR':2,'PHANTOM':4,'REFERENCE':5,'NONFUNC':6,'DICHROIC':7,'MISSING_DATA':9,'HOT':10,'COLD':11,'FULLSAMPLE':12,'PHANMISS':14,'NONLINEAR':15,'PERSIST':17,'OUTLIER':20,'SOURCE':21,'HALO':28,'SATELLITE_HALO':29}
PHOT_BAD=['SUR_ERROR','NONFUNC','MISSING_DATA','HOT','COLD','NONLINEAR','PERSIST']
BG_BAD=['OVERFLOW','SUR_ERROR','NONFUNC','MISSING_DATA','HOT','COLD','NONLINEAR','PERSIST','OUTLIER','SOURCE','TRANSIENT']

def masks(vals,names):
    m=0
    for n in names:m|=(1<<BITS[n])
    return (vals.astype(np.int64)&m)!=0

def inspect(url,ra,dec):
    cu=f'{url}?center={ra:.8f},{dec:.8f}&size=0.018'; req=urllib.request.Request(cu,headers={'User-Agent':'ISEF-SPHEREx-Vesta-flags/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: raw=r.read()
    with fits.open(io.BytesIO(raw),memmap=False) as h:
        img=np.asarray(h['IMAGE'].data,float); flags=np.asarray(h['FLAGS'].data,dtype=np.int64); w=WCS(h['IMAGE'].header).celestial; x,y=w.world_to_pixel_values(ra,dec)
        yy,xx=np.indices(img.shape); rr=np.hypot(xx-x,yy-y); ap=rr<=2.0; ann=(rr>=4.0)&(rr<=7.0)
        af=flags[ap]; nf={n:int(np.sum((af&(1<<b))!=0)) for n,b in BITS.items()}
        return {'aperture_pixels':int(ap.sum()),'any_nonzero':int(np.sum(af!=0)),'photometry_bad_pixels':int(np.sum(masks(af,PHOT_BAD))),'source_flag_pixels':nf['SOURCE'],'dichroic_pixels':nf['DICHROIC'],'overflow_pixels':nf['OVERFLOW'],'transient_pixels':nf['TRANSIENT'],'per_bit_aperture_counts':nf,'annulus_pixels':int(ann.sum()),'annulus_bg_bad_pixels':int(np.sum(masks(flags[ann],BG_BAD)))}

def main():
    try:
        q=Most.query_object(output_mode='Regular',obj_name='20000004',obs_begin='2025-06-01',obs_end='2025-06-30',catalog='spherex'); r=q['results']; r=r[np.argsort(np.asarray(r['mjd_obs'],float))]
        idx=np.unique(np.linspace(0,len(r)-1,min(20,len(r)),dtype=int)); rows=[]; fails=[]
        for i in idx:
            row=r[i]
            try:
                z=inspect(str(row['image_url']),float(row['ra_obj']),float(row['dec_obj'])); z.update({'mjd':float(row['mjd_obs']),'image_id':str(row['Image_ID'])}); rows.append(z)
            except Exception as e:fails.append({'index':int(i),'error':f'{type(e).__name__}: {e}'})
        n=len(rows); zero_bad=sum(x['photometry_bad_pixels']==0 for x in rows); source_only=sum(x['photometry_bad_pixels']==0 and x['source_flag_pixels']>0 and x['dichroic_pixels']==0 and x['overflow_pixels']==0 and x['transient_pixels']==0 for x in rows)
        out={'success':True,'attempted':len(idx),'usable':n,'frames_zero_photometry_bad_pixels':zero_bad,'frames_source_only_among_checked_warning_bits':source_only,'zero_bad_fraction':zero_bad/n if n else None,'rows':rows,'failures':fails,'interpretation':'SOURCE is not a photometry-fit bad bit under official SPHEREx guidance; this probe separates it from true fit-mask bits.'}
    except Exception as e:out={'success':False,'error':f'{type(e).__name__}: {e}'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
