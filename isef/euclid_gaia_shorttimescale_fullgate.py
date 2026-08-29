#!/usr/bin/env python3
"""Frozen Stage-0B gate on the pre-existing Gaia DR3 short-timescale control cohort.

This deliberately reuses the external-only selection from euclid_gaia_positive_controls.py:
G<19, Gaia amplitude>=0.10 mag, Gaia frequency>=4/day, ordered by Gaia amplitude.
No Euclid measurement is used for target selection or ordering.
"""
import csv,io,json,urllib.parse,urllib.request
from pathlib import Path
import numpy as np
from astropy.table import Table
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
import euclid_stage0_psf_detector as pd
import euclid_stage0_psf_flag_gate as fg
OUT=Path('results/euclid_gaia_shorttimescale_fullgate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
TAPS=['https://gea.esac.esa.int/tap-server/tap/sync','https://gaia.aip.de/tap/sync'];CENTER=(267.5945,-30.0074);RADIUS=0.20
MULTIPATCH_Q95=0.14011415120359302
MORPH={'control_quantile':0.95,'shape_residual_max':0.7433354680523049,'shape_correlation_min':0.6246851398220109}
MAX_FULLGATE=5

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
   req=urllib.request.Request(u,data=body,headers={'User-Agent':'isef-euclid-short-fullgate/1.0','Content-Type':'application/x-www-form-urlencoded'});return parse(urllib.request.urlopen(req,timeout=20).read()),u
  except Exception as e:errs.append(f'{u}: {type(e).__name__}: {e}')
 raise RuntimeError('; '.join(errs))
def gate(row,gm):
 ra=float(row['cra']);de=float(row['cdec']);target=(ra,de);base={'source_id':str(row.get('sid') or row.get('datalinkid')),'ra':ra,'dec':de,'gmag':float(row['gmag']),'gaia_amplitude_mag':float(row['amp']),'gaia_frequency_per_day':float(row['freq'])}
 try:routes,diag=er.route_target(gm,target)
 except Exception as e:return {**base,'routed':False,'route_error':str(e)}
 spec={'offset_arcsec':(0,0),'target':target,'routes':routes,'route_diagnostics':diag}
 try:res=mp.analyze_patch(0,spec,MORPH);cube,hs,meta=mp.fetch_cube(spec);orig=[(int(m['x0']),int(m['y0'])) for m in meta]
 except Exception as e:return {**base,'routed':True,'gate_error':f'{type(e).__name__}: {e}'}
 cuts={e:pd.cut(cube,hs,orig,ra,de,e) for e in range(16)}
 if any(v is None for v in cuts.values()):return {**base,'routed':True,'gate_error':'forced target cutout missing'}
 meas=[]
 for e in range(16):
  peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,c=pd.scale_metric(cuts[e],ref);morph=pd.morph_ok(s,c,MORPH);artifact=False;checked=False;ferr=None
  if morph and abs(f)>fg.CHECK_FLOOR:
   checked=True
   try:artifact=bool(fg.flag_artifact(hs[e],e,ra,de)[0])
   except Exception as ex:artifact=True;ferr=f'{type(ex).__name__}: {ex}'
  corr=fg.common_correct(f,res['epoch_common_mode_fraction'][e]);meas.append({'epoch':e,'fraction':float(f),'corrected_fraction':float(corr),'morphology_ok':bool(morph),'artifact_flag':bool(artifact),'flag_checked':checked,'flag_error':ferr,'accepted':bool(morph and not artifact),'shape_residual':float(s),'shape_correlation':float(c)})
 good=[x for x in meas if x['accepted']];vals=np.asarray([x['corrected_fraction'] for x in good],float);mx=float(np.max(np.abs(vals))) if len(vals) else None;me=int(good[int(np.argmax(np.abs(vals)))]['epoch']) if len(vals) else None
 recovered=bool(len(good)>=pd.MIN_ACCEPTED and mx is not None and mx>=MULTIPATCH_Q95)
 return {**base,'routed':True,'accepted_epochs':len(good),'max_abs_corrected_fraction':mx,'max_epoch':me,'passes_multipatch_q95':bool(mx is not None and mx>=MULTIPATCH_Q95),'positive_control_recovered':recovered,'measurements':meas}
def main():
 ra,de=CENTER;q=f"""SELECT TOP 30 gs.source_id AS sid,gs.ra AS cra,gs.dec AS cdec,gs.phot_g_mean_mag AS gmag,v.amplitude_estimate AS amp,v.frequency AS freq FROM gaiadr3.gaia_source AS gs JOIN gaiadr3.vari_short_timescale AS v ON gs.source_id=v.source_id WHERE 1=CONTAINS(POINT('ICRS',gs.ra,gs.dec),CIRCLE('ICRS',{ra},{de},{RADIUS})) AND gs.phot_g_mean_mag < 19.0 AND v.amplitude_estimate >= 0.10 AND v.frequency >= 4.0 ORDER BY v.amplitude_estimate DESC"""
 try:rows,endpoint=tap(q)
 except Exception as e:return save({'success':False,'gate_passed':False,'error':str(e),'query':q})
 rows=sorted(rows,key=lambda r:(-float(r['amp']),float(r['gmag'])));gm=er.map_groups();tested=[];full=0
 for row in rows:
  z=gate(row,gm);tested.append(z)
  if z.get('routed'):full+=1
  if full>=MAX_FULLGATE:break
 recovered=[x for x in tested if x.get('positive_control_recovered')]
 save({'success':True,'gate_passed':len(recovered)>0,'endpoint':endpoint,'query':q,'selection':'Exact pre-existing Gaia vari_short_timescale cohort: G<19, amplitude_estimate>=0.10 mag, frequency>=4/day, ordered by Gaia amplitude then G magnitude; no Euclid-yield selection','frozen_threshold':MULTIPATCH_Q95,'minimum_accepted_epochs':pd.MIN_ACCEPTED,'frozen_morphology_limits':MORPH,'fullgate_tested':full,'recovered_controls':len(recovered),'tested':tested})
if __name__=='__main__':main()
