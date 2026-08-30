#!/usr/bin/env python3
"""Execute the frozen Stage-A v1 protocol with the pre-outcome edge-coverage correction.

Scientific thresholds/noise/null/injection rules remain those in
ngc1427a_muse_stagea_v1_correlated_noise.py. The only correction is the one
documented in research/NGC1427A_MUSE_STAGEA_V1_COVERAGE_CORRECTION.md:
fixed circles with <100 full-PSF-support pixels are skipped in place, count as
zero usable area, and the gate additionally requires >=50% geometrical coverage.
"""
from pathlib import Path
import importlib.util, math, json

BASE=Path('isef/ngc1427a_muse_stagea_v1_correlated_noise.py')
src=BASE.read_text()

old="""   area=float(support.sum()*PIX_ARC**2); total_area+=area
   # Internal target map used only to define empirical noise for injection detection; no real target peaks/counts are emitted.
   _, target_noise=snr_emp(base,bv,support); sigmas.append(target_noise['sigma_eff'])
"""
new="""   area=float(support.sum()*PIX_ARC**2)
   if int(support.sum()) < 100:
    o['tiles'].append({'tile_index':ti,'cutout_bytes':nbytes,'shape':list(data.shape),'usable_area_arcsec2':0.0,'coverage_status':'INSUFFICIENT_VALID_COVERAGE','valid_psf_support_pixels':int(support.sum())})
    continue
   total_area+=area
   # Internal target map used only to define empirical noise for injection detection; no real target peaks/counts are emitted.
   _, target_noise=snr_emp(base,bv,support); sigmas.append(target_noise['sigma_eff'])
"""
if old not in src:
    raise RuntimeError('base Stage-A v1 coverage insertion point drifted')
src=src.replace(old,new,1)

old2="""  sample_false=.5*null_total; mosaic=736*611*PIX_ARC**2; full_false=sample_false/total_area*mosaic
  a27=sum(t['usable_area_arcsec2'] for t in o['tiles'] if t['recovery']['27.0']['fraction']>=.90); a275=sum(t['usable_area_arcsec2'] for t in o['tiles'] if t['recovery']['27.5']['fraction']>=.50)
  medsig=float(np.median(sigmas)); sigma_regime_ok=all(.5*medsig<=x<=10*medsig for x in sigmas)
  o.update({'aggregate_offline_null_peaks':null_total,'sampled_expected_false_scaled':sample_false,'usable_sampled_area_arcsec2':total_area,'conservative_full_mosaic_expected_false':full_false,'area_fraction_passing_27':a27/total_area,'area_fraction_passing_27p5':a275/total_area,'gate_recovery_27':a27/total_area>=.5,'gate_recovery_27p5':a275/total_area>=.5,'gate_false_positive_full_mosaic':full_false<=1.,'gate_noise_tail_sanity':not pathological,'gate_sigma_regime_sanity':sigma_regime_ok})
  o['gate_passed']=bool(o['gate_recovery_27'] and o['gate_recovery_27p5'] and o['gate_false_positive_full_mosaic'] and o['gate_noise_tail_sanity'] and o['gate_sigma_regime_sanity'])
"""
new2="""  geometrical_area=len(CENTERS)*math.pi*6.0**2
  coverage_fraction=total_area/geometrical_area
  if total_area <= 0 or not sigmas:
   o.update({'geometrical_sampled_area_arcsec2':geometrical_area,'usable_sampled_area_arcsec2':total_area,'usable_geometrical_area_fraction':coverage_fraction,'gate_validation_coverage':False,'gate_passed':False,'decision':'STAGEA_V1_FAILED_KILL_DIRECTION','success':True})
   OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\\n'); print(json.dumps(o,indent=2,sort_keys=True)); return
  sample_false=.5*null_total; mosaic=736*611*PIX_ARC**2; full_false=sample_false/total_area*mosaic
  used=[t for t in o['tiles'] if t.get('coverage_status')!='INSUFFICIENT_VALID_COVERAGE']
  a27=sum(t['usable_area_arcsec2'] for t in used if t['recovery']['27.0']['fraction']>=.90); a275=sum(t['usable_area_arcsec2'] for t in used if t['recovery']['27.5']['fraction']>=.50)
  medsig=float(np.median(sigmas)); sigma_regime_ok=all(.5*medsig<=x<=10*medsig for x in sigmas)
  o.update({'aggregate_offline_null_peaks':null_total,'sampled_expected_false_scaled':sample_false,'geometrical_sampled_area_arcsec2':geometrical_area,'usable_sampled_area_arcsec2':total_area,'usable_geometrical_area_fraction':coverage_fraction,'gate_validation_coverage':coverage_fraction>=.5,'conservative_full_mosaic_expected_false':full_false,'area_fraction_passing_27':a27/total_area,'area_fraction_passing_27p5':a275/total_area,'gate_recovery_27':a27/total_area>=.5,'gate_recovery_27p5':a275/total_area>=.5,'gate_false_positive_full_mosaic':full_false<=1.,'gate_noise_tail_sanity':not pathological,'gate_sigma_regime_sanity':sigma_regime_ok})
  o['gate_passed']=bool(o['gate_validation_coverage'] and o['gate_recovery_27'] and o['gate_recovery_27p5'] and o['gate_false_positive_full_mosaic'] and o['gate_noise_tail_sanity'] and o['gate_sigma_regime_sanity'])
"""
if old2 not in src:
    raise RuntimeError('base Stage-A v1 aggregate block drifted')
src=src.replace(old2,new2,1)
src=src.replace("FREEZE='f1d464cde039a2483695b46c9c0627744d34fe89'","FREEZE='f1d464cde039a2483695b46c9c0627744d34fe89+coverage-correction-dabedd01a840a5e3fc78a4447e3695226f5e14d7'",1)
src=src.replace("OUT=Path('results/ngc1427a_muse_stagea_v1_correlated_noise.json')","OUT=Path('results/ngc1427a_muse_stagea_v1_coverage_corrected.json')",1)
ns={'__name__':'stagea_v1_coverage_corrected'}
exec(compile(src,str(BASE),'exec'),ns)
ns['main']()
