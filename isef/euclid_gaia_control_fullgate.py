#!/usr/bin/env python3
"""Pass the strongest measured Gaia DR3 rapid-variable control through the full Euclid Stage-0B gate."""
import json, math
from pathlib import Path
import numpy as np
import euclid_exact_routing as er
import euclid_stage0_multi_patch as mp

OUT=Path('results/euclid_gaia_control_fullgate.json');OUT.parent.mkdir(parents=True,exist_ok=True)
TARGET={'source_id':'4056413404956022528','ra':267.5813953658793,'dec':-30.11408905040285,'gaia_amplitude_mag':0.609702,'gaia_frequency_per_day':5.353459999063657}
DEV_Q95=0.10999505618160727
MULTIPATCH_Q95=0.14011415120359302

def sep_arcsec(a,b,c,d):
    return 3600*math.hypot((a-c)*math.cos(math.radians((b+d)/2)),b-d)

def main():
    gm=er.map_groups();res=mp.process_patch(gm,{'name':'gaia_control','ra':TARGET['ra'],'dec':TARGET['dec']})
    if not res.get('success'):
        out={'success':False,'target':TARGET,'patch_result':res};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return
    rows=res['rows'];nearest=min(rows,key=lambda r:sep_arcsec(r['ra'],r['dec'],TARGET['ra'],TARGET['dec']));dist=sep_arcsec(nearest['ra'],nearest['dec'],TARGET['ra'],TARGET['dec'])
    out={'success':True,'target':TARGET,'nearest_detected_source_separation_arcsec':dist,'nearest_source':nearest,'patch_summary':{k:res[k] for k in ['valid_stars','median_max_abs','q90','q95','q99','max']},'passes_original_dev_q95':bool(nearest['max_abs_corrected']>=DEV_Q95),'passes_broad_multipatch_q95':bool(nearest['max_abs_corrected']>=MULTIPATCH_Q95),'interpretation':'A positive control is considered recovered only if the source nearest the Gaia coordinate passes the same morphology+FLAG+common-mode source statistic above a pre-existing development threshold; no threshold is tuned here.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
