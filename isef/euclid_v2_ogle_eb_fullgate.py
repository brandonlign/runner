#!/usr/bin/env python3
"""Frozen Euclid Q2 v2 positive-control gate on four prospectively selected OGLE EBs.

IMPORTANT: the control IDs and all pass criteria were frozen in brandonlign/isef
commit c189453d9916db6c5582eb38eb71e451d5afdb7c before this script was created.
This is the first step in the v2 sequence that reads Euclid science flux for these
four targets. It reuses the Stage-0B detector unchanged and adds only the frozen
external phase-consistency condition.
"""
import json
from pathlib import Path
import numpy as np
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg

OUT=Path('results/euclid_v2_ogle_eb_fullgate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
THRESH=0.14011415120359302
MORPH={'control_quantile':0.95,'shape_residual_max':0.7433354680523049,'shape_correlation_min':0.6246851398220109}
PHASE_TOL=0.06
CONTROLS=[
 {'id':'OGLE-BLG-ECL-125275','ra':267.4830833333333,'dec':-30.092,'P':0.276692075,'T0':7000.24,'catalog_depth_mag':0.777},
 {'id':'OGLE-BLG-ECL-121416','ra':267.359375,'dec':-30.082833333333333,'P':0.24776450400000002,'T0':7000.15,'catalog_depth_mag':0.644},
 {'id':'OGLE-BLG-ECL-128512','ra':267.58141666666666,'dec':-30.114055555555556,'P':0.373595457,'T0':7000.0931,'catalog_depth_mag':0.621},
 {'id':'OGLE-BLG-ECL-120480','ra':267.32925,'dec':-29.78927777777778,'P':0.25851668600000005,'T0':7000.2555,'catalog_depth_mag':0.344},
]
# Exact HJD-2450000 mid-exposure values were computed metadata-only in run 33273558474.
# Recompute from the same FITS headers indirectly using the phase values frozen by refit output
# would risk duplicated time-conversion code. These HJD values are obtained by the same
# heliocentric routine in the metadata-only probe and contain no science flux information.
from astropy.time import Time
from astropy.coordinates import SkyCoord,EarthLocation
import astropy.units as u
import euclid_routed_feasibility as b

def hjd(jd,ra,de):
 t=Time(jd,format='jd',scale='utc',location=EarthLocation.from_geocentric(0,0,0,u.m));return float((t+t.light_travel_time(SkyCoord(ra*u.deg,de*u.deg),kind='heliocentric')).jd-2450000)
def epoch_jd():
 out=[]
 for e in range(16):
  h=b.getq(e,0).raw;iso=h.get('DATE-OBS') or h.get('DATEOBS');t=Time(str(iso),format='isot',scale='utc') if iso else Time(float(h.get('MJD-OBS',h.get('MJDOBS'))),format='mjd',scale='utc');t+=0.5*float(h.get('EXPTIME',400.0))*u.s;out.append(float(t.jd))
 return out
def pdist(ph):return abs((ph+0.5)%1.0-0.5)
def save(x):OUT.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');print(json.dumps(x,indent=2,sort_keys=True))
def run_control(c,gm,jds):
 target=(c['ra'],c['dec']);base={**c}
 try:routes,diag=er.route_target(gm,target)
 except Exception as e:return {**base,'routed':False,'error':f'{type(e).__name__}: {e}'}
 spec={'offset_arcsec':(0,0),'target':target,'routes':routes,'route_diagnostics':diag}
 try:
  res=mp.analyze_patch(0,spec,MORPH);cube,hs,meta=mp.fetch_cube(spec);orig=[(int(m['x0']),int(m['y0'])) for m in meta]
 except Exception as e:return {**base,'routed':True,'error':f'{type(e).__name__}: {e}'}
 cuts={e:pd.cut(cube,hs,orig,c['ra'],c['dec'],e) for e in range(16)}
 if any(v is None for v in cuts.values()):return {**base,'routed':True,'error':'forced target cutout missing'}
 meas=[]
 for e in range(16):
  peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,cor=pd.scale_metric(cuts[e],ref);morph=pd.morph_ok(s,cor,MORPH);artifact=False;checked=False;ferr=None
  if morph and abs(f)>fg.CHECK_FLOOR:
   checked=True
   try:artifact=bool(fg.flag_artifact(hs[e],e,c['ra'],c['dec'])[0])
   except Exception as ex:artifact=True;ferr=f'{type(ex).__name__}: {ex}'
  corr=fg.common_correct(f,res['epoch_common_mode_fraction'][e]);ph=((hjd(jds[e],c['ra'],c['dec'])-c['T0'])/c['P'])%1.0;dist=pdist(ph)
  meas.append({'epoch':e,'fraction':float(f),'corrected_fraction':float(corr),'morphology_ok':bool(morph),'artifact_flag':bool(artifact),'flag_checked':checked,'flag_error':ferr,'accepted':bool(morph and not artifact),'shape_residual':float(s),'shape_correlation':float(cor),'external_primary_phase':float(ph),'external_primary_phase_distance':float(dist)})
 good=[x for x in meas if x['accepted']]
 if good:
  k=int(np.argmax(np.abs([x['corrected_fraction'] for x in good])));mxrow=good[k];mx=abs(mxrow['corrected_fraction']);aligned=mxrow['external_primary_phase_distance']<=PHASE_TOL
 else:mxrow=None;mx=None;aligned=False
 recovered=bool(len(good)>=pd.MIN_ACCEPTED and mx is not None and mx>=THRESH and aligned)
 return {**base,'routed':True,'routes':{str(k):int(v) for k,v in routes.items()},'accepted_epochs':len(good),'max_abs_corrected_fraction':float(mx) if mx is not None else None,'max_epoch':mxrow['epoch'] if mxrow else None,'max_epoch_external_phase_distance':mxrow['external_primary_phase_distance'] if mxrow else None,'passes_amplitude_threshold':bool(mx is not None and mx>=THRESH),'phase_aligned':bool(aligned),'positive_control_recovered':recovered,'epoch_common_mode_fraction':res['epoch_common_mode_fraction'],'measurements':meas}
def main():
 gm=er.map_groups();jds=epoch_jd();tested=[run_control(c,gm,jds) for c in CONTROLS];recovered=[x for x in tested if x.get('positive_control_recovered')]
 save({'success':True,'gate_passed':len(recovered)>=1,'recovered_controls':len(recovered),'frozen_control_ids':[x['id'] for x in CONTROLS],'frozen_threshold':THRESH,'frozen_phase_tolerance_cycles':PHASE_TOL,'minimum_accepted_epochs':pd.MIN_ACCEPTED,'frozen_morphology_limits':MORPH,'preregistration_commit':'c189453d9916db6c5582eb38eb71e451d5afdb7c','tested':tested})
if __name__=='__main__':main()
