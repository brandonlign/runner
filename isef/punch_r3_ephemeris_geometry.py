#!/usr/bin/env python3
"""Generate target-blind ephemeris geometry for the frozen PUNCH R3 intervals.

No PUNCH image pixels are opened. JPL Horizons supplies both comet and Sun sky
coordinates from the same Earth-geocenter observer and epochs. This prevents
origin/frame mismatches in the projected anti-solar direction.
"""
from __future__ import annotations

import json
import time as time_module
from datetime import datetime, timedelta, timezone
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord
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
OBSERVER = "500@399"


def epochs(start: datetime, n: int):
    return [start + timedelta(minutes=CADENCE_MIN*i) for i in range(n)]


def horizons_batch(times: list[datetime], *, object_id: str, id_type=None):
    t=Time(times)
    last=None
    for attempt in range(RETRIES):
        try:
            obj=Horizons(id=object_id,id_type=id_type,location=OBSERVER,epochs=t.jd.tolist())
            return obj.ephemerides(quantities="1")
        except Exception as exc:
            last=exc
            if attempt+1<RETRIES:
                time_module.sleep(2*(attempt+1))
    raise RuntimeError(f"Horizons failed for {object_id!r} after {RETRIES} attempts") from last


def query_rows(label: str, times: list[datetime]):
    rows=[]
    for start in range(0,len(times),BATCH):
        chunk=times[start:start+BATCH]
        tc=Time(chunk)
        comet_eph=horizons_batch(chunk,object_id="C/2025 R3",id_type="designation")
        sun_eph=horizons_batch(chunk,object_id="10")
        if len(comet_eph)!=len(chunk) or len(sun_eph)!=len(chunk):
            raise RuntimeError("Horizons row mismatch")
        for i,dt in enumerate(chunk):
            # Both coordinates come from the same Horizons observer/service and
            # are treated as directions in the same ICRF-oriented sky frame.
            comet=SkyCoord(float(comet_eph["RA"][i])*u.deg,float(comet_eph["DEC"][i])*u.deg,frame="icrs")
            sun=SkyCoord(float(sun_eph["RA"][i])*u.deg,float(sun_eph["DEC"][i])*u.deg,frame="icrs")
            sep=float(comet.separation(sun).to_value(u.deg))
            pa=float((comet.position_angle(sun).to_value(u.deg)+180.0)%360.0)
            rows.append({
                "partition":label,
                "timestamp_utc":dt.isoformat().replace("+00:00","Z"),
                "jd_utc":float(tc[i].jd),
                "comet_ra_deg":float(comet_eph["RA"][i]),
                "comet_dec_deg":float(comet_eph["DEC"][i]),
                "sun_ra_deg":float(sun_eph["RA"][i]),
                "sun_dec_deg":float(sun_eph["DEC"][i]),
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
    # Sanity check: R3 is a near-Sun PUNCH target around perihelion. A grossly
    # inconsistent elongation indicates a frame/origin bug and must fail closed.
    if not all(0.0 < r["sun_comet_separation_deg"] < 60.0 for r in rows):
        raise RuntimeError("implausible Sun-comet elongation; reject geometry")
    report={
      "information_barrier":"matched JPL Horizons Sun + comet ephemerides only; no PUNCH target image pixels opened",
      "observer":OBSERVER,
      "designation":"C/2025 R3",
      "sun_horizons_id":"10",
      "frozen_partitions":{"primary_n":PRIMARY_N,"holdout_n":HOLDOUT_N,"cadence_min":CADENCE_MIN},
      "axis_rule":"local tangent-plane anti-solar PA = PA(comet->Sun)+180 deg; no image-based optimization",
      "rows":rows,
    }
    (OUT/"geometry.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "n_rows":len(rows),
      "primary_n":sum(r["partition"]=="primary" for r in rows),
      "holdout_n":sum(r["partition"]=="holdout" for r in rows),
      "sun_ra_first":rows[0]["sun_ra_deg"],
      "sun_dec_first":rows[0]["sun_dec_deg"],
      "separation_deg_range":[min(r["sun_comet_separation_deg"] for r in rows),max(r["sun_comet_separation_deg"] for r in rows)],
      "pa_deg_range":[min(r["antisolar_pa_east_of_north_deg"] for r in rows),max(r["antisolar_pa_east_of_north_deg"] for r in rows)],
    },indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
