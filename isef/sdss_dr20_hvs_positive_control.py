#!/usr/bin/env python3
"""Literature-only positive control for the DR20 high-speed-star pipeline.
Uses published S5-HVS1 parameters; no SDSS source/candidate data are accessed.
"""
from pathlib import Path
import json,math
import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord,Galactocentric,CartesianDifferential,ICRS
from galpy.potential import MWPotential2014,evaluatePotentials
from galpy.potential.mwpotentials import McMillan17,Cautun20
from galpy.util.conversion import get_physical
OUT=Path('results/sdss_dr20_hvs_positive_control.json');OUT.parent.mkdir(parents=True,exist_ok=True)
GC=Galactocentric(galcen_coord=ICRS(ra=266.4051*u.deg,dec=-28.936175*u.deg),galcen_distance=8.122*u.kpc,galcen_v_sun=CartesianDifferential([12.9,245.6,7.78]*u.km/u.s),z_sun=20.8*u.pc,roll=0*u.deg)
# Koposov et al. 2020 published parameters, deliberately external to DR20.
P={'ra_deg':343.715345,'dec_deg':-51.195607,'pmra_masyr':35.328,'pmdec_masyr':0.587,'rv_kms':1017.0,'distance_kpc':9.0}
def esc(p,Rk,zK,ro,vo):
 R=Rk/ro;z=zK/ro;pin=float(evaluatePotentials(p,1e5,0,use_physical=False));pl=float(evaluatePotentials(p,R,z,use_physical=False));return math.sqrt(max(0.,2*(pin-pl)))*vo
def main():
 o={'success':False,'status':'LITERATURE_POSITIVE_CONTROL_ONLY','source_catalog_data_accessed':False,'published_input':P}
 try:
  c=SkyCoord(ra=P['ra_deg']*u.deg,dec=P['dec_deg']*u.deg,distance=P['distance_kpc']*u.kpc,pm_ra_cosdec=P['pmra_masyr']*u.mas/u.yr,pm_dec=P['pmdec_masyr']*u.mas/u.yr,radial_velocity=P['rv_kms']*u.km/u.s,frame='icrs');g=c.transform_to(GC)
  v=float(np.sqrt(g.v_x.to_value(u.km/u.s)**2+g.v_y.to_value(u.km/u.s)**2+g.v_z.to_value(u.km/u.s)**2));R=float(np.hypot(g.x.to_value(u.kpc),g.y.to_value(u.kpc)));z=abs(float(g.z.to_value(u.kpc)))
  models={'MWPotential2014':(MWPotential2014,8.,220.)}
  for n,p in [('McMillan17',McMillan17),('Cautun20',Cautun20)]:
   ph=get_physical(p);models[n]=(p,float(ph['ro']),float(ph['vo']))
  es={n:esc(p,R,z,ro,vo) for n,(p,ro,vo) in models.items()};margin={n:v-x for n,x in es.items()}
  o.update(galactocentric_speed_kms=v,galactocentric_R_kpc=R,abs_z_kpc=z,escape_speed_kms=es,margin_kms=margin,literature_reported_speed_kms=1755.,transform_within_150_kms_of_literature=abs(v-1755)<150,above_all_three_potentials=all(x>0 for x in margin.values()))
  o['success']=bool(o['transform_within_150_kms_of_literature'] and o['above_all_three_potentials']);o['decision']='KNOWN_HVS_POSITIVE_CONTROL_RECOVERED' if o['success'] else 'KNOWN_HVS_POSITIVE_CONTROL_FAILED'
 except Exception as e:o['error']=f'{type(e).__name__}: {e}';o['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__':main()
