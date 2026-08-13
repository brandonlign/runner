#!/usr/bin/env python3
import csv,json,tempfile
from pathlib import Path
from adapt import index_rows
from transform import canonical_geometry

def put(path,header,rows):
    with path.open('w',newline='') as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows)

def main():
    with tempfile.TemporaryDirectory() as td:
        r=Path(td); idx=r/'i.csv'
        put(idx,['event_id','utc_time','solar_longitude_deg'],[['a','2023-01-01T00:00:00Z','19.999'],['b','2023-01-01T00:00:00Z','20'],['c','2023-01-01T00:00:00Z','55'],['d','2023-01-01T00:00:00Z','55.001']])
        keep=index_rows(idx,2023); assert keep=={'a':19.999,'d':55.001}
        g=canonical_geometry(100.0,0.0,0.0,20.0); assert g==(100.0,-100.0,0.0,20.0)
        g=canonical_geometry(0.0,90.0,0.0,30.0); assert abs(g[2]+23.43928)<1e-10
    print('PASS_AMOS_CANONICAL_ADAPTER_SELFTEST')
if __name__=='__main__': main()
