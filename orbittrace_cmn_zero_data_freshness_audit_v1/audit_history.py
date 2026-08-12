#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT=Path("output")
AUDIT_PREFIX="orbittrace_cmn_zero_data_freshness_audit_v1/"
WORKFLOW_PATH=".github/workflows/orbittrace_cmn_zero_data_freshness_audit_v1.yml"
CURRENT_BRANCH="agent/orbittrace-cmn-zero-data-freshness-audit-v1"
PATTERNS=(
    r"Croatian Meteor Network",
    r"CroatianMeteorNetwork",
    r"CMN Orbit",
    r"CMN_Orbit",
    r"CMN-Orbit",
    r"cmn\.rgn\.hr",
)
POSITIVE=("FRIPON","UKMON")


def run(*args: str) -> str:
    return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT)


def historical_hits(pattern: str) -> list[dict[str,str]]:
    # Search every historical patch, while excluding this audit's own files.
    cmd=[
        "git","log","--all","-i",f"-G{pattern}",
        "--pretty=format:COMMIT:%H","--name-only","--",
        ".",f":!{AUDIT_PREFIX}",f":!{WORKFLOW_PATH}",
    ]
    text=run(*cmd)
    hits=[]; commit=""
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith("COMMIT:"):
            commit=line.split(":",1)[1]
        elif line and commit:
            hits.append({"commit":commit,"path":line})
    # stable de-duplication
    seen=set(); out=[]
    for h in hits:
        k=(h["commit"],h["path"])
        if k not in seen:
            seen.add(k); out.append(h)
    return out


def ref_hits() -> list[str]:
    refs=run("git","for-each-ref","--format=%(refname)","refs/heads","refs/remotes","refs/tags").splitlines()
    rx=re.compile("|".join(f"(?:{p})" for p in PATTERNS),re.I)
    out=[]
    for ref in refs:
        if CURRENT_BRANCH in ref:
            continue
        if rx.search(ref):
            out.append(ref)
    return sorted(set(out))


def main() -> int:
    OUT.mkdir(parents=True,exist_ok=True)
    cmn={p:historical_hits(p) for p in PATTERNS}
    positives={p:historical_hits(re.escape(p)) for p in POSITIVE}
    refs=ref_hits()
    any_cmn=any(cmn[p] for p in PATTERNS) or bool(refs)
    positive_ok=all(bool(positives[p]) for p in POSITIVE)
    passed=(not any_cmn) and positive_ok
    result={
        "stage":"CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT_V1",
        "verdict":"PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT" if passed else "FAIL_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT",
        "cmn_history_hits":cmn,
        "cmn_ref_hits":refs,
        "positive_control_hits":positives,
        "positive_controls_pass":positive_ok,
        "catalogue_network_access":False,
        "cmn_scientific_value_access":False,
        "cmn_event_identifier_access":False,
        "cmn_shower_label_access":False,
        "sonotaco_scientific_access":False,
        "maarsy_scientific_access":False,
        "dms_scientific_access":False,
        "target_information_access":False,
        "target_region_events_accessed":False,
        "claim_boundary":"A pass authorizes only a separately frozen structure-only public-interface audit before any CMN scientific/event-level access.",
    }
    path=OUT/"CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT_V1.json"
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if passed else 1

if __name__=="__main__":
    raise SystemExit(main())
