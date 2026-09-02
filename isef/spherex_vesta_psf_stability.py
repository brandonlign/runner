#!/usr/bin/env python3
"""Frozen SPHEREx/Vesta PSF stability positive-control gate.
See brandonlign/isef research/SPHEREX_VESTA_PSF_STABILITY_PREREG_2026-09-01.md.
Aggregate/group output only; no discovery search.
"""
from pathlib import Path
import json, urllib.request
import numpy as np
from astroquery.ipac.irsa.most import Most
from spexpi.spherex_pipeline import PipelineConfig, process_cutout_row, measure_cutout_photometry

OUT=Path('results/spherex_vesta_psf_stability.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
CACHE=Path('/tmp/spherex_vesta_psf'); CACHE.mkdir(parents=True,exist_ok=True)

def download(url,ra,dec,path):
    cu=f'{url}?center={ra:.8f},{dec:.8f}&size=0.018'
    req=urllib.request.Request(cu,headers={'User-Agent':'ISEF-SPHEREx-Vesta-PSF/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r, path.open('wb') as f:f.write(r.read())

def finite(v):
    try:return float(v) if v is not None and np.isfinite(v) else None
    except Exception:return None

def main():
    try:
        q=Most.query_object(output_mode='Regular',obj_name='20000004',obs_begin='2025-06-01',obs_end='2025-06-30',catalog='spherex')
        r=q['results']; r=r[np.argsort(np.asarray(r['mjd_obs'],float))]
        cfg=PipelineConfig(photometry_method='psf',plot_spectrum=False,save_raw_measurements=False,save_manifest=False,
            download_dir=str(CACHE/'downloads'),sapm_cache_dir=str(CACHE/'sapm'),enable_psf_local_grid_search=True,
            psf_local_grid_half_range_pix=1.0,psf_local_grid_step_pix=0.25,psf_local_grid_metric='snr',
            psf_max_reduced_chi2=None,subtract_zodi=True,show_download_progress=False)
        sapm_cache={}; rows=[]; failures=[]
        for i,row in enumerate(r):
            ra=float(row['ra_obj']); dec=float(row['dec_obj']); mjd=float(row['mjd_obs']); image_id=str(row['Image_ID']); url=str(row['image_url'])
            p=CACHE/f'{i:04d}_{image_id.replace("/","_")}.fits'
            try:
                if not p.exists(): download(url,ra,dec,p)
                prepared=process_cutout_row({'local_uri':str(p),'uri':url,'cutout_index':i,'time_bounds_lower':mjd,'time_bounds_upper':mjd,'data_release':'qr2'},ra,dec,cfg)
                if prepared is None or 'image_hdu' not in prepared: raise RuntimeError(f'cutout open failed: {prepared}')
                measurements=measure_cutout_photometry(prepared,sapm_cache,cfg)
                ps=[x for x in measurements if str(x.get('photometry_method','')).lower()=='psf']
                if not ps: raise RuntimeError(f'no PSF measurement; n={len(measurements)}')
                m=ps[0]; flux=finite(m.get('flux')); err=finite(m.get('err')); status=str(m.get('psf_status','unknown'))
                rows.append({'mjd':mjd,'image_id':image_id,'wavelength_um':float(prepared['central_wavelength_um']),'detector':int(prepared['detector']),
                    'flux_jy':flux,'err_jy':err,'psf_status':status,'psf_reduced_chi2':finite(m.get('psf_reduced_chi2')),
                    'psf_n_valid':int(m['psf_n_valid']) if m.get('psf_n_valid') is not None else None,
                    'psf_fit_offset_pix':finite(m.get('psf_fit_offset_pix')),'n_bad_aperture_pixels':int(m.get('n_bad_aperture_pixels',0)),
                    'sapm_status':str(m.get('sapm_status',''))})
            except Exception as e:failures.append({'index':i,'mjd':mjd,'image_id':image_id,'error':f'{type(e).__name__}: {e}'})
        valid=[x for x in rows if x['psf_status']=='ok' and x['flux_jy'] is not None and x['err_jy'] is not None and x['flux_jy']>0 and x['err_jy']>0]
        by={}
        for x in valid:by.setdefault(round(x['wavelength_um'],2),[]).append(x)
        groups=[]; dtmax=10/(24*60)
        for wb,xs in sorted(by.items()):
            xs=sorted(xs,key=lambda z:z['mjd']); cur=[]
            for x in xs:
                if not cur or x['mjd']-cur[-1]['mjd']<=dtmax:cur.append(x)
                else:
                    if len(cur)>=3:groups.append((wb,cur))
                    cur=[x]
            if len(cur)>=3:groups.append((wb,cur))
        gout=[]
        for wb,g in groups:
            f=np.asarray([x['flux_jy'] for x in g]); cv=float(np.std(f,ddof=1)/np.mean(f)) if np.mean(f)>0 else None
            gout.append({'wavelength_um_rounded':wb,'n':len(g),'duration_min':float((g[-1]['mjd']-g[0]['mjd'])*1440),'cv':cv,'mean_flux_jy':float(np.mean(f)),'min_max_ratio':float(np.min(f)/np.max(f))})
        cvs=np.asarray([g['cv'] for g in gout if g['cv'] is not None]); nw=len(set(g['wavelength_um_rounded'] for g in gout)); frac10=float(np.mean(cvs<=.10)) if len(cvs) else 0.; med=float(np.median(cvs)) if len(cvs) else None; mx=float(np.max(cvs)) if len(cvs) else None
        passed=len(gout)>=4 and nw>=2 and frac10>=.75 and med is not None and med<=.07 and mx is not None and mx<=.20
        out={'success':True,'science_status':'PASS' if passed else 'FAIL','archive_frames':len(r),'psf_rows':len(rows),'valid_psf_rows':len(valid),'failures_count':len(failures),
            'unique_valid_wavelength_bins_0p01um':len(set(round(x['wavelength_um'],2) for x in valid)),
            'valid_wavelength_range_um':[min((x['wavelength_um'] for x in valid),default=None),max((x['wavelength_um'] for x in valid),default=None)],
            'testable_groups':len(gout),'distinct_group_wavelength_bins':nw,'fraction_groups_cv_le_0p10':frac10,'median_group_cv':med,'max_group_cv':mx,
            'frozen_gate':{'groups_ge4':len(gout)>=4,'wave_bins_ge2':nw>=2,'fraction_cv_le0p10_ge0p75':frac10>=.75,'median_cv_le0p07':med is not None and med<=.07,'max_cv_le0p20':mx is not None and mx<=.20},
            'groups':gout,'rows':rows,'failures':failures[:30],'note':'Frozen PSF stability positive-control only. Wavelength comes from SPHEREx spectral WCS through process_cutout_row.'}
    except Exception as e:out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()
