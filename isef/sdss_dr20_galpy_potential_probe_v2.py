#!/usr/bin/env python3
"""Infrastructure-only validation of local escape-speed calculation for several galpy MW potentials.
No SDSS/Gaia source rows are accessed.
"""
from pathlib import Path
import json, math
import numpy as np
OUT=Path('results/sdss_dr20_galpy_potential_probe_v2.json');OUT.parent.mkdir(parents=True,exist_ok=True)
out={'success':False,'status':'POTENTIAL_API_ONLY_V2','source_data_accessed':False}
try:
 from galpy.potential import MWPotential2014, evaluatePotentials, vesc
 from galpy.potential.mwpotentials import McMillan17, Cautun20
 from galpy.util.conversion import get_physical
 models={'MWPotential2014':MWPotential2014,'McMillan17':McMillan17,'Cautun20':Cautun20}
 res={}
 for name,p in models.items():
  if name=='MWPotential2014': ro,vo=8.0,220.0
  else:
   ph=get_physical(p); ro=float(ph['ro']); vo=float(ph['vo'])
  # Establish potential zero at infinity numerically and verify convergence.
  radii=[1e3,1e4,1e5]
  phinf=[float(evaluatePotentials(p,R,0.0,use_physical=False)) for R in radii]
  phi_inf=phinf[-1]
  def esc(R,z):
   phi=float(evaluatePotentials(p,R,z,use_physical=False))
   x=2.0*(phi_inf-phi)
   return float(math.sqrt(max(0.0,x))*vo)
  # Compare our general formula with galpy's R-only convenience function at the solar midplane.
  ours=esc(1.0,0.0); builtin=float(vesc(p,1.0,use_physical=False)*vo)
  rel=abs(ours-builtin)/max(abs(builtin),1e-12)
  grid=[]
  for R,z in [(0.5,0.0),(1.0,0.0),(2.0,0.0),(1.0,0.25),(2.0,0.5)]:
   grid.append({'R_over_ro':R,'z_over_ro':z,'vesc_kms':esc(R,z)})
  res[name]={'ro_kpc':ro,'vo_kms':vo,'phi_at_large_R':dict(zip(map(str,radii),phinf)),'phi_inf_used':phi_inf,'solar_vesc_formula_kms':ours,'solar_vesc_builtin_kms':builtin,'solar_relative_difference':rel,'formula_matches_builtin_1pct':bool(rel<0.01),'grid':grid}
 out['models']=res
 out['all_midplane_validations_pass']=all(x['formula_matches_builtin_1pct'] for x in res.values())
 out['all_infinity_sequences_finite']=all(all(np.isfinite(list(x['phi_at_large_R'].values()))) for x in res.values())
 out['success']=bool(out['all_midplane_validations_pass'] and out['all_infinity_sequences_finite'])
 out['decision']='MULTIPOTENTIAL_API_VALIDATED' if out['success'] else 'MULTIPOTENTIAL_API_NOT_VALIDATED'
 out['note']='Infrastructure/API validation only. No source data or candidate outcomes accessed.'
except Exception as e:
 out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
