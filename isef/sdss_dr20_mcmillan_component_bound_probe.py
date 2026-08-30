#!/usr/bin/env python3
"""Candidate-independent validation of single-component escape lower bounds.
No SDSS/Gaia/source data are accessed. This only inspects the frozen galpy
McMillan17 potential decomposition and verifies additive escape-energy algebra.
"""
from pathlib import Path
import json, math
import numpy as np
from galpy.potential import evaluatePotentials
from galpy.potential.mwpotentials import McMillan17
from galpy.util.conversion import get_physical
OUT=Path('results/sdss_dr20_mcmillan_component_bound_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
out={'success':False,'status':'POTENTIAL_ONLY','source_data_accessed':False}
try:
    ro=float(get_physical(McMillan17)['ro']);vo=float(get_physical(McMillan17)['vo'])
    pinf_total=float(evaluatePotentials(McMillan17,1e5,0.0,use_physical=False))
    comps=[]
    for i,p in enumerate(McMillan17):
        pinf=float(evaluatePotentials(p,1e5,0.0,use_physical=False))
        phi=float(evaluatePotentials(p,1.0,0.0,use_physical=False))
        e2=2*(pinf-phi)*vo*vo
        comps.append({'index':i,'type':type(p).__name__,'solar_escape_contribution_kms':math.sqrt(max(0,e2)),'positive_binding':bool(e2>=0)})
    # Verify vesc_total^2 equals sum of component vesc^2 over a broad (R,z) grid.
    max_abs=0.0; min_component_margin=float('inf')
    for R in np.geomspace(0.2,30/ro,25):
        for z in np.linspace(0,20/ro,21):
            pt=float(evaluatePotentials(McMillan17,R,z,use_physical=False))
            total_e2=2*(pinf_total-pt)*vo*vo
            sum_e2=0.0
            for p in McMillan17:
                pi=float(evaluatePotentials(p,1e5,0.0,use_physical=False))
                ph=float(evaluatePotentials(p,R,z,use_physical=False))
                ce2=2*(pi-ph)*vo*vo
                sum_e2 += ce2
                min_component_margin=min(min_component_margin,total_e2-ce2)
            max_abs=max(max_abs,abs(total_e2-sum_e2))
    out.update({'ro_kpc':ro,'vo_kms':vo,'components':comps,'max_abs_escape_energy_additivity_error':max_abs,'minimum_total_minus_single_component_escape_energy':min_component_margin})
    viable=[c for c in comps if c['positive_binding'] and c['solar_escape_contribution_kms']>0]
    if not viable: raise RuntimeError('no positive-binding component')
    best=max(viable,key=lambda x:x['solar_escape_contribution_kms'])
    out['recommended_lower_bound_component']=best
    out['success']=bool(max_abs<1e-5 and min_component_margin>=-1e-5)
    out['decision']='SINGLE_COMPONENT_NECESSARY_SCREEN_VALIDATED' if out['success'] else 'COMPONENT_BOUND_VALIDATION_FAILED'
except Exception as e:
    out['error_type']=type(e).__name__;out['error']=str(e)[:1000];out['decision']='INFRASTRUCTURE_FAILURE'
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(OUT.read_text())
