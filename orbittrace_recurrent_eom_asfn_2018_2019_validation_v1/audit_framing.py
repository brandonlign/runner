#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ARCHIVE_SHA = "c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4"
DATA_BASENAME = "nasfn_2013-2019_data.txt"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def skeleton(s: str) -> str:
    out=[]; last_space=False
    for ch in s[:160]:
        if ch.isspace():
            if not last_space:
                out.append(" ")
            last_space=True
        else:
            last_space=False
            out.append("A" if ch.isalpha() else "D" if ch.isdigit() else ch)
    return "".join(out)


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--archive",type=Path,required=True); p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    if sha(a.archive)!=ARCHIVE_SHA: raise RuntimeError("archive changed")
    rows=[]
    with zipfile.ZipFile(a.archive) as z:
        ds=[i for i in z.infolist() if Path(i.filename).name==DATA_BASENAME]
        if len(ds)!=1: raise RuntimeError("data member ambiguity")
        with z.open(ds[0].filename) as f:
            physical=0
            for raw in f:
                physical += 1
                line=raw.decode("utf-8",errors="strict").rstrip("\r\n")
                if not line.strip(): continue
                toks=line.split()
                first=toks[0] if toks else ""
                rows.append({
                    "physical_line":physical,
                    "characters":len(line),
                    "whitespace_tokens":len(toks),
                    "tabs":line.count("\t"),"commas":line.count(","),"semicolons":line.count(";"),"pipes":line.count("|"),
                    "first_token_starts_four_digits":bool(re.match(r"^\d{4}",first)),
                    "first_token_if_digit_free":first[:64] if first and not any(c.isdigit() for c in first) else None,
                    "skeleton":skeleton(line),
                })
                if len(rows)>=8: break
    result={
        "verdict":"PASS_ASFN_DATA_FRAMING_ENGINEERING_AUDIT",
        "scientific_endpoint":False,"lines":rows,
        "scientific_field_values_reported":False,"shw_access":False,"performance_access":False,
        "target_information_access":False,"target_region_events_accessed":False,"maarsy_scientific_access":False,"dms_scientific_access":False,
    }
    (a.output/"ASFN_DATA_FRAMING_AUDIT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
