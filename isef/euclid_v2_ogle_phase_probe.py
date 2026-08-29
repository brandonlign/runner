#!/usr/bin/env python3
"""Metadata-only Euclid v2 kill test using OGLE EB eclipse epochs.

No Euclid science pixels/fluxes are read. The script uses released Euclid FITS
headers for timestamps/WCS coverage and the published OGLE bulge EB catalog for
coordinates, periods, primary-eclipse epochs, depths, and magnitudes. It asks
whether any *routable* known EB is predicted, at the catalog's stated numeric
precision, to have one or more Q2 exposures near primary eclipse and others well
away from eclipse. Any survivor is only a candidate for an external control; its
OGLE time series must then be re-fit to establish ephemeris uncertainty before
Euclid flux is inspected.
"""
import json, math, urllib.request
from pathlib import Path
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
import euclid_routed_feasibility as b
import euclid_exact_routing as er

BASE='https://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/blg/ecl'
OUT=Path('results/euclid_v2_ogle_phase_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
CENTER=(267.45,-30.05); RAD=0.60
# Published fixed-width precision: period F12.7 d, epoch F9.4 d.
PERIOD_QUANT_HALF=0.5e-7
EPOCH_QUANT_HALF=0.5e-4

def fetch(name):
    req=urllib.request.Request(f'{BASE}/{name}',headers={'User-Agent':'isef-euclid-v2-ogle-phase/1.0'})
    with urllib.request.urlopen(req,timeout=240) as r:return r.read().decode('ascii',errors='replace')
def parse_ident(txt):
    d={}
    for line in txt.splitlines():
        if len(line)<48: continue
        try:
            sid=line[0:19].strip(); sub=line[21:24].strip(); rah=int(line[25:27]); ram=int(line[28:30]); ras=float(line[31:36]); sgn=-1 if line[37:38]=='-' else 1; dd=int(line[38:40]); dm=int(line[41:43]); ds=float(line[44:48]);
            d[sid]={'id':sid,'subtype':sub,'ra':15*(rah+ram/60+ras/3600),'dec':sgn*(dd+dm/60+ds/3600)}
        except Exception: pass
    return d
def parse_ecl(txt):
    d={}
    for line in txt.splitlines():
        if len(line)<65: continue
        try:
            sid=line[0:19].strip(); imag=float(line[21:27]); vm=line[28:34].strip(); p=float(line[35:47]); ep=float(line[49:58]); dep=float(line[60:65]); sec=line[66:71].strip()
            d[sid]={'imag':imag,'vmag':float(vm) if vm else None,'period_days':p,'epoch_hjd_minus2450000':ep,'primary_depth_mag':dep,'secondary_depth_mag':float(sec) if sec else None}
        except Exception: pass
    return d
def sep(ra,de):
    return math.hypot((ra-CENTER[0])*math.cos(math.radians((de+CENTER[1])/2)),de-CENTER[1])
def euclid_times():
    out=[]
    for e in range(16):
        h=b.getq(e,0).raw; iso=h.get('DATE-OBS') or h.get('DATEOBS');
        if iso: t=Time(str(iso),format='isot',scale='utc')
        else: t=Time(float(h.get('MJD-OBS',h.get('MJDOBS'))),format='mjd',scale='utc')
        t=t+0.5*float(h.get('EXPTIME',400.0))*u.s
        out.append({'epoch':e,'jd_utc_mid':float(t.jd),'utc_mid_isot':t.utc.isot})
    return out
def hjd(jd,ra,de):
    t=Time(jd,format='jd',scale='utc',location=EarthLocation.from_geocentric(0,0,0,u.m)); sc=SkyCoord(ra*u.deg,de*u.deg)
    return float((t+t.light_travel_time(sc,kind='heliocentric')).jd)
def pdist(ph): return abs((ph+0.5)%1.0-0.5)
def main():
    ident=parse_ident(fetch('ident.dat')); ecl=parse_ecl(fetch('ecl.dat')); ts=euclid_times(); gm=er.map_groups(); selected=[]; routed=0; route_fail=0
    for sid,a in ident.items():
        p=ecl.get(sid)
        if not p: continue
        r={**a,**p}
        if sep(r['ra'],r['dec'])>RAD or r['period_days']>0.5 or r['period_days']<0.12 or r['primary_depth_mag']<0.20 or r['imag']>19.5: continue
        try: routes,diag=er.route_target(gm,(r['ra'],r['dec'])); routed+=1
        except Exception: route_fail+=1; continue
        ep=2450000.0+r['epoch_hjd_minus2450000']; P=r['period_days']; phases=[]; near=[]; far=[]; max_qsig=0
        for z in ts:
            h=hjd(z['jd_utc_mid'],r['ra'],r['dec']); cycles=(h-ep)/P; ph=cycles%1.0; n=abs(cycles)
            # Numeric-precision lower bound only, deliberately *not* called a physical ephemeris error.
            dtq=EPOCH_QUANT_HALF+n*PERIOD_QUANT_HALF; qsig=dtq/P; max_qsig=max(max_qsig,qsig); d=pdist(ph)
            if d+qsig<=0.055: near.append(z['epoch'])
            if d-qsig>=0.18: far.append(z['epoch'])
            phases.append({'epoch':z['epoch'],'hjd_utc_mid':h,'phase':ph,'distance_primary':d,'catalog_quantization_phase_bound':qsig})
        if near and len(far)>=3:
            selected.append({**r,'routes':{str(k):int(v) for k,v in routes.items()},'route_diagnostics':diag,'near_primary_epochs':near,'far_primary_epochs':far,'max_catalog_quantization_phase_bound':max_qsig,'phases':phases})
    selected.sort(key=lambda x:(-x['primary_depth_mag'],x['max_catalog_quantization_phase_bound'],x['imag'],x['period_days']))
    out={'success':True,'decision':'OGLE_EPHEMERIS_REFIT_WORTHWHILE' if selected else 'OGLE_PHASE_CONTROL_NOT_FEASIBLE','ident_objects':len(ident),'ecl_objects':len(ecl),'exact_routed_metadata_candidates':routed,'routing_rejections':route_fail,'catalog_precision_phase_candidates':len(selected),'best_candidates':selected[:20],'euclid_times':ts,'note':'No Euclid science flux read. Phase uncertainty shown is ONLY a bound from catalog numeric precision; survivors require OGLE time-series ephemeris refit before qualifying as controls.'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
