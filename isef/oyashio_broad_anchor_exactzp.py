#!/usr/bin/env python3
"""Exact-zero-point repeat of the external Oyashio broad-anchor count pilot.

Identical source detection, aperture, and predeclared strict/broad photometric
boxes as oyashio_broad_anchor_count_pilot.py. The only intended change is to
replace its approximate AB-to-Vega conversion with STScI ACS date-dependent
VEGAMAG zero points via acstools.acszpt. No MATLAS science/final-null pixels.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import sep
from acstools import acszpt
import oyashio_broad_anchor_count_pilot as p

OUT=Path('results/oyashio_broad_anchor_exactzp');OUT.mkdir(parents=True,exist_ok=True)

def vega_zp(filter_name,date_obs):
    date=str(date_obs)[:10]
    t=acszpt.Query(date=date,detector='WFC',filt=filter_name).fetch()
    # acszpt tables use a VEGAmag column with a scalar Quantity value.
    col='VEGAmag'
    if col not in t.colnames: raise RuntimeError(f'VEGAmag absent from acszpt columns {t.colnames}')
    z=t[col][0]
    return float(z.value if hasattr(z,'value') else z),date

def nearest(x,y,strict,broad,mi,color,objs):
    raw,dense=p.truth_dense();xy=np.c_[x,y];out={}
    for name,mask in [('all_detected',np.ones(len(x),bool)),('strict_photometric',strict),('broad_photometric',broad)]:
        ii=np.where(mask)[0]
        if not len(ii): out[name]={'n':0};continue
        tr=cKDTree(xy[ii]);eps=[]
        for k,z in enumerate((raw[0],raw[-1])):
            d,j=tr.query(z);q=int(ii[int(j)])
            eps.append({'endpoint_index':k,'distance_px':float(d),'source_index':q,'x_px':float(x[q]),'y_px':float(y[q]),
                        'i_vega':float(mi[q]) if np.isfinite(mi[q]) else None,'v_minus_i':float(color[q]) if np.isfinite(color[q]) else None,
                        'a_px':float(objs['a'][q]),'b_px':float(objs['b'][q])})
        td,_=cKDTree(dense).query(xy[ii]);j=int(np.argmin(td));q=int(ii[j])
        out[name]={'n':int(len(ii)),'nearest_to_endpoints':eps,
                   'source_nearest_any_clicked_track_point':{'distance_px':float(td[j]),'source_index':q,'x_px':float(x[q]),'y_px':float(y[q]),
                        'i_vega':float(mi[q]) if np.isfinite(mi[q]) else None,'v_minus_i':float(color[q]) if np.isfinite(color[q]) else None,
                        'a_px':float(objs['a'][q]),'b_px':float(objs['b'][q])}}
    return out

def main():
    rows={f:p.q(f) for f in p.FILTERS};paths={f:p.dl(rows[f]) for f in p.FILTERS}
    a814,w814,m814=p.load(paths['F814W']);a555,w555,m555=p.load(paths['F555W'])
    r814,finite,sig=p.prep_detection(a814)
    objs=sep.extract(np.ascontiguousarray(r814,dtype=np.float32),p.DETECT_SIGMA*sig,minarea=p.MINAREA,mask=~finite)
    x=np.asarray(objs['x'],float);y=np.asarray(objs['y'],float)
    f814,_,_=sep.sum_circle(np.ascontiguousarray(r814,dtype=np.float32),x,y,p.APER_R_PX,mask=~finite)
    sky=w814.pixel_to_world(x,y);x5,y5=w555.world_to_pixel(sky)
    r555,finite5,sig5=p.prep_detection(a555);f555=np.full(len(x),np.nan,float)
    inside=(x5>=p.APER_R_PX)&(x5<a555.shape[1]-p.APER_R_PX)&(y5>=p.APER_R_PX)&(y5<a555.shape[0]-p.APER_R_PX)
    if np.any(inside):
        vv,_,_=sep.sum_circle(np.ascontiguousarray(r555,dtype=np.float32),x5[inside],y5[inside],p.APER_R_PX,mask=~finite5);f555[inside]=vv
    zp814,d814=vega_zp('F814W',m814['date_obs']);zp555,d555=vega_zp('F555W',m555['date_obs'])
    mi=p.mag_from_flux(f814,zp814);mv=p.mag_from_flux(f555,zp555);color=mv-mi
    strict=np.isfinite(color)&np.isfinite(mi)&(color>p.STRICT_COLOR[0])&(color<p.STRICT_COLOR[1])&(mi>p.STRICT_I[0])&(mi<p.STRICT_I[1])
    broad=np.isfinite(color)&np.isfinite(mi)&(color>p.BROAD_COLOR[0])&(color<p.BROAD_COLOR[1])&(mi>p.BROAD_I[0])&(mi<p.BROAD_I[1])
    diag=nearest(x,y,strict,broad,mi,color,objs)
    rep={'role':'external positive-control exact-zero-point broad-anchor calibration','matlas_target_science_values_opened':False,
         'final_null_science_values_opened':False,'information_barrier':'Only GO-16890 UGC9050-DW1 F814W+F555W combined DRC opened',
         'intended_change_from_pilot':'STScI acstools.acszpt date-dependent VEGAMAG zero points replace approximate AB-minus-Vega offsets; source detection/aperture/boxes unchanged',
         'detection':{'source_n':int(len(objs)),'detect_sigma':p.DETECT_SIGMA,'minarea':p.MINAREA,'aperture_radius_px':p.APER_R_PX,
                      'broad_sigma_px':p.BROAD_SIGMA_PX,'f814_resid_sigma':sig,'f555_resid_sigma':sig5},
         'zero_points':{'F814W':{'VEGAmag':zp814,'date':d814},'F555W':{'VEGAmag':zp555,'date':d555}},
         'photometric_boxes':{'strict_external':{'color_v_minus_i':p.STRICT_COLOR,'i_mag':p.STRICT_I,'n':int(strict.sum())},
                              'broad_external':{'color_v_minus_i':p.BROAD_COLOR,'i_mag':p.BROAD_I,'n':int(broad.sum())}},
         'morphology_vetoes_applied':False,'post_generation_truth_diagnostic':diag}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    for z in paths.values():z.unlink(missing_ok=True)
    print(json.dumps({'source_n':len(objs),'strict_anchor_n':int(strict.sum()),'broad_anchor_n':int(broad.sum()),'zero_points':rep['zero_points'],'truth_diagnostic':diag},indent=2))
if __name__=='__main__':main()
