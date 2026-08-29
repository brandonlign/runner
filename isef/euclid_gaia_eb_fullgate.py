#!/usr/bin/env python3
"""Run externally selected Gaia DR3 eclipsing binaries through the frozen Euclid Stage-0B gate.

The target set is defined only by Gaia metadata and exact-WCS geometry before
Euclid fluxes are evaluated. No Euclid amplitude is used for target selection.
"""
import csv,io,json,urllib.parse,urllib.request
from pathlib import Path
import numpy as np
from astropy.table import Table
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg

OUT=Path('results/euclid_gaia_eb_fullgate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
TAPS=['https://gea.esac.esa.int/tap-server/tap/sync','https://gaia.aip.de/tap/sync']
CENTER=(267.58,-30.11);RADIUS=0.18
MULTIPATCH_Q95=0.14011415120359302
MORPH={'control_quantile':0.95,'shape_residual_max':0.7433354680523049,'shape_correlation_min':0.6246851398220109}
MAX_FULLGATE=4

def save(x):OUT.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');print(json.dumps(x,indent=2,sort_keys=True))
def parse(raw):
 t=raw.decode('utf-8','replace')
 if 'value="ERROR"' in t[:4000]:raise RuntimeError(t[:1600])
 if '<VOTABLE' in t[:1000]:
  q=Table.read(io.BytesIO(raw),format='votable');return [{str(n).lower():('' if np.ma.is_masked(r[n]) else str(r[n])) for n in q.colnames} for r in q]
 return [{str(k).lower():v for k,v in r.items()} for r in csv.DictReader(io.StringIO(t))]
def tap(q):
 body=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q}).encode();errs=[]
 for u in TAPS:
  try:
   req=urllib.request.Request(u,data=body,headers={'User-Agent':'isef-euclid-eb-fullgate/1.0','Content-Type':'application/x-www-form-urlencoded'});return parse(urllib.request.urlopen(req,timeout=30).read()),u
  except Exception as e:errs.append(f'{u}: {e}')
 raise RuntimeError('; '.join(errs))
def gate(row,gm):
 ra=float(row['cra']);de=float(row['cdec']);target=(ra,de)
 base={'source_id':str(row['sid']),'ra':ra,'dec':de,'gmag':float(row['gmag']),'frequency_per_day':float(row['freq']),'period_hours':24/float(row['freq']),'primary_depth_mag':float(row['depth']),'primary_duration_phase':float(row['duration']),'global_ranking':float(row['rank'])}
 try:routes,diag=er.route_target(gm,target)
 except Exception as e:return {**base,'routed':False,'route_error':str(e)}
 spec={'offset_arcsec':(0,0),'target':target,'routes':routes,'route_diagnostics':diag}
 try:res=mp.analyze_patch(0,spec,MORPH);cube,hs,meta=mp.fetch_cube(spec);orig=[(int(m['x0']),int(m['y0'])) for m in meta]
 except Exception as e:return {**base,'routed':True,'gate_error':f'{type(e).__name__}: {e}'}
 cuts={e:pd.cut(cube,hs,orig,ra,de,e) for e in range(16)}
 if any(v is None for v in cuts.values()):return {**base,'routed':True,'gate_error':'forced target cutout missing'}
 rows=[]
 for e in range(16):
  peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,c=pd.scale_metric(cuts[e],ref);morph=pd.morph_ok(s,c,MORPH);artifact=False;checked=False;ferr=None
  if morph and abs(f)>fg.CHECK_FLOOR:
   checked=True
   try:artifact=bool(fg.flag_artifact(hs[e],e,ra,de)[0])
   except Exception as ex:artifact=True;ferr=f'{type(ex).__name__}: {ex}'
  corr=fg.common_correct(f,res['epoch_common_mode_fraction'][e]);rows.append({'epoch':e,'fraction':float(f),'corrected_fraction':float(corr),'morphology_ok':bool(morph),'artifact_flag':bool(artifact),'flag_checked':checked,'flag_error':ferr,'accepted':bool(morph and not artifact),'shape_residual':float(s),'shape_correlation':float(c)})
 good=[x for x in rows if x['accepted']];vals=np.asarray([x['corrected_fraction'] for x in good],float);mx=float(np.max(np.abs(vals))) if len(vals) else None;me=int(good[int(np.argmax(np.abs(vals)))]['epoch']) if len(vals) else None
 recovered=bool(len(good)>=pd.MIN_ACCEPTED and mx is not None and mx>=MULTIPATCH_Q95)
 return {**base,'routed':True,'accepted_epochs':len(good),'max_abs_corrected_fraction':mx,'max_epoch':me,'passes_multipatch_q95':bool(mx is not None and mx>=MULTIPATCH_Q95),'positive_control_recovered':recovered,'measurements':rows}
def main():
 ra,de=CENTER;q=f"""SELECT TOP 60 gs.source_id AS sid,gs.ra AS cra,gs.dec AS cdec,gs.phot_g_mean_mag AS gmag,v.frequency AS freq,v.derived_primary_ecl_depth AS depth,v.derived_primary_ecl_duration AS duration,v.global_ranking AS rank FROM gaiadr3.gaia_source AS gs JOIN gaiadr3.vari_eclipsing_binary AS v ON gs.source_id=v.source_id WHERE 1=CONTAINS(POINT('ICRS',gs.ra,gs.dec),CIRCLE('ICRS',{ra},{de},{RADIUS})) AND gs.phot_g_mean_mag<19.0 AND v.frequency>=2.0 AND v.derived_primary_ecl_depth>=0.20 AND v.derived_primary_ecl_duration>=0.03 AND v.global_ranking>=0.5 ORDER BY v.derived_primary_ecl_depth DESC"""
 try:rows,endpoint=tap(q)
 except Exception as e:return save({'success':False,'gate_passed':False,'error':str(e),'query':q})
 gm=er.map_groups();tested=[];full=0
 for row in rows:
  # Geometry is allowed to determine measurability; Euclid flux is not.
  try:er.route_target(gm,(float(row['cra']),float(row['cdec'])))
  except Exception as e:
   tested.append({'source_id':str(row['sid']),'ra':float(row['cra']),'dec':float(row['cdec']),'routed':False,'route_error':str(e)});continue
  z=gate(row,gm);tested.append(z);full+=1
  if full>=MAX_FULLGATE:break
 recovered=[x for x in tested if x.get('positive_control_recovered')]
 save({'success':True,'gate_passed':len(recovered)>0,'endpoint':endpoint,'query':q,'selection':'Gaia DR3 EB external-only selection: G<19, frequency>=2/d, primary eclipse depth>=0.20 mag, eclipse duration phase>=0.03, global ranking>=0.5, ordered by Gaia eclipse depth; first exact-WCS-routable systems tested without Euclid-yield ordering','frozen_threshold':MULTIPATCH_Q95,'minimum_accepted_epochs':pd.MIN_ACCEPTED,'frozen_morphology_limits':MORPH,'fullgate_tested':full,'recovered_controls':len(recovered),'tested':tested})
if __name__=='__main__':main()
