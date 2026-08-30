#!/usr/bin/env python3
"""Guarded identity-open rerun for the frozen DR20 LCO search.

This file is intentionally NOT wired to an automatic workflow. It may be run
only after an authoritative anonymous pass. It recomputes the frozen gate and
emits identities only if the recomputed survivor count exactly equals the
externally supplied positive expected count.
"""
from pathlib import Path
import importlib.util, os

if os.environ.get('ALLOW_IDENTITY_OPEN') != 'YES_AFTER_ANONYMOUS_PASS':
    raise SystemExit('identity opening not authorized')
try:
    EXPECTED=int(os.environ['EXPECTED_ANONYMOUS_SURVIVORS'])
except Exception:
    raise SystemExit('positive EXPECTED_ANONYMOUS_SURVIVORS required')
if EXPECTED <= 0:
    raise SystemExit('identity opening forbidden for zero survivors')

# Reuse the already-frozen source transformation and NFW helper from v6.
spec=importlib.util.spec_from_file_location('v6','isef/sdss_dr20_lco_final_anonymous_gate_v6_nfw.py')
v6=importlib.util.module_from_spec(spec); spec.loader.exec_module(v6)
src=Path('isef/sdss_dr20_lco_final_anonymous_gate_v4_sql.py').read_text()
if v6.old not in src:
    raise RuntimeError('frozen v4 MC block drifted; refusing identity open')
src=src.replace(v6.old,v6.new,1)

old_out="""        o['mc_tested_rows']=int(tested); o['anonymous_robust_unbound_survivors']=int(len(final)); o['sixway_min_probability_aggregate']=g.quant(minps); o['computational_short_circuit_counts']=dict(fail_stage)
        o['decision']='ANONYMOUS_ROBUST_UNBOUND_SURVIVORS_EXIST' if final else 'NO_ANONYMOUS_ROBUST_UNBOUND_SURVIVORS'; o['success']=True"""
new_out="""        o['mc_tested_rows']=int(tested); o['anonymous_robust_unbound_survivors']=int(len(final)); o['sixway_min_probability_or_upper_bound_aggregate']=g.quant(minps); o['computational_short_circuit_counts']=dict(fail_stage)
        if len(final) != EXPECTED:
            raise RuntimeError('recomputed survivor count does not match authorized anonymous count')
        o['identity_open_survivors']=[{
            'sdss_id':int(x['sdss']), 'gaia_dr3_source_id':int(x['gaia']),
            'ra_deg':float(x['ra']), 'dec_deg':float(x['dec']),
            'summary_v_rad_kms':float(x['v']), 'summary_e_v_rad_kms':float(x['ev']),
            'r_med_geo_pc':float(x['gm']), 'r_med_photogeo_pc':float(x['pm']),
            'gaia_pmra_masyr':float(x['g']['pmra']), 'gaia_pmdec_masyr':float(x['g']['pmde'])
        } for x in final]
        o['identity_open_authorized_count']=EXPECTED
        o['decision']='IDENTITIES_OPENED_AFTER_MATCHED_ANONYMOUS_PASS'; o['success']=True"""
if old_out not in src:
    raise RuntimeError('frozen output block drifted; refusing identity open')
src=src.replace(old_out,new_out,1)

ns={'__name__':'identity_embedded','_nfw_lower_escape':v6._nfw_lower_escape,'EXPECTED':EXPECTED}
exec(compile(src,'isef/sdss_dr20_lco_final_anonymous_gate_v4_sql.py','exec'),ns)
ns['g'].gaia_pass=v6.v5.gaia_pass_conform

if __name__=='__main__':
    ns['main']()
