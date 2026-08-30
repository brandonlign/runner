#!/usr/bin/env python3
"""Infrastructure-only probe of galpy Milky-Way potential APIs for later frozen escape-speed testing."""
from pathlib import Path
import json
OUT=Path('results/sdss_dr20_galpy_potential_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
out={'success':False,'status':'POTENTIAL_API_ONLY','source_data_accessed':False}
try:
 from galpy.potential import MWPotential2014
 from galpy.potential.mwpotentials import McMillan17,Cautun20
 from galpy.potential import vesc
 from galpy.util.conversion import get_physical
 models={'MWPotential2014':MWPotential2014,'McMillan17':McMillan17,'Cautun20':Cautun20}
 res={}
 for name,p in models.items():
  if name=='MWPotential2014':
   ro,vo=8.0,220.0; solar=float(vesc(p,1.0)*vo)
  else:
   ph=get_physical(p);ro=float(ph['ro']);vo=float(ph['vo']);solar=float(vesc(p,1.0,use_physical=False)*vo)
  # API sanity at a few dimensionless R,z points; values are not applied to sources.
  vals=[]
  for R,z in [(0.5,0.0),(1.0,0.0),(2.0,0.0),(1.0,0.25)]:
   vals.append({'R_over_ro':R,'z_over_ro':z,'vesc_kms':float(vesc(p,R,z=z,use_physical=False)*vo)})
  res[name]={'ro_kpc':ro,'vo_kms':vo,'solar_vesc_kms':solar,'api_grid':vals}
 out.update(success=True,models=res,note='No SDSS/Gaia rows or identities accessed. This only validates potential availability and escape-speed API semantics.')
except Exception as e:out['error']=f'{type(e).__name__}: {e}'
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
