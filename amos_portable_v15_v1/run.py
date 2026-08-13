#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8
from orbittrace_sparse_support_multiplicity_v5 import run_holdout as mult
from orbittrace_v15_canonical_application_v1 import application
Y=(2023,2024); M=tuple(f'{y}-{m:02d}' for y in Y for m in range(1,13))
def need(x,m):
    if not x: raise RuntimeError(m)
def read(path,year):
    x=json.loads(path.read_text()); need(isinstance(x,list) and x,'empty canonical file'); return [application.project_existing(r,allowed_years=Y) for r in x if int(r['year'])==year]
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--y2023',type=Path,required=True); p.add_argument('--y2024',type=Path,required=True); p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True); p.add_argument('--source-audit-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    v6.YEARS=Y; v6.MONTH_KEYS=M; v8.YEARS=Y; v8.MONTH_KEYS=M; mult.YEARS=Y; mult.MONTH_KEYS=M; mult.TOP_K=100
    runtime=mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=Y; support.MONTH_KEYS=M; support.CORPUS='orbittrace-amos-2023-2024-portable-v15-v1'; support.RANKING_VARIANTS=('persistence','mean_year_strength','sqrt_support_strength','min_year_strength','size_penalized_strength')
    need(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval drift'); need(int(support.MIN_FAMILY_YEARS)==2,'recurrence drift'); need(abs(float(support.FAMILY_LINK_RADIUS)-1.5)<1e-15,'link radius drift'); need(int(support.MIN_COMPONENT_EVENTS)==4 and int(support.MIN_COMPONENT_QUARTETS)==2,'component gate drift'); need(int(support.SHORTLIST_K)==64 and int(support.AUDIT_SHORTLIST_K)==128,'shortlist drift'); need(int(support.MIN_ANCHOR_COUNT)==2 and int(support.MAX_QUARTETS_PER_BIN)==512,'proposal drift')
    setattr(a,'fixed4_baseline_json',a.source_audit_json); _candidate,base,_scorer=support.load_sources(a)
    scan={2023:read(a.y2023,2023),2024:read(a.y2024,2024)}; box={}
    def builder(years,canonical_scan):
        comps=[]; audits=[]
        for year in years:
            audit,_passing,c=v6.label_free_scan_year(year,canonical_scan[year],support,base); need(audit['calibration_events_used']==0 and audit['source_labels_used_for_proposals'] is False and audit['score_threshold_applied'] is False,'label-free boundary drift'); audits.append(audit); comps.extend(c)
        fam,_rank=support.build_families(comps,base); need(fam,'no recurrent families'); repair=v8.repair_year_centroids(fam,comps,canonical_scan,support,base); box.update(families=fam,scan_audits=audits,centroid_repair=repair); return fam
    result=application.run_pretruth(years=Y,scan_by_year=scan,family_builder=builder,runtime=runtime,base=base,score_episode=mult.score_episode); need(result['labels_read'] is False and result['survey_conditioned_science'] is False,'pretruth boundary drift')
    (a.output/'amos_v15_pretruth.json').write_text(json.dumps({k:v for k,v in result.items() if k!='component_scores'},indent=2,sort_keys=True,allow_nan=False)+'\n'); (a.output/'amos_v15_families.json').write_text(json.dumps(box['families'],separators=(',',':'),allow_nan=False)+'\n'); (a.output/'amos_v15_scan_audits.json').write_text(json.dumps(box['scan_audits'],indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':'PASS_AMOS_PORTABLE_V15_PRETRUTH_V1','family_count':result['family_count'],'v15_order_sha256':result['v15_order_sha256'],'labels_read':False},sort_keys=True))
if __name__=='__main__': main()
