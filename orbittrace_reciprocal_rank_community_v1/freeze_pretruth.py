#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
YEARS=(2013,2014); METHOD="OrbitTrace Reciprocal Rank Communities v1"; LIT="catalogue HDBSCAN"
def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def dump(p,o):
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); Path(p).write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--prepare-dir",type=Path,required=True); ap.add_argument("--candidate-dir",type=Path,required=True)
    ap.add_argument("--hdbscan-2013-dir",type=Path,required=True); ap.add_argument("--hdbscan-2014-dir",type=Path,required=True); ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True); manp=a.candidate_dir/"candidate_source_manifest.json"; man=load(manp)
    req(man['method']==METHOD and man['truth_accessed'] is False and man['target_information_access'] is False,"candidate manifest invalid")
    hdirs={2013:a.hdbscan_2013_dir,2014:a.hdbscan_2014_dir}; panels=[]
    for y in YEARS:
        cp=a.candidate_dir/f"candidate_{y}.json"; c=load(cp); req(c['method']==METHOD and c['year']==y and c['truth_accessed'] is False,"candidate invalid")
        req(c['target_information_access'] is False and c['target_region_events_accessed'] is False,"candidate target access")
        fam=c['families']; req(len(fam)==c['family_count'] and [f['rank'] for f in fam]==list(range(1,len(fam)+1)),"candidate order")
        rp=a.prepare_dir/f"hdbscan_{y}.json"; rows=load(rp); ids=[str(r['id']) for r in rows]; req(len(ids)==len(set(ids)),"dupe ids")
        idsha=hashlib.sha256(("\n".join(sorted(ids))+"\n").encode()).hexdigest()
        hd=hdirs[y]; hp=hd/"comparator_primary_output.json"; hmp=hd/"comparator_source_manifest.json"; hsp=hd/"comparator_pretruth_summary.json"
        h=load(hp); hm=load(hmp); hs=load(hsp); req(h['method']==LIT and h['year']==y and h['truth_accessed'] is False,"HDB invalid")
        req(hm['target_information_access'] is False and hm['truth_labels_accepted'] is False,"HDB manifest invalid")
        B=int(h['retained_family_count']); req(B==len(h['families']) and B>0,"HDB budget"); req(len(fam)>=B,"candidate capacity below HDB")
        req(hs['primary_output_sha256']==sha(hp) and hs['source_manifest_sha256']==sha(hmp),"HDB hash")
        panels.append({"year":y,"event_count":len(rows),"event_ids_sha256":idsha,"rows_json_sha256":sha(rp),"candidate_primary_output_sha256":sha(cp),"candidate_source_manifest_sha256":sha(manp),"candidate_family_count":len(fam),"hdbscan_primary_output_sha256":sha(hp),"hdbscan_source_manifest_sha256":sha(hmp),"hdbscan_pretruth_summary_sha256":sha(hsp),"hdbscan_family_budget":B})
    f={"schema":"ORBITTRACE_RECIPROCAL_RANK_COMMUNITY_V1_HDBSCAN_PRETRUTH_FREEZE","method":METHOD,"literature_comparator":LIT,"pretruth_outputs_frozen":True,"panels":panels,"blind_exclusion":[20.0,55.0],"truth_accessed_before_freeze":False,"target_information_access":False,"target_region_events_accessed":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"post_result_parameter_search":False}
    fs=dump(a.output/"PRETRUTH_FREEZE.json",f); print(json.dumps({"verdict":"PASS_RECIPROCAL_RANK_COMMUNITY_V1_HDBSCAN_PRETRUTH_FREEZE","freeze_sha256":fs,"panels":len(panels)},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
