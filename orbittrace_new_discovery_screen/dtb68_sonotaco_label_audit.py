#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.astro.sk/iaumdcDB/public/data/SNMv3/{yy:03d}a.zip"
YEARS = range(2007, 2026)
TARGETS = {"2012/02/03T13:19:05", "2022/02/07T10:18:33"}
TOKENS = ("ECO", "FCM", "098", "111")


def load(year: int) -> tuple[pd.DataFrame, str]:
    url = URL.format(yy=year % 1000)
    response = requests.get(url, timeout=240)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith("_s.csv") and "__note" not in n.lower()]
        if not names:
            names = [n for n in archive.namelist() if n.lower().endswith(".csv") and "__note" not in n.lower()]
        if not names:
            raise RuntimeError(f"no data csv in {url}")
        name = names[0]
        frame = pd.read_csv(io.BytesIO(archive.read(name)), low_memory=False)
    frame.columns = [str(c).strip() for c in frame.columns]
    return frame, name


def clean(v):
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    return str(v) if not isinstance(v, (int, float, bool)) else v


def row_dict(row: pd.Series, year: int) -> dict:
    keys = ["day(UT)", "time(UT)", "sol(deg)", "ra(deg)", "de(deg)", "vg(km/s)", "a(AU)", "q(AU)", "e", "peri(deg)", "node(deg)", "incl(deg)", "Shower", "dr", "dv", "dd", "ZF"]
    out = {k: clean(row.get(k)) for k in keys if k in row.index}
    out["year"] = year
    return out


def main() -> int:
    out = Path("sonotaco_label_output")
    out.mkdir(exist_ok=True)
    target_rows = []
    label_rows = []
    yearly = {}
    for year in YEARS:
        frame, member = load(year)
        if "day(UT)" not in frame or "time(UT)" not in frame:
            raise RuntimeError(f"{year} schema missing day/time")
        identifiers = frame["day(UT)"].astype(str).str.strip() + "T" + frame["time(UT)"].astype(str).str.strip()
        tmask = identifiers.isin(TARGETS)
        for _, row in frame.loc[tmask].iterrows():
            target_rows.append(row_dict(row, year))
        if "Shower" in frame:
            labels = frame["Shower"].fillna("").astype(str).str.strip()
            upper = labels.str.upper()
            mask = False
            for token in TOKENS:
                mask = mask | upper.str.contains(token, regex=False)
            subset = frame.loc[mask]
            counts = labels.loc[mask].value_counts().to_dict()
            yearly[str(year)] = {"archive_member": member, "matching_rows": int(mask.sum()), "label_counts": {str(k): int(v) for k,v in counts.items()}}
            for _, row in subset.iterrows():
                label_rows.append(row_dict(row, year))
        else:
            yearly[str(year)] = {"archive_member": member, "matching_rows": 0, "label_counts": {}, "missing_shower_column": True}
        print(year, "targets", int(tmask.sum()), "label_matches", yearly[str(year)]["matching_rows"], flush=True)
    payload = {"stage":"dtb68_sonotaco_label_audit_v1","targets":sorted(TARGETS),"target_rows":target_rows,"label_match_rows":label_rows,"yearly":yearly}
    (out/"dtb68_sonotaco_label_audit.json").write_text(json.dumps(payload,indent=2)+"\n")
    lines=["# DTb68 SonotaCo source-label audit","",f"Exact selected rows recovered: **{len(target_rows)}**.","","## Exact DTb68 fixed-template members",""]
    for row in target_rows:
        lines.append(f"- `{row.get('day(UT)')}T{row.get('time(UT)')}`: Shower=`{row.get('Shower')}`, dr=`{row.get('dr')}`, dv=`{row.get('dv')}`, dd=`{row.get('dd')}`, sol=`{row.get('sol(deg)')}`, Vg=`{row.get('vg(km/s)')}`")
    lines += ["", "## Pre-existing ECO/FCM-like source labels", "", f"Rows across 2007-2025 containing ECO/FCM/098/111 in the source Shower field: **{len(label_rows)}**.", ""]
    for year in YEARS:
        info=yearly[str(year)]
        if info["matching_rows"]:
            lines.append(f"- {year}: {info['matching_rows']} rows; `{info['label_counts']}`")
    (out/"DTB68_SONOTACO_LABEL_AUDIT.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines),flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
