#!/usr/bin/env python3
import math
OBLIQUITY_DEG=23.43928

def wrap180(x):
    return (float(x)+180.0)%360.0-180.0

def equatorial_to_ecliptic(ra_deg,dec_deg):
    ra=math.radians(float(ra_deg)); dec=math.radians(float(dec_deg)); eps=math.radians(OBLIQUITY_DEG)
    x=math.cos(dec)*math.cos(ra)
    y=math.cos(dec)*math.sin(ra)*math.cos(eps)+math.sin(dec)*math.sin(eps)
    z=-math.cos(dec)*math.sin(ra)*math.sin(eps)+math.sin(dec)*math.cos(eps)
    lon=math.degrees(math.atan2(y,x))%360.0
    lat=math.degrees(math.asin(max(-1.0,min(1.0,z))))
    return lon,lat

def canonical_geometry(sol_deg,ra_j2000_deg,dec_j2000_deg,vg_km_s):
    sol=float(sol_deg); ra=float(ra_j2000_deg); dec=float(dec_j2000_deg); vg=float(vg_km_s)
    if not (0<=sol<360 and 0<=ra<360 and -90<=dec<=90 and vg>0): raise RuntimeError('invalid geometry')
    lon,lat=equatorial_to_ecliptic(ra,dec)
    return sol,wrap180(lon-sol),lat,vg
