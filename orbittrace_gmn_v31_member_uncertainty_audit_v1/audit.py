#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,gzip,hashlib,json,math,tempfile,urllib.request
from pathlib import Path

YEARS=(2022,2023); MONTHS=range(1,13); BLIND=(20.0,55.0)
URL='https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt'
IDX={'id':0,'sol':5,'ra':7,'ra_sigma':8,'dec':9,'dec_sigma':10,'vg':15,'vg_sigma':16,'Qc':80,'fiterr':81,'num_stat':84}
USER_AGENT='orbittrace-v31-member-uncertainty-audit/1.0'

def req(x,m):
    if not x: raise RuntimeError(m)
def f(row,k):
    s=row[IDX[k]].strip(); x=float(s); req(math.isfinite(x),f'nonfinite {k}'); return x
def i(row,k):
    x=f(row,k); req(abs(x-round(x))<=1e-8,f'noninteger {k}'); return int(round(x))
def download(url,path):
    h=hashlib.sha256(); n=0
    request=urllib.request.Request(url,headers={'User-Agent':USER_AGENT})
    with urllib.request.urlopen(request,timeout=300) as r, path.open('wb') as o:
        while True:
            b=r.read(1024*1024)
            if not b: break
            h.update(b); n+=len(b); o.write(b)
        return {'url':url,'bytes':n,'sha256':h.hexdigest(),'last_modified':r.headers.get('Last-Modified')}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--p19-prelabel',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    payload=json.loads(a.p19_prelabel.read_text()); hard=payload['hard_families']; req(len(hard)==226,'hard family count changed')
    wanted={y:set() for y in YEARS}
    for fam in hard:
        for eid0 in fam['event_ids']:
            eid=str(eid0); y=int(eid[:4]);
            if y in wanted: wanted[y].add(eid)
    req(len(wanted[2022])==4726 and len(wanted[2023])==4068,'fixed member universe changed')
    found={y:{} for y in YEARS}; sources=[]
    with tempfile.TemporaryDirectory(prefix='orbittrace_member_uncertainty_') as td:
        root=Path(td)
        for y in YEARS:
            for m in MONTHS:
                path=root/f'{y}{m:02d}.txt'; src=download(URL.format(year=y,month=m),path); src.update({'year':y,'month':m}); sources.append(src)
                with path.open('r',encoding='utf-8-sig',errors='replace',newline='') as h:
                    for row in csv.reader(h,delimiter=';'):
                        if not row or row[0].lstrip().startswith('#'): continue
                        eid=row[0].strip()
                        if eid not in wanted[y]: continue  # firewall: no nonmember scientific columns are accessed
                        req(eid not in found[y],f'duplicate member row {eid}')
                        req(len(row)>IDX['num_stat'],f'truncated member row {eid}')
                        sol=f(row,'sol'); req(not (BLIND[0] <= sol <= BLIND[1]),f'protected member row {eid}')
                        ra=f(row,'ra'); dec=f(row,'dec'); vg=f(row,'vg'); ras=f(row,'ra_sigma'); decs=f(row,'dec_sigma'); vgs=f(row,'vg_sigma')
                        req(0<=ra<360 and -90<=dec<=90 and vg>0 and ras>=0 and decs>=0 and vgs>=0,f'invalid physical member row {eid}')
                        found[y][eid]={'id':eid,'year':y,'sol':sol,'ra':ra,'dec':dec,'vg':vg,'ra_sigma':ras,'dec_sigma':decs,'vg_sigma':vgs,'Qc':f(row,'Qc'),'fiterr':f(row,'fiterr'),'num_stat':i(row,'num_stat')}
                path.unlink(missing_ok=True)
    for y in YEARS: req(set(found[y])==wanted[y],f'missing fixed v31 members in {y}: {len(wanted[y]-set(found[y]))}')
    out=a.output/'GMN_V31_FIXED_MEMBER_UNCERTAINTY_V1.jsonl.gz'
    with gzip.open(out,'wt',encoding='utf-8') as g:
        for y in YEARS:
            for eid in sorted(found[y]): g.write(json.dumps(found[y][eid],sort_keys=True)+'\n')
    result={'verdict':'PASS_GMN_V31_MEMBER_UNCERTAINTY_AUDIT_V1','scientific_endpoint_computed':False,'candidate_ranking_computed':False,'truth_metric_computed':False,'member_counts':{str(y):len(found[y]) for y in YEARS},'total_member_rows':sum(map(len,found.values())),'source_month_count':len(sources),'sources':sources,'enriched_member_file_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'blind_exclusion':[20.0,55.0],'sonotaco_2013_2014_access':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    (a.output/'GMN_V31_MEMBER_UNCERTAINTY_AUDIT_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({k:v for k,v in result.items() if k!='sources'},indent=2,sort_keys=True))
if __name__=='__main__': main()
