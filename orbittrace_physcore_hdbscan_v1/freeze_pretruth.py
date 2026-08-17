#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p:Path,o):
 raw=(json.dumps(o,indent=2,sort_keys=True)+'\n').encode();p.write_bytes(raw);return hashlib.sha256(raw).hexdigest()
def req(x,m):
 if not x: raise RuntimeError(m)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--rows',type=Path,required=True);ap.add_argument('--h13',type=Path,required=True);ap.add_argument('--h14',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 panels=[]
 for y,hd in ((2013,a.h13),(2014,a.h14)):
  c=a.input/f'physcore_{y}.json';m=a.input/f'physcore_{y}_manifest.json';r=a.rows/f'hdbscan_{y}.json';hp=hd/'comparator_primary_output.json';hm=hd/'comparator_source_manifest.json'
  d=json.loads(c.read_text());h=json.loads(hp.read_text());req(d['truth_accessed'] is False and d['target_information_access'] is False,'candidate firewall failure');req(len(d['families'])==len(h['families']),'budget changed')
  ids=sorted(str(x['id']) for x in json.loads(r.read_text())); ids_sha=hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest()
  panels.append({'year':y,'candidate_output_sha256':sha(c),'candidate_manifest_sha256':sha(m),'pairwise_rows_json_sha256':sha(r),'pairwise_event_ids_sha256':ids_sha,'hdbscan_primary_output_sha256':sha(hp),'hdbscan_source_manifest_sha256':sha(hm),'family_count':len(h['families'])})
 out={'schema':'ORBITTRACE_PHYSCORE_HDBSCAN_V1_PRETRUTH_FREEZE','pretruth_outputs_frozen':True,'truth_accessed_before_freeze':False,'source_sha256':sha(a.source),'protocol_sha256':sha(a.protocol),'panels':panels,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
 print(dump(a.output/'PRETRUTH_FREEZE.json',out))
if __name__=='__main__':main()
