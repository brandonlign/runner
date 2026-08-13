#!/usr/bin/env python3
import csv,json,subprocess,sys,tempfile
from pathlib import Path
from adapt import index_rows
from transform import canonical_geometry

def put(path,header,rows):
    with path.open('w',newline='') as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows)

def main():
    here=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as td:
        r=Path(td); idx=r/'i.csv'; geom=r/'g.csv'; out=r/'o.json'
        put(idx,['event_id','utc_time','solar_longitude_deg'],[['a','2023-01-01T00:00:00Z','19.999'],['b','2023-01-01T00:00:00Z','20'],['c','2023-01-01T00:00:00Z','55'],['d','2023-01-01T00:00:00Z','55.001']])
        keep=index_rows(idx,2023); assert keep=={'a':19.999,'d':55.001}
        g=canonical_geometry(123.4,250.0,-30.0,42.1)
        assert abs(g[1]-129.2062932290088)<1e-12 and abs(g[2]+7.760417514308222)<1e-12
        assert canonical_geometry(0.0,180.0,0.0,10.0)[1]==-180.0
        put(geom,['event_id','ra_j2000_deg','dec_j2000_deg','vg_km_s'],[['a','0','0','20'],['b','0','0','20'],['d','0','0','20']])
        cmd=[sys.executable,str(here/'adapt.py'),'--index',str(idx),'--geometry',str(geom),'--year','2023','--output',str(out)]
        bad=subprocess.run(cmd,capture_output=True,text=True); assert bad.returncode!=0 and 'geometry ID not retained/unique' in bad.stderr
        put(geom,['event_id','ra_j2000_deg','dec_j2000_deg','vg_km_s'],[['a','0','0','20'],['d','0','0','20']])
        good=subprocess.run(cmd,capture_output=True,text=True); assert good.returncode==0,good.stderr
        rows=json.loads(out.read_text()); assert [x['id'] for x in rows]==['a','d'] and all(x['iau']==0 and x['complex_key']=='HIDDEN' for x in rows)
    print('PASS_AMOS_CANONICAL_ADAPTER_SELFTEST')
if __name__=='__main__': main()
