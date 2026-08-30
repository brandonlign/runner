#!/usr/bin/env python3
"""Validate a NumPy affine ICRS->Galactocentric transform against Astropy.
No survey/source data are accessed. This is computational-equivalence testing only.
"""
from pathlib import Path
import importlib.util, json
import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord, ICRS, CartesianRepresentation, CartesianDifferential

spec=importlib.util.spec_from_file_location('g','isef/sdss_dr20_lco_final_anonymous_gate.py')
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
OUT=Path('results/sdss_dr20_fast_coordinate_transform_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
K=4.740470463533349

def tr(px,py,pz,vx,vy,vz):
    rep=CartesianRepresentation(px*u.kpc,py*u.kpc,pz*u.kpc,
        differentials=CartesianDifferential(vx*u.km/u.s,vy*u.km/u.s,vz*u.km/u.s))
    return SkyCoord(rep,frame=ICRS()).transform_to(g.GC)

base=tr(0.,0.,0.,0.,0.,0.)
t=np.array([base.x.to_value(u.kpc),base.y.to_value(u.kpc),base.z.to_value(u.kpc)],float)
v0=np.array([base.v_x.to_value(u.km/u.s),base.v_y.to_value(u.km/u.s),base.v_z.to_value(u.km/u.s)],float)
Mp=np.zeros((3,3)); Mv=np.zeros((3,3))
for j in range(3):
    p=np.zeros(3); p[j]=1.; q=tr(*p,0.,0.,0.)
    Mp[:,j]=[q.x.to_value(u.kpc),q.y.to_value(u.kpc),q.z.to_value(u.kpc)]-t
    vv=np.zeros(3); vv[j]=1.; q=tr(0.,0.,0.,*vv)
    Mv[:,j]=[q.v_x.to_value(u.km/u.s),q.v_y.to_value(u.km/u.s),q.v_z.to_value(u.km/u.s)]-v0

def fast(ra,dec,dist_pc,pmra,pmde,rv):
    ra=np.deg2rad(np.asarray(ra,float)); de=np.deg2rad(np.asarray(dec,float)); d=np.asarray(dist_pc,float)/1000.
    ca=np.cos(ra); sa=np.sin(ra); cd=np.cos(de); sd=np.sin(de)
    r=np.column_stack((cd*ca,cd*sa,sd))
    ah=np.column_stack((-sa,ca,np.zeros_like(sa)))
    dh=np.column_stack((-sd*ca,-sd*sa,cd))
    pos=d[:,None]*r
    vel=np.asarray(rv,float)[:,None]*r + (K*d)[:,None]*(np.asarray(pmra,float)[:,None]*ah+np.asarray(pmde,float)[:,None]*dh)
    gp=pos@Mp.T+t; gv=vel@Mv.T+v0
    sp=np.sqrt(np.sum(gv*gv,axis=1)); R=np.hypot(gp[:,0],gp[:,1]); z=np.abs(gp[:,2])
    return sp,R,z

out={'success':False,'status':'COORDINATE_TRANSFORM_ONLY','source_data_accessed':False}
try:
    rng=np.random.default_rng(20260830); n=10000
    ra=rng.uniform(0,360,n); dec=np.rad2deg(np.arcsin(rng.uniform(-1,1,n)))
    dist=10**rng.uniform(1.5,5.0,n); pmra=rng.normal(0,80,n); pmde=rng.normal(0,80,n); rv=rng.normal(0,800,n)
    a=g.speed(ra,dec,dist,pmra,pmde,rv); b=fast(ra,dec,dist,pmra,pmde,rv)
    ds=np.max(np.abs(a[0]-b[0])); dR=np.max(np.abs(a[1]-b[1])); dz=np.max(np.abs(a[2]-b[2]))
    out.update({'n_random_tests':n,'max_abs_speed_difference_kms':float(ds),'max_abs_R_difference_kpc':float(dR),'max_abs_z_difference_kpc':float(dz),'position_matrix':Mp.tolist(),'velocity_matrix':Mv.tolist(),'position_offset_kpc':t.tolist(),'velocity_offset_kms':v0.tolist(),'max_matrix_difference':float(np.max(np.abs(Mp-Mv)))})
    out['success']=bool(ds<1e-6 and dR<1e-9 and dz<1e-9 and np.max(np.abs(Mp-Mv))<1e-10)
    out['decision']='FAST_AFFINE_TRANSFORM_VALIDATED' if out['success'] else 'FAST_AFFINE_TRANSFORM_FAILED_VALIDATION'
except Exception as e:
    out['error_type']=type(e).__name__; out['error']=str(e)[:1000]; out['decision']='INFRASTRUCTURE_FAILURE'
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(OUT.read_text())
