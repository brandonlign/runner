#!/usr/bin/env python3
"""Generate target-blind ephemeris geometry for the frozen PUNCH R3 intervals.

No PUNCH image pixels are opened. JPL Horizons supplies comet sky coordinates;
Astropy supplies the apparent Sun direction. Output is the mechanically fixed
nucleus coordinate and projected anti-solar position angle for every frozen
v0l epoch. Pixel coordinates are intentionally deferred to applying the audited
celestial WCS header at analysis time.
"""
from __future__ import annotations

import json
import time as time_module
from datetime import datetime, timedelta, timezone
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord, get_sun
from astropy.time import Time
from astroquery.jplhorizons import Horizons

OUT = Path("results/punch_r3_ephemeris_geometry")
OUT.mkdir(parents=True, exist_ok=True)

PRIMARY_START = datetime(2026,4,21,18,0,29,tzinfo=timezone.utc)
PRIMARY_N = 80
HOLDOUT_START = datetime(2026,4,22,4,56,29,tzinfo=timezone.utc)
HOLDOUT_N = 53
CADENCE_MIN = 8
BATCH = 12
RETRIES = 5


def epochs(start: datetime, n: int):
    return [start + timedelta(minutes=CADENCE_MIN*i) for i in range(n)]


def horizons_batch(times: list[datetime]):
    t=Time(times)
    last=None
    for attempt in range(RETRIES):
        try:
            obj=Horizons(id="C/2025 R3",id_type="designation",location="500@399",epochs=t.jd.tolist())
            return obj.ephemerides(quantities="1,3")
        except Exception as exc:
            last=exc
            if attempt+1<RETRIES:
                time_module.sleep(2*(attempt+1))
    raise RuntimeError(f"Horizons failed after {RETRIES} attempts") from last


def query_rows(label: str, times: list[datetime]):
    rows=[]
    for start in range(0,len(times),BATCH):
        chunk=times[start:start+BATCH]
        tc=Time(chunk)
        eph=horizons_batch(chunk)
        if len(eph)!=len(chunk):
            raise RuntimeError(f"Horizons row mismatch: {len(eph)} != {len(chunk)}")
        for i,dt in enumerate(chunk):
            comet=SkyCoord(float(eph["RA"][i])*u.deg,float(eph["DEC"][i])*u.deg,frame="icrs")
            sun=get_sun(Time(dt)).icrs
            # Local tangent-plane anti-solar direction at the comet: first find
            # the bearing FROM comet TO Sun, then reverse it by 180 degrees.
            # The earlier sun.position_angle(comet) value is a bearing at the
            # Sun and is not equivalent for a large (~131 deg) separation.
            pa=float((comet.position_angle(sun).to_value(u.deg)+180.0)%360.0)
            sep=float(comet.separation(sun).to_value(u.deg))
            rows.append({
                "partition":label,
                "timestamp_utc":dt.isoformat().replace("+00:00","Z"),
                "jd_utc":float(tc[i].jd),
                "comet_ra_deg":float(eph["RA"][i]),
                "comet_dec_deg":float(eph["DEC"][i]),
                "sun_ra_deg":float(sun.ra.deg),
                "sun_dec_deg":float(sun.dec.deg),
                "sun_comet_separation_deg":sep,
                "antisolar_pa_east_of_north_deg":pa,
            })
    return rows


def main():
    primary=epochs(PRIMARY_START,PRIMARY_N)
    holdout=epochs(HOLDOUT_START,HOLDOUT_N)
    rows=query_rows("primary",primary)+query_rows("holdout",holdout)
    if len(rows)!=PRIMARY_N+HOLDOUT_N:
        raise RuntimeError("incomplete frozen ephemeris geometry")
    report={
      "information_barrier":"JPL Horizons + Astropy Sun ephemeris only; no PUNCH target image pixels opened",
      "observer":"Earth geocenter (500@399); spacecraft-vs-geocenter parallax to be included as geometric systematic if needed",
      "designation":"C/2025 R3",
      "frozen_partitions":{"primary_n":PRIMARY_N,"holdout_n":HOLDOUT_N,"cadence_min":CADENCE_MIN},
      "axis_rule":"local tangent-plane anti-solar PA = PA(comet->Sun)+180 deg; no image-based optimization",
      "rows":rows,
    }
    (OUT/"geometry.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "n_rows":len(rows),
      "primary_n":sum(r["partition"]=="primary" for r in rows),
      "holdout_n":sum(r["partition"]=="holdout" for r in rows),
      "separation_deg_range":[min(r["sun_comet_separation_deg"] for r in rows),max(r["sun_comet_separation_deg"] for r in rows)],
      "pa_deg_range":[min(r["antisolar_pa_east_of_north_deg"] for r in rows),max(r["antisolar_pa_east_of_north_deg"] for r in rows)],
    },indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
