#!/usr/bin/env python3
import csv,json,subprocess,sys,tempfile
from pathlib import Path

H=['event_id','utc_time','solar_longitude_deg']

def make(path,reps):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(H)
        for deg in range(360):
            for rep in range(reps):
                w.writerow([f'e{deg:03d}_{rep}','2023-01-01T00:00:00Z',str(float(deg))])

def run(script,index,out):
    p=subprocess.run([sys.executable,str(script),'--index',str(index),'--year','2023','--output',str(out)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    return json.loads(out.read_text())

def main():
    script=Path(__file__).with_name('audit.py')
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); idx=root/'index.csv'; out=root/'result.json'
        make(idx,5); dense=run(script,idx,out)
        assert dense['verdict']=='PASS' and dense['scannable_bin_count']==30 and dense['retained']==1620
        make(idx,4); sparse=run(script,idx,out)
        assert sparse['verdict']=='FAIL' and sparse['scannable_bin_count']==0 and sparse['retained']==1296
    print('PASS_AMOS_CAPACITY_V1_SELFTEST')
if __name__=='__main__': main()
