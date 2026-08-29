#!/usr/bin/env python3
"""Pass the strongest measured Gaia DR3 rapid-variable control through the current Euclid Stage-0B gate."""
import json, math
from pathlib import Path
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp
import euclid_stage0_psf_detector as pd
OUT=Path('results/euclid_gaia_control_fullgate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
TARGET={'source_id':'4056413404956022528','ra':267.5813953658793,'dec':-30.11408905040285,'gaia_amplitude_mag':0.609702,'gaia_frequency_per_day':5.353459999063657}
DEV_Q95=0.10999505618160727;MULTIPATCH_Q95=0.14011415120359302

def sep_arcsec(a,b,c,d):return 3600*math.hypot((a-c)*math.cos(math.radians((b+d)/2)),b-d)
def save(x):OUT.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');print(json.dumps(x,indent=2,sort_keys=True))
def main():
    gm=er.map_groups();target=(TARGET['ra'],TARGET['dec'])
    try:routes,diag=er.route_target(gm,target)
    except Exception as e:return save({'success':False,'target':TARGET,'error':f'route: {type(e).__name__}: {e}'})
    spec={'offset_arcsec':(0,0),'target':target,'routes':routes,'route_diagnostics':diag}
    try:res=mp.analyze_patch(0,spec,pd.morphology_limits())
    except Exception as e:return save({'success':False,'target':TARGET,'error':f'analyze: {type(e).__name__}: {e}'})
    tops=res.get('top_sources',[])
    if not tops:return save({'success':False,'target':TARGET,'error':'no valid sources in control patch','patch':res})
    nearest=min(tops,key=lambda r:sep_arcsec(r['ra'],r['dec'],TARGET['ra'],TARGET['dec']));dist=sep_arcsec(nearest['ra'],nearest['dec'],TARGET['ra'],TARGET['dec'])
    recovered=dist<=0.5 and nearest['max_abs_fraction']>=MULTIPATCH_Q95
    save({'success':True,'target':TARGET,'nearest_top_source_separation_arcsec':dist,'nearest_top_source':nearest,'patch_summary':{'valid_stars':res['valid_stars'],'flag_reads':res['flag_reads'],'flagged_high_measurements':res['flagged_high_measurements'],'max_abs_fraction':res['max_abs_fraction']},'passes_original_dev_q95':bool(dist<=0.5 and nearest['max_abs_fraction']>=DEV_Q95),'passes_broad_multipatch_q95':bool(recovered),'positive_control_recovered':bool(recovered),'interpretation':'Recovery requires the detected source nearest the Gaia coordinate to be within 0.5 arcsec and exceed the pre-existing five-patch q95 full-gate threshold. No threshold is tuned on this control.'})
if __name__=='__main__':main()
