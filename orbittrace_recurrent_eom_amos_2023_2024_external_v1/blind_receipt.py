#!/usr/bin/env python3
import argparse,csv,hashlib,json,math
from datetime import datetime
from pathlib import Path

EXPECTED=['event_id','utc_time','solar_longitude_deg']
YEARS={2023,2024}

def sha256(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def parse_utc(s):
    s=s.strip().replace('Z','+00:00')
    return datetime.fromisoformat(s)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--index',type=Path,required=True)
    ap.add_argument('--year',type=int,choices=sorted(YEARS),required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    kept=[]; seen=set(); total=excluded=0
    with a.index.open('r',encoding='utf-8',newline='') as f:
        r=csv.DictReader(f)
        if r.fieldnames!=EXPECTED: raise RuntimeError(f'exact header required: {EXPECTED}')
        for row in r:
            total+=1
            eid=row['event_id'].strip()
            if not eid or eid in seen: raise RuntimeError('blank or duplicate event_id')
            seen.add(eid)
            if parse_utc(row['utc_time']).year!=a.year: raise RuntimeError('wrong-year timestamp')
            sl=float(row['solar_longitude_deg'])
            if not math.isfinite(sl) or not (0.0<=sl<360.0): raise RuntimeError('invalid solar longitude')
            if 20.0<=sl<=55.0: excluded+=1
            else: kept.append(eid)
    if total==0: raise RuntimeError('empty index')
    kept_sorted=sorted(kept)
    (a.output/f'AMOS_{a.year}_RETAINED_IDS.txt').write_text('\n'.join(kept_sorted)+'\n')
    ids_hash=hashlib.sha256(('\n'.join(kept_sorted)+'\n').encode()).hexdigest()
    result={'verdict':'PASS_AMOS_BLIND_RECEIPT_V1','year':a.year,'input_sha256':sha256(a.index),'rows':total,'excluded_rows':excluded,'retained_rows':len(kept_sorted),'retained_ids_sha256':ids_hash,'protected_interval_inclusive':[20.0,55.0],'parsed_columns':EXPECTED,'scientific_values_emitted':False,'labels_opened':False}
    (a.output/f'AMOS_{a.year}_BLIND_RECEIPT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__': main()
