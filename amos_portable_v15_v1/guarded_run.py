#!/usr/bin/env python3
import hashlib,json,os,sys
from pathlib import Path
import run as core

PINS=((core.v6,'orbittrace_label_free_sparse_support_v6/run_development.py','7995fc6b75d1fd51eb4b304ace39db28a5a1e876'),(core.v8,'orbittrace_pooled_year_centroid_v8/run_development.py','f248df78e1258b132b41aecca6a985a5eb782654'),(core.mult,'orbittrace_sparse_support_multiplicity_v5/run_holdout.py','0136cb1603c947070947d1754bc83910b76415b9'))
def arg(name):
    i=sys.argv.index(name); return Path(sys.argv[i+1])
def blob(path):
    raw=path.read_bytes(); return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def guard_imports():
    root=Path(os.environ.get('ORBITTRACE_FROZEN_V8_ROOT','')).resolve(); core.need(root.is_dir(),'ORBITTRACE_FROZEN_V8_ROOT missing')
    for module,rel,want in PINS:
        path=(root/rel).resolve(); core.need(Path(module.__file__).resolve()==path,f'import escaped frozen root: {rel}'); core.need(blob(path)==want,f'frozen source drift: {rel}')
def checked(path,year):
    x=json.loads(path.read_text()); core.need(isinstance(x,list) and x,'empty canonical file'); core.need(all(isinstance(r,dict) and r.get('year')==year for r in x),'wrong-year canonical row'); return [core.application.project_existing(r,allowed_years=core.Y) for r in x]
def main():
    guard_imports(); sa=json.loads(arg('--source-audit-json').read_text()); core.need(sa.get('verdict')=='PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT','source audit failed'); core.need(sa.get('development_source_sha256')=='ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51','runtime source drift'); core.need(sa.get('support_source_sha256')=='fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62','support source drift')
    core.read=checked; core.main()
if __name__=='__main__': main()
