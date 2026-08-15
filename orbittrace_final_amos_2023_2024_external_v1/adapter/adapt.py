#!/usr/bin/env python3
import argparse,csv,json,math
from datetime import datetime
from pathlib import Path
from transform import canonical_geometry
INDEX=['event_id','utc_time','solar_longitude_deg']
GEOM=['event_id','ra_j2000_deg','dec_j2000_deg','vg_km_s']
YEARS=(2023,2024)

def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def number(x):
    y=float(x); need(math.isfinite(y),'nonfinite value'); return y

def index_rows(path,year):
    out={}; seen=set()
    with path.open(newline='',encoding='utf-8') as f:
        r=csv.DictReader(f); need(r.fieldnames==INDEX,'wrong index header')
        for row in r:
            eid=row['event_id'].strip(); need(eid and eid not in seen,'bad index ID'); seen.add(eid)
            need(datetime.fromisoformat(row['utc_time'].replace('Z','+00:00')).year==year,'wrong year')
            sol=number(row['solar_longitude_deg']); need(0<=sol<360,'bad solar longitude')
            if not (20.0<=sol<=55.0): out[eid]=sol
    need(out,'no retained IDs'); return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--index',type=Path,required=True); p.add_argument('--geometry',type=Path,required=True); p.add_argument('--year',type=int,choices=YEARS,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    keep=index_rows(a.index,a.year); rows=[]; seen=set()
    with a.geometry.open(newline='',encoding='utf-8') as f:
        r=csv.DictReader(f); need(r.fieldnames==GEOM,'wrong geometry header')
        for x in r:
            eid=x['event_id'].strip(); need(eid in keep and eid not in seen,'geometry ID not retained/unique'); seen.add(eid)
            sol,slon,lat,vg=canonical_geometry(keep[eid],number(x['ra_j2000_deg']),number(x['dec_j2000_deg']),number(x['vg_km_s']))
            rows.append({'id':eid,'year':a.year,'sol':sol,'sun_lon':slon,'ecl_lat':lat,'vg':vg,'iau':0,'complex_key':'HIDDEN'})
    need(seen==set(keep),'geometry file must contain every retained ID and no others')
    rows.sort(key=lambda x:x['id']); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(rows,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps({'verdict':'PASS_AMOS_CANONICAL_ADAPTER_V1','year':a.year,'rows':len(rows),'labels_opened':False,'orbit_elements_opened':False},sort_keys=True))
if __name__=='__main__': main()
