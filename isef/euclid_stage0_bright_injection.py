#!/usr/bin/env python3
"""Conservative injection pilot on the brightest Stage-0 stars."""
import json
from pathlib import Path
import numpy as np
import euclid_stage0_injection as p

OUT=Path('results/euclid_stage0_bright_injection.json')

def stat(v):
    m=np.median(v);return float(np.max(np.abs(v/m-1)))

def main():
    rng=np.random.default_rng(20260829);out={'success':True,'note':'bright-subset development diagnostic; threshold is maximum observed null, not final survey FDR','radii':{}}
    for radius in (1.8,3.2):
        fl,peak=p.build_flux(radius);order=np.argsort(peak)[::-1]
        rd={}
        for n in (10,20):
            idx=order[:min(n,len(order))];corr=p.normalize(fl[idx]);null=np.array([stat(v) for v in corr]);thr=float(np.max(null)+1e-12);rows=[]
            for kind,sgn in [('flare',1),('eclipse',-1)]:
              for dur in (1,2,3):
                for amp in (0.03,0.05,0.08,0.10,0.15,0.20,0.30,0.50):
                    hit=tot=0
                    for v in corr:
                      for rep in range(100):
                        start=int(rng.integers(0,17-dur));z=v.copy();z[start:start+dur]*=(1+sgn*amp);hit+=stat(z)>thr;tot+=1
                    rows.append({'kind':kind,'duration_epochs':dur,'amplitude':amp,'recovery':hit/tot,'trials':tot})
            rd[str(n)]={'stars':int(len(corr)),'null_max_fractional_excursions':sorted([float(x) for x in null]),'zero_observed_fp_threshold':thr,'injections':rows}
        out['radii'][str(radius)]=rd
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__':main()
