from __future__ import annotations
import numpy as np
import sugar_uncertainty_catalogue as sugar
ITERATIONS=1000; SEED_ROOT=20170209; TAG='GMN_V31_MEASUREMENT_ERROR_MARGINALIZED_MARGIN_V1'
def req(x,m):
    if not x: raise RuntimeError(m)
def wrap180(x): return (np.asarray(x,float)+180.0)%360.0-180.0
def draw(rows,iteration):
    sol=np.asarray([r['sol'] for r in rows],float); ra0=np.asarray([r['ra'] for r in rows],float); de0=np.asarray([r['dec'] for r in rows],float); vg0=np.asarray([r['vg'] for r in rows],float)
    sra=np.asarray([r['ra_sigma'] for r in rows],float); sde=np.asarray([r['dec_sigma'] for r in rows],float); svg=np.asarray([r['vg_sigma'] for r in rows],float)
    seed=sugar.stable_seed(SEED_ROOT,TAG,int(iteration)); rng=np.random.default_rng(int(seed))
    ra=rng.normal(ra0,sra); dec=rng.normal(de0,sde); ra,dec=sugar._reflect_declination(ra,dec); vg=sugar._positive_gaussian(rng,vg0,svg)
    lon,lat=sugar.equatorial_to_ecliptic(ra,dec); sun=wrap180(lon-sol)
    req(np.isfinite(np.column_stack((sol,sun,lat,vg))).all(),'nonfinite cloned geometry')
    return sol,sun,lat,vg,int(seed)
