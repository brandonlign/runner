#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, importlib.util, json
from pathlib import Path
import numpy as np
from rate_balance import EXPOSURES, adjusted_score, compute_rate_balance

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
QUALITY_SHA="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_PRELABEL_SHA="efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
PARENT_RESULT_SHA="ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
PARENT_TOTAL_100=179
REQUIRED_GAIN=2


def req(x,msg):
    if not x: raise RuntimeError(msg)

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path); req(spec and spec.loader,f"cannot import {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def memberships(rows): return {tuple(sorted(str(x) for x in r["event_ids"])) for r in rows}

def order_sig(rows): return [tuple(sorted(str(x) for x in r["event_ids"])) for r in rows]


def main():
    ap=argparse.ArgumentParser()
    for name in ["parent-runner","parent-prelabel-json","parent-result-json","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json","output"]:
        ap.add_argument("--"+name,type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(EXPOSURES=={2022:315024,2023:423658},"exposures changed")
    req(sha(a.quality_source)==QUALITY_SHA,"runtime utility changed")
    req(sha(a.v8_result_json)==V8_RESULT_SHA,"support artifact changed")
    req(sha(a.parent_prelabel_json)==PARENT_PRELABEL_SHA,"#1263 prelabel changed")
    req(sha(a.parent_result_json)==PARENT_RESULT_SHA,"#1263 result changed")
    parent=load_module(a.parent_runner,"rate_balance_recurrent_parent")
    pp=json.loads(a.parent_prelabel_json.read_text()); pr=json.loads(a.parent_result_json.read_text())
    req(pp["scientific_role"]=="PRELABEL_FROZEN_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1","wrong parent prelabel")
    base_candidates=list(pp["successor_candidates"]); req(len(base_candidates)==2094,"parent count changed"); req(len(memberships(base_candidates))==2094,"duplicate parent membership")

    qmod=parent.load_module(a.quality_source,"rate_balance_frozen_gmn_utility")
    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-density-sync-rate-balance-v1-development-2022-2023-target-excluded"; support.RANKING_VARIANTS=("persistence",)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"blind changed")
    setattr(a,"fixed4_baseline_json",a.v8_result_json)
    _c,base,_s=support.load_sources(a); scan,_cal,hidden_sealed,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS),"wrong years"); req([x["key"] for x in sources]==list(MONTH_KEYS),"sources changed")
    events=[]
    for y in YEARS:
        raw=list(scan[y]); rows=[parent.normalize_event(r,y) for r in raw]; req(len(rows)==len(raw),"normalization changed"); events.extend(rows)
    req(len(events)==sum(EXPOSURES.values()),"pooled count changed")
    req(sum(e["year"]==2022 for e in events)==EXPOSURES[2022],"2022 exposure changed"); req(sum(e["year"]==2023 for e in events)==EXPOSURES[2023],"2023 exposure changed")
    req(all(not (BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected event survived")
    byid={str(e["id"]):e for e in events}; req(len(byid)==len(events),"duplicate event IDs")

    out=[]; balances=[]
    for i,c in enumerate(base_candidates):
        mids=tuple(sorted(str(x) for x in c["event_ids"])); req(len(mids)==int(c["member_count"]),f"member count mismatch {i}")
        stat=compute_rate_balance([byid[x] for x in mids]); score=adjusted_score(float(c["synchronous_stability"]),stat)
        row=dict(c); row.update({"rate_balance_score":score,"rate_balance":stat.balance,"annual_count_2022":stat.n_2022,"annual_count_2023":stat.n_2023,"annual_rate_2022":stat.rate_2022,"annual_rate_2023":stat.rate_2023})
        out.append(row); balances.append(stat.balance)
    out.sort(key=lambda f:(-f["rate_balance_score"],-f["synchronous_stability"],-f["ordinary_stability"],-f["member_count"],f["family_id"]))
    req(len(out)==2094 and memberships(out)==memberships(base_candidates),"membership universe changed")
    active=order_sig(out)!=order_sig(base_candidates)
    summary={"candidate_count":2094,"mean_balance":float(np.mean(balances)),"median_balance":float(np.median(balances)),"min_balance":float(np.min(balances)),"max_balance":float(np.max(balances)),"zero_balance":int(sum(x==0.0 for x in balances))}
    pre={"scientific_role":"PRELABEL_FROZEN_DENSITY_SYNC_RATE_BALANCE_V1","parent_prelabel_sha256":PARENT_PRELABEL_SHA,"candidate_count":2094,"membership_universe_identical":True,"mechanism_active":active,"score_summary":summary,"parent_candidates":base_candidates,"successor_candidates":out,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"sonotaco_2013_2014_access":False,"amos_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False}
    prepath=a.output/"DENSITY_SYNC_RATE_BALANCE_V1_PRELABEL.json"; prepath.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+"\n"); pre_sha=sha(prepath)

    hidden=hidden_sealed; ids={y:{str(e["id"]) for e in events if e["year"]==y} for y in YEARS}
    pm={str(y):parent.metrics(base_candidates,hidden,ids[y]) for y in YEARS}; sm={str(y):parent.metrics(out,hidden,ids[y]) for y in YEARS}; req(pm==pr["successor_metrics"],"#1263 metrics reproduction failed")
    gates={str(y):parent.annual_gate(pm[str(y)],sm[str(y)]) for y in YEARS}
    pt=sum(int(pm[str(y)]["recovered_at_100"]) for y in YEARS); st=sum(int(sm[str(y)]["recovered_at_100"]) for y in YEARS); req(pt==PARENT_TOTAL_100,"parent total changed")
    gain=st-pt; strong=gain>=REQUIRED_GAIN; passed=bool(active and strong and all(all(g.values()) for g in gates.values()))
    verdict="PASS_DENSITY_SYNC_RATE_BALANCE_V1_GMN_DEVELOPMENT" if passed else "FAIL_DENSITY_SYNC_RATE_BALANCE_V1_GMN_DEVELOPMENT"
    res={"verdict":verdict,"scientific_role":"TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY","prelabel_sha256":pre_sha,"parent_prelabel_sha256":PARENT_PRELABEL_SHA,"parent_result_sha256":PARENT_RESULT_SHA,"candidate_count":2094,"membership_universe_identical":True,"mechanism_active":active,"parent_total_recovered_at_100":pt,"successor_total_recovered_at_100":st,"total_recovered_at_100_gain":gain,"required_total_recovered_at_100_gain":REQUIRED_GAIN,"strong_recovery_gate":strong,"score_summary":summary,"parent_metrics":pm,"successor_metrics":sm,"annual_gates":gates,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"sonotaco_2013_2014_access":False,"amos_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False}
    (a.output/"DENSITY_SYNC_RATE_BALANCE_V1_GMN_DEVELOPMENT.json").write_text(json.dumps(res,indent=2,sort_keys=True,allow_nan=False)+"\n")
    def compact(m): return {k:v for k,v in m.items() if k!="first_rank_by_label"}
    print(json.dumps({"verdict":verdict,"gain":gain,"mechanism_active":active,"summary":summary,"parent":{y:compact(m) for y,m in pm.items()},"successor":{y:compact(m) for y,m in sm.items()},"annual_gates":gates},indent=2,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
