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


def epochs(start: datetime, n: int):
    return [start + timedelta(minutes=CADENCE_MIN*i) for i in range(n)]


def query_rows(label: str, times: list[datetime]):
    t = Time(times)
    # Horizons accepts comet designations directly with id_type='designation'.
    obj = Horizons(id="C/2025 R3", id_type="designation", location="500@399", epochs=t.jd.tolist())
    eph = obj.ephemerides(quantities="1,3")
    rows=[]
    for i, dt in enumerate(times):
        comet=SkyCoord(float(eph["RA"][i])*u.deg,float(eph["DEC"][i])*u.deg,frame="icrs")
        sun=get_sun(Time(dt)).icrs
        # PA is measured east of north from the Sun toward the comet. Continuing
        # in this direction from the nucleus is the frozen projected anti-solar
        # downstream-axis prior.
        pa=float(sun.position_angle(comet).to_value(u.deg))
        sep=float(sun.separation(comet).to_value(u.deg))
        rows.append({
            "partition":label,
            "timestamp_utc":dt.isoformat().replace("+00:00","Z"),
            "jd_utc":float(t[i].jd),
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
    report={
      "information_barrier":"JPL Horizons + Astropy Sun ephemeris only; no PUNCH target image pixels opened",
      "observer":"Earth geocenter (500@399); spacecraft-vs-geocenter parallax to be included as geometric systematic if needed",
      "designation":"C/2025 R3",
      "frozen_partitions":{"primary_n":PRIMARY_N,"holdout_n":HOLDOUT_N,"cadence_min":CADENCE_MIN},
      "axis_rule":"projected anti-solar PA from Sun to comet; no image-based optimization",
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
