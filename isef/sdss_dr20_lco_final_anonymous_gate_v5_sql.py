#!/usr/bin/env python3
"""Authoritative transport wrapper for the frozen LCO final gate.

Only protocol-conformance correction relative to v4: astrometric_excess_noise is
diagnostic-only exactly as preregistered, so missing/nonfinite values cannot
reject a source. All mandatory Gaia cuts and all other scientific rules remain
unchanged.
"""
import importlib.util
import numpy as np

spec=importlib.util.spec_from_file_location('v4','isef/sdss_dr20_lco_final_anonymous_gate_v4_sql.py')
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)


def gaia_pass_conform(g):
    try:
        val=v4.g.val
        pmra=float(val(g['pmra'])); epmra=float(val(g['pmra_error']))
        pmde=float(val(g['pmdec'])); epmde=float(val(g['pmdec_error']))
        corr=float(val(g['pmra_pmdec_corr'])); ruwe=float(val(g['ruwe']))
        solved=int(val(g['astrometric_params_solved'])); vis=int(val(g['visibility_periods_used']))
        dup_raw=val(g['duplicated_source']); ipdm=float(val(g['ipd_frac_multi_peak']))
        ipdg=float(val(g['ipd_gof_harmonic_amplitude'])); nss=int(val(g['non_single_star']))
        # Mandatory fields must be genuinely present and finite.
        if dup_raw is None: return False,None
        dup=bool(dup_raw)
        if not all(np.isfinite([pmra,epmra,pmde,epmde,corr,ruwe,ipdm,ipdg])): return False,None
        if epmra<=0 or epmde<=0 or abs(corr)>1: return False,None
        cov=np.array([[epmra**2,corr*epmra*epmde],[corr*epmra*epmde,epmde**2]],float)
        if np.min(np.linalg.eigvalsh(cov)) < -1e-10: return False,None
        ok=(solved==31 and ruwe<1.4 and vis>=8 and (not dup) and ipdm<2 and ipdg<0.1 and nss==0)
        # Diagnostic only: absence/nonfinite does not affect `ok`.
        ex=None
        try:
            raw=val(g.get('astrometric_excess_noise'))
            if raw is not None:
                fx=float(raw)
                if np.isfinite(fx): ex=fx
        except Exception:
            ex=None
        return bool(ok),{'pmra':pmra,'pmde':pmde,'cov':cov,'excess':ex}
    except Exception:
        return False,None

v4.g.gaia_pass=gaia_pass_conform
if __name__=='__main__':
    v4.main()
