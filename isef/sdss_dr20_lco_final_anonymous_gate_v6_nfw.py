#!/usr/bin/env python3
"""Accelerated but scientifically equivalent final anonymous LCO gate.

This executes the frozen SQL-backed v4 implementation with the preregistered
Gaia-excess-noise conformance fix from v5, plus the separately frozen
McMillan17 NFW necessary-condition screen. The screen can only prove failure;
all screen passers receive the original full six-way calculation.
"""
from pathlib import Path
import importlib.util
import numpy as np
from galpy.potential import evaluatePotentials

# Load the already-frozen conformance function without running v5.main().
spec=importlib.util.spec_from_file_location('v5','isef/sdss_dr20_lco_final_anonymous_gate_v5_sql.py')
v5=importlib.util.module_from_spec(spec); spec.loader.exec_module(v5)

src=Path('isef/sdss_dr20_lco_final_anonymous_gate_v4_sql.py').read_text()
old="""                ve=g.escape_array(models['McMillan17'],R,z); pMc=float(np.mean(sp>ve)); probs[(label,'McMillan17')]=pMc
                if pMc<.95: fail_stage[f'{label}_McMillan17']+=1; break"""
new="""                # Frozen exact necessary condition: McMillan17 component 1 is the NFW halo.
                # Full escape energy is the sum of positive component escape energies, so
                # P(v > vesc_full) <= P(v > vesc_NFW) draw by draw. If even this upper
                # bound is <0.95, the original full-potential criterion is guaranteed to fail.
                ve_nfw=_nfw_lower_escape(models['McMillan17'],R,z)
                pUpper=float(np.mean(sp>ve_nfw))
                if pUpper<.95:
                    probs[(label,'McMillan17')]=pUpper
                    fail_stage[f'{label}_McMillan17_NFW_upper_bound']+=1
                    break
                ve=g.escape_array(models['McMillan17'],R,z); pMc=float(np.mean(sp>ve)); probs[(label,'McMillan17')]=pMc
                if pMc<.95: fail_stage[f'{label}_McMillan17']+=1; break"""
if old not in src:
    raise RuntimeError('frozen v4 MC block not found; refusing silent source drift')
src=src.replace(old,new,1)
# For early NFW-proven failures the stored value is an upper bound, not the exact full
# McMillan probability. Rename only the descriptive aggregate key; survivor decisions
# remain exact because all NFW passers receive the full original calculation.
src=src.replace("o['sixway_min_probability_aggregate']=g.quant(minps)","o['sixway_min_probability_or_upper_bound_aggregate']=g.quant(minps)",1)

_halo_cache={}
def _nfw_lower_escape(spec,R,z):
    p,ro,vo,_=spec
    halo=p[1]
    key=id(halo)
    if key not in _halo_cache:
        _halo_cache[key]=float(evaluatePotentials(halo,1e5,0.0,use_physical=False))
    pinf=_halo_cache[key]
    phi=np.asarray(evaluatePotentials(halo,np.asarray(R)/ro,np.asarray(z)/ro,use_physical=False),float)
    return np.sqrt(np.maximum(0.0,2*(pinf-phi)))*vo

ns={'__name__':'v6_embedded','_nfw_lower_escape':_nfw_lower_escape}
exec(compile(src,'isef/sdss_dr20_lco_final_anonymous_gate_v4_sql.py','exec'),ns)
# Apply the already-frozen diagnostic-only astrometric_excess_noise correction.
ns['g'].gaia_pass=v5.gaia_pass_conform

if __name__=='__main__':
    ns['main']()
