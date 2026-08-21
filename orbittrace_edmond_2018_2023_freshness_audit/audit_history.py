#!/usr/bin/env python3
"""Repository-history-only scientific-freshness audit for EDMOND 2018-2023.

No EDMOND archive, scientific value, shower label, target-region datum, or OrbitTrace
information is accessed by this script. It only scans git history text.
"""
from __future__ import annotations
import json, re, subprocess
from pathlib import Path

OUT = Path("output"); OUT.mkdir(exist_ok=True)
TARGETS = tuple(range(2018, 2024))
SELF = (
    "orbittrace_edmond_2018_2023_freshness_audit/",
    ".github/workflows/orbittrace-edmond-2018-2023-freshness-audit",
)

def cmd(*a):
    return subprocess.check_output(a, text=True, stderr=subprocess.DEVNULL)

def refs():
    return [x for x in cmd("git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin").splitlines()
            if x and not x.endswith("/HEAD")]

def grep(ref, pat):
    p = subprocess.run(["git", "grep", "-n", "-I", "-E", pat, ref, "--"], text=True, capture_output=True)
    if p.returncode not in (0, 1):
        raise RuntimeError(p.stderr)
    out=[]; pref=ref+":"
    for line in p.stdout.splitlines():
        if not line.startswith(pref):
            continue
        parts=line[len(pref):].split(":",2)
        if len(parts)!=3:
            continue
        path,ln,text=parts
        if path.startswith(SELF):
            continue
        out.append({"ref":ref,"path":path,"line":int(ln),"text":text[:1000]})
    return out

def dedup(xs):
    seen=set(); out=[]
    for x in xs:
        k=(x["path"],x["line"],x["text"])
        if k not in seen:
            seen.add(k); out.append(x)
    return out

def years_in_range(t):
    s=set()
    for m in re.finditer(r"range\(\s*(\d{4})\s*,\s*(\d{4})\s*\)",t):
        a,b=map(int,m.groups())
        if 1900 <= a <= 2200 and 1900 <= b <= 2201 and b-a < 100:
            s.update(range(a,b))
    return s

def classify(h,y):
    p=h["path"].lower(); t=h["text"].lower(); yrs=years_in_range(h["text"])
    if "range(" in h["text"] and yrs and y not in yrs:
        return "range_excludes_target"
    if any(k in t for k in ("untouched","reserved","must not access","must not download","not downloaded",
                             "no edmond","no scientific","unread","freshness audit","history-only")):
        return "reservation_or_audit_only"
    if "edmond" not in p and "edmond" not in t:
        return "unrelated_year"
    return "potential_exposure"

def hits_for(rs,y):
    pats=[
        rf"iaumdcedmond{y}",
        rf"U2_{y}_EDM",
        rf"EDMOND[^\n]{{0,180}}{y}|{y}[^\n]{{0,180}}EDMOND",
        r"EDMOND[^\n]{0,200}range\([^\n]{0,100}\)|range\([^\n]{0,100}\)[^\n]{0,200}EDMOND",
    ]
    xs=[]
    for r in rs:
        for pat in pats:
            xs += grep(r,pat)
    xs=dedup(xs)
    for h in xs:
        h["classification"]=classify(h,y)
        h["dynamic_range_years"]=sorted(years_in_range(h["text"]))
    return xs

def main():
    rs=refs(); targets={}
    for y in TARGETS:
        hs=hits_for(rs,y)
        targets[str(y)]={
            "hits":hs,
            "potential_exposure_hits":[h for h in hs if h["classification"]=="potential_exposure"],
        }
    # Positive control: known-spent EDMOND 2017 must be visible in repository history.
    pc=[]
    for r in rs:
        pc += grep(r,r"(iaumdcedmond2017|EDMOND[^\n]{0,180}2017|2017[^\n]{0,180}EDMOND)")
    pc=dedup(pc)
    pc_actual=any(("edmond2017" in h["path"].lower()) or ("iaumdcedmond2017" in h["text"].lower()) for h in pc)
    clean=all(not targets[str(y)]["potential_exposure_hits"] for y in TARGETS)
    verdict="PASS_EDMOND_2018_2023_REPO_SCIENTIFIC_FRESHNESS_AUDIT" if clean and pc_actual else "FAIL_EDMOND_2018_2023_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    result={
        "verdict":verdict,
        "refs_scanned":len(rs),
        "catalogue_access_this_audit":False,
        "scientific_value_access_this_audit":False,
        "label_access_this_audit":False,
        "target_information_access":False,
        "targets":targets,
        "positive_control_2017_spent_detected":pc_actual,
        "positive_control_2017_hit_count":len(pc),
        "claim_boundary":"History-only audit. A pass would authorize only a separately frozen structure/schema audit before any EDMOND 2018-2023 scientific values or shower labels are opened; a fail leaves the affected year spent.",
    }
    p=OUT/"edmond_2018_2023_repo_freshness_audit.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith("FAIL_"):
        raise SystemExit(1)

if __name__=="__main__":
    main()
