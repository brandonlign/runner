#!/usr/bin/env python3
import json,sys
from pathlib import Path
import run as core

def arg(name):
    i=sys.argv.index(name); return Path(sys.argv[i+1])
def checked(path,year):
    x=json.loads(path.read_text()); core.need(isinstance(x,list) and x,'empty canonical file'); core.need(all(isinstance(r,dict) and r.get('year')==year for r in x),'wrong-year canonical row'); return [core.application.project_existing(r,allowed_years=core.Y) for r in x]
def main():
    sa=json.loads(arg('--source-audit-json').read_text()); core.need(sa.get('verdict')=='PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT','source audit failed'); core.need(sa.get('development_source_sha256')=='ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51','runtime source drift'); core.need(sa.get('support_source_sha256')=='fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62','support source drift')
    core.read=checked; core.main()
if __name__=='__main__': main()
