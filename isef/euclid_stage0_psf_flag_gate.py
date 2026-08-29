#!/usr/bin/env python3
"""Construct a source-level PSF null after independent morphology + Euclid FLAG gates.

To keep remote I/O bounded, released FLG maps are read only for morphology-clean
measurements whose absolute PSF-scale excursion exceeds 5%. Measurements below
5% cannot set any reported threshold above 5%; the output explicitly verifies
whether that condition holds. FLAG classification itself never uses event rank.
Development field only.
"""
import json
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

def main():
    base,cube,hs,orig=pd.setup();lim=pd.morphology_limits();ra,de,peak=pd.sources(cube,hs,orig)
    stars=[];flag_reads=flagged=0;events=[]
    for j,(r,d) in enumerate(zip(ra,de)):
        cuts={e:pd.cut(cube,hs,orig,r,d,e) for e in range(16)}
        if any(v is None for v in cuts.values()):continue
        accepted=[]
        for e in range(16):
            peers=[p for p in range(e%4,16,4) if p!=e];ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);f,s,c=pd.scale_metric(cuts[e],ref)
            morph=pd.morph_ok(s,c,lim);artifact=False;center_flag=None;read=False
            if morph and abs(f)>CHECK_FLOOR:
                try:artifact,center_flag=flag_artifact(hs[e],e,float(r),float(d));read=True;flag_reads+=1;flagged+=int(artifact)
                except Exception as ex:artifact=True;center_flag=None
            ok=bool(morph and not artifact);accepted.append({'epoch':e,'fraction':float(f),'morphology_ok':morph,'flag_checked':read,'artifact_flag':artifact,'center_flag':center_flag,'accepted':ok,'shape_residual':float(s),'shape_correlation':float(c)})
            if morph and abs(f)>CHECK_FLOOR:events.append({'star':j,'ra':float(r),'dec':float(d),**accepted[-1]})
        good=[x for x in accepted if x['accepted']]
        if len(good)<pd.MIN_ACCEPTED:continue
        vals=np.asarray([x['fraction'] for x in good]);sig,med=pd.mad_sigma(vals);mx=float(np.max(np.abs(vals)));imax=int(np.argmax(np.abs(vals)))
        stars.append({'star':j,'ra':float(r),'dec':float(d),'peak':float(peak[j]),'accepted_epochs':len(good),'max_abs_fraction':mx,'max_epoch':int(good[imax]['epoch']),'robust_sigma':sig,'median_fraction':med,'measurements':accepted})
    maxima=np.asarray([s['max_abs_fraction'] for s in stars],float)
    if not len(maxima):raise RuntimeError('no FLAG-clean morphology-complete stars')
    th={'q90':float(np.quantile(maxima,.90)),'q95':float(np.quantile(maxima,.95)),'q99':float(np.quantile(maxima,.99)),'zero_observed_fp':float(np.max(maxima))}
    complete=bool(th['q95']>=CHECK_FLOOR)
    stars.sort(key=lambda x:x['max_abs_fraction'],reverse=True);events.sort(key=lambda x:abs(x['fraction']),reverse=True)
    out={'success':complete,'note':'development PSF null after independent morphology and released FLAG gates','flag_check_floor':CHECK_FLOOR,'flag_screen_complete_for_q95':complete,'morphology_limits':lim,'candidate_stars':len(ra),'valid_stars':len(stars),'flag_reads':flag_reads,'flagged_high_measurements':flagged,'source_level_max_abs_fraction':pd.summary(maxima),'thresholds':th,'top_sources':stars[:15],'high_measurement_flag_audit':events[:100]}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
