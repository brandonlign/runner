#!/usr/bin/env python3
import argparse,csv,json,math
from datetime import datetime
from pathlib import Path
H=['event_id','utc_time','solar_longitude_deg']; Y=(2023,2024)
def w(x): return (x+180)%360-180
def req(x,m):
    if not x: raise RuntimeError(m)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--index',type=Path,required=True); p.add_argument('--year',type=int,choices=Y,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); s=[]; ids=set()
    with a.index.open(newline='') as f:
        r=csv.DictReader(f); req(r.fieldnames==H,'header')
        for x in r:
            i=x['event_id'].strip(); req(i and i not in ids,'id'); ids.add(i); req(datetime.fromisoformat(x['utc_time'].replace('Z','+00:00')).year==a.year,'year')
            v=float(x['solar_longitude_deg']); req(math.isfinite(v) and 0<=v<360,'longitude')
            if not 20<=v<=55: s.append(v)
    req(s,'empty'); good=[]
    for b in range(36):
        lo=10*b; c=lo+5; anchors=sum(lo<=v<lo+10 for v in s); pool=sum(abs(w(v-c))<=15 for v in s)
        if anchors and pool>=128: good.append(b)
    o={'verdict':'PASS' if len(good)>=24 else 'FAIL','year':a.year,'retained':len(s),'scannable_bin_count':len(good),'scannable_bins':good,'min_required':24}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(o,sort_keys=True)+'\n'); print(json.dumps(o,sort_keys=True))
if __name__=='__main__': main()
