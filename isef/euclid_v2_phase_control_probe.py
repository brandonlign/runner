#!/usr/bin/env python3
"""Euclid Q2 v2 kill test: can external Gaia EB ephemerides predict eclipses in Q2?

This script deliberately does NOT read Euclid fluxes. It reads only released FITS
headers to recover observation times and Gaia DR3 eclipsing-binary model parameters.
A usable v2 control exists only if the Gaia ephemeris, propagated to the Euclid
observation date including frequency uncertainty, predicts at least one Euclid
exposure securely inside eclipse and at least one securely outside eclipse.
"""
import csv, io, json, math, urllib.parse, urllib.request
from pathlib import Path
import numpy as np
from astropy.table import Table
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
import euclid_routed_feasibility as b

OUT=Path('results/euclid_v2_phase_control_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
TAPS=['https://gea.esac.esa.int/tap-server/tap/sync','https://gaia.aip.de/tap/sync']
CENTER=(267.425,-30.019); RADIUS=0.48

def save(x): OUT.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n'); print(json.dumps(x,indent=2,sort_keys=True))
def parse(raw):
    txt=raw.decode('utf-8','replace')
    if 'value="ERROR"' in txt[:5000]: raise RuntimeError(txt[:2000])
    if '<VOTABLE' in txt[:1000]:
        t=Table.read(io.BytesIO(raw),format='votable')
        return [{str(n).lower():('' if np.ma.is_masked(r[n]) else str(r[n])) for n in t.colnames} for r in t]
    return [{str(k).lower():v for k,v in r.items()} for r in csv.DictReader(io.StringIO(txt))]
def tap(q):
    body=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q}).encode(); errs=[]
    for endpoint in TAPS:
        try:
            req=urllib.request.Request(endpoint,data=body,headers={'User-Agent':'isef-euclid-v2-phase-control/1.0','Content-Type':'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(req,timeout=40) as r: return parse(r.read()),endpoint
        except Exception as e: errs.append(f'{endpoint}: {type(e).__name__}: {e}')
    raise RuntimeError('; '.join(errs))

def header_times():
    out=[]
    # One SCI extension per exposure is sufficient because timing is exposure-global.
    for e in range(16):
        q=b.getq(e,0); h=q.raw
        keys={k:h.get(k) for k in ('DATE-OBS','DATEOBS','MJD-OBS','MJDOBS','EXPSTART','EXPTIME') if k in h}
        iso=h.get('DATE-OBS') or h.get('DATEOBS')
        if iso:
            t=Time(str(iso),format='isot',scale='utc')
        elif h.get('MJD-OBS') is not None:
            t=Time(float(h['MJD-OBS']),format='mjd',scale='utc')
        elif h.get('MJDOBS') is not None:
            t=Time(float(h['MJDOBS']),format='mjd',scale='utc')
        else:
            raise RuntimeError(f'no observation time in epoch {e}; keys={sorted(h)}')
        exptime=float(h.get('EXPTIME',400.0)); tmid=t+0.5*exptime*u.s
        out.append({'epoch':e,'header_time':keys,'utc_mid_isot':tmid.utc.isot,'jd_utc_mid':float(tmid.utc.jd)})
    return out

def bjdtcb(jdutc,ra,dec):
    t=Time(jdutc,format='jd',scale='utc',location=EarthLocation.from_geocentric(0,0,0,u.m))
    sc=SkyCoord(ra*u.deg,dec*u.deg,frame='icrs')
    ltt=t.light_travel_time(sc,kind='barycentric')
    tb=(t.tdb+ltt).tcb
    return float(tb.jd)
def phase_dist(x,c):
    d=abs((x-c+0.5)%1.0-0.5); return d

def main():
    try: times=header_times()
    except Exception as e: return save({'success':False,'stage':'header_times','error':f'{type(e).__name__}: {e}'})
    ra,de=CENTER
    q=f"""SELECT TOP 500 gs.source_id AS sid,gs.ra AS cra,gs.dec AS cdec,gs.phot_g_mean_mag AS gmag,v.global_ranking AS rank,v.reference_time AS tref,v.frequency AS freq,v.frequency_error AS ferr,v.derived_primary_ecl_phase AS pphase,v.derived_primary_ecl_phase_error AS pphaseerr,v.derived_primary_ecl_duration AS pdur,v.derived_primary_ecl_depth AS pdepth,v.derived_secondary_ecl_phase AS sphase,v.derived_secondary_ecl_phase_error AS sphaseerr,v.derived_secondary_ecl_duration AS sdur,v.derived_secondary_ecl_depth AS sdepth FROM gaiadr3.gaia_source AS gs JOIN gaiadr3.vari_eclipsing_binary AS v ON gs.source_id=v.source_id WHERE 1=CONTAINS(POINT('ICRS',gs.ra,gs.dec),CIRCLE('ICRS',{ra},{de},{RADIUS})) AND gs.phot_g_mean_mag BETWEEN 16.0 AND 19.0 AND v.global_ranking>=0.5 AND v.derived_primary_ecl_depth>=0.15 AND v.derived_primary_ecl_duration>=0.02 AND v.frequency>0 AND v.frequency_error IS NOT NULL ORDER BY v.derived_primary_ecl_depth DESC"""
    try: rows,endpoint=tap(q)
    except Exception as e: return save({'success':False,'stage':'gaia_query','error':f'{type(e).__name__}: {e}','query':q,'euclid_times':times})
    candidates=[]
    for r in rows:
        try:
            sid=str(r['sid']); cra=float(r['cra']); cdec=float(r['cdec']); freq=float(r['freq']); ferr=float(r['ferr']); tref=float(r['tref'])+2455197.5
            pp=float(r['pphase']); ppe=float(r['pphaseerr'] or 0); pdur=float(r['pdur']); pdepth=float(r['pdepth'])
            phases=[]; securely_in=[]; securely_out=[]
            for z in times:
                tb=bjdtcb(z['jd_utc_mid'],cra,cdec); dt=tb-tref; ph=(dt*freq)%1.0
                # Conservative 1-sigma phase uncertainty from catalog phase+frequency only.
                sig=math.hypot(ppe,abs(dt)*ferr)
                d=phase_dist(ph,pp); half=pdur/2
                inside=d+sig < half
                outside=d-sig > half
                phases.append({'epoch':z['epoch'],'bjd_tcb':tb,'phase':ph,'phase_sigma_1s':sig,'distance_primary_phase':d,'securely_inside_primary_1s':inside,'securely_outside_primary_1s':outside})
                if inside: securely_in.append(z['epoch'])
                if outside: securely_out.append(z['epoch'])
            usable=bool(securely_in and securely_out and max(p['phase_sigma_1s'] for p in phases)<0.25)
            candidates.append({'source_id':sid,'ra':cra,'dec':cdec,'gmag':float(r['gmag']),'global_ranking':float(r['rank']),'frequency_per_day':freq,'frequency_error_per_day':ferr,'period_hours':24/freq,'reference_bjd_tcb':tref,'primary_phase':pp,'primary_phase_error':ppe,'primary_duration_phase':pdur,'primary_depth_mag':pdepth,'secure_in_epochs':securely_in,'secure_out_epochs':securely_out,'max_phase_sigma_1s':max(p['phase_sigma_1s'] for p in phases),'usable_phase_control':usable,'phases':phases})
        except Exception as e:
            candidates.append({'source_id':str(r.get('sid')),'parse_error':f'{type(e).__name__}: {e}'})
    usable=[x for x in candidates if x.get('usable_phase_control')]
    usable.sort(key=lambda x:(-x['primary_depth_mag'],x['max_phase_sigma_1s'],x['gmag']))
    save({'success':True,'endpoint':endpoint,'query':q,'gaia_rows':len(rows),'euclid_times':times,'usable_phase_controls':len(usable),'best_usable_controls':usable[:30],'decision':'V2_PHASE_CONTROL_FEASIBLE' if usable else 'V2_PHASE_CONTROL_NOT_FEASIBLE','note':'No Euclid flux values were read. Selection uses only FITS timing/WCS-neutral metadata and Gaia DR3 ephemerides.'})
if __name__=='__main__': main()
