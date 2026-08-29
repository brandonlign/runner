#!/usr/bin/env python3
"""Joint morphology + Euclid FLAG + epoch-common-mode PSF null.

The event amplitude statistic is a same-dither PSF scale. Candidate-independent
PSF morphology is applied first. Released FLG maps are then checked in parallel
for morphology-clean measurements above 5%. Finally an epoch-wide multiplicative
PSF/throughput common mode is estimated as the median of accepted stars and
removed before source maxima are constructed. Development field only.
"""
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np
import euclid_routed_feasibility as b
import euclid_stage0_psf_detector as pd
import euclid_stage0_flag_population as fp

OUT=Path('results/euclid_stage0_psf_flag_gate.json');CHECK_FLOOR=0.05
ART_BITS=(1,2,8,16,128,512)

def flag_artifact(q,e,ra,de):
    gx,gy=b.pix(q,ra,de);fn=b.FILES[e].replace('_sci.fits','_flg.fits');url=f'{b.BASE}/{fn}'
    z=fp.stamp_cached(url,q.k,gx,gy,2).astype(np.int64)
    return bool(any(np.any(z & bit) for bit in ART_BITS)),int(z[z.shape[0]//2,z.shape[1]//2])

def common_correct(f,cm):
    return float((1.0+float(f))/(1.0+float(cm))-1.0)

def main():
    base,cube,hs,orig=pd.setup();lim=pd.morphology_limits();ra,de,peak=pd.sources(cube,hs,orig)
    source_rows=[];checks=[]
    for j,(r,d) in enumerate(zip(ra,de)):
        cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
        if any(v is None for v in cuts.values()):continue
        mm=[]
        for e in range(16):
            peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,c=pd.scale_metric(cuts[e],ref);morph=pd.morph_ok(s,c,lim)
            row={'star':j,'ra':float(r),'dec':float(d),'epoch':e,'fraction':float(f),'morphology_ok':morph,'flag_checked':False,'artifact_flag':False,'center_flag':None,'shape_residual':float(s),'shape_correlation':float(c)}
            mm.append(row)
            if morph and abs(f)>CHECK_FLOOR:checks.append(row)
        source_rows.append({'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'measurements':mm})
    # I/O dominates this stage, so issue independent FLG range reads concurrently.
    with ThreadPoolExecutor(max_workers=32) as ex:
        fs={ex.submit(flag_artifact,hs[r['epoch']],r['epoch'],r['ra'],r['dec']):r for r in checks}
        for fut in as_completed(fs):
            r=fs[fut];r['flag_checked']=True
            try:r['artifact_flag'],r['center_flag']=fut.result()
            except Exception as e:r['artifact_flag']=True;r['flag_error']=f'{type(e).__name__}: {e}'
    # accepted_precommon uses only candidate-independent morphology + FLG state.
    for s in source_rows:
        for r in s['measurements']:r['accepted_precommon']=bool(r['morphology_ok'] and not r['artifact_flag'])
    common=[];common_n=[]
    for e in range(16):
        vals=[r['fraction'] for s in source_rows for r in s['measurements'] if r['epoch']==e and r['accepted_precommon']]
        common.append(float(np.median(vals)) if vals else 0.0);common_n.append(len(vals))
    stars=[]
    for s in source_rows:
        good=[]
        for r in s['measurements']:
            r['common_mode_fraction']=common[r['epoch']];r['corrected_fraction']=common_correct(r['fraction'],common[r['epoch']]);r['accepted']=r['accepted_precommon']
            if r['accepted']:good.append(r)
        if len(good)<pd.MIN_ACCEPTED:continue
        vals=np.asarray([r['corrected_fraction'] for r in good]);sig,med=pd.mad_sigma(vals);imax=int(np.argmax(np.abs(vals)))
        stars.append({'star':s['star'],'ra':s['ra'],'dec':s['dec'],'peak':s['peak'],'accepted_epochs':len(good),'max_abs_fraction':float(np.max(np.abs(vals))),'max_epoch':int(good[imax]['epoch']),'robust_sigma':sig,'median_fraction':med,'measurements':s['measurements']})
    maxima=np.asarray([s['max_abs_fraction'] for s in stars],float)
    if not len(maxima):raise RuntimeError('no FLAG-clean morphology-complete stars')
    th={'q90':float(np.quantile(maxima,.90)),'q95':float(np.quantile(maxima,.95)),'q99':float(np.quantile(maxima,.99)),'zero_observed_fp':float(np.max(maxima))};complete=bool(th['q95']>=CHECK_FLOOR)
    stars.sort(key=lambda x:x['max_abs_fraction'],reverse=True);checks.sort(key=lambda x:abs(x['fraction']),reverse=True)
    out={'success':complete,'note':'development PSF null after independent morphology, released FLAG, and ensemble epoch-common-mode correction','flag_check_floor':CHECK_FLOOR,'flag_screen_complete_for_q95':complete,'morphology_limits':lim,'candidate_stars':len(ra),'valid_stars':len(stars),'flag_reads':len(checks),'flagged_high_measurements':sum(bool(r['artifact_flag']) for r in checks),'epoch_common_mode_fraction':common,'epoch_common_mode_n':common_n,'epoch_common_mode_summary':pd.summary(np.abs(common)),'source_level_max_abs_fraction':pd.summary(maxima),'thresholds':th,'top_sources':stars[:15],'high_measurement_flag_audit':checks[:100]}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
