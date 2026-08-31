#!/usr/bin/env python3
"""Metadata-only direct SDAC inventory for the PUNCH C/2025 R3 interval.

This script reads Apache directory listings only. It does NOT download or open
any FITS image, so no quantitative comet morphology is exposed.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

OUT = Path("results/punch_r3_sdac_inventory")
OUT.mkdir(parents=True, exist_ok=True)
ROOT = "https://umbra.nascom.nasa.gov/punch"
START = datetime(2026, 4, 21, 18, 0, tzinfo=timezone.utc)
END = datetime(2026, 4, 22, 12, 0, tzinfo=timezone.utc)
DATES = ["2026/04/21", "2026/04/22"]

PRODUCTS = [
    ("L2_CTM", 2, "CTM"),
    ("L1_CR1", 1, "CR1"),
    ("L1_CR2", 1, "CR2"),
    ("L1_CR3", 1, "CR3"),
    ("L1_CR4", 1, "CR4"),
    ("L0_CR1", 0, "CR1"),
    ("L0_CR2", 0, "CR2"),
    ("L0_CR3", 0, "CR3"),
    ("L0_CR4", 0, "CR4"),
    ("L3_CIM", 3, "CIM"),
    ("L3_CTM", 3, "CTM"),
    ("L3_CAM", 3, "CAM"),
]

HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
FILE_RE = re.compile(r"PUNCH_L([0-3])_([A-Z0-9]+)_(\d{14})_v([A-Za-z0-9]+)\.fits$")


def parse_listing(url: str):
    try:
        r = requests.get(url, timeout=(5, 12))
        status = r.status_code
        if status != 200:
            return status, [], r.text[:500]
        files = []
        for href in HREF_RE.findall(r.text):
            name = href.rsplit("/", 1)[-1]
            m = FILE_RE.match(name)
            if not m:
                continue
            dt = datetime.strptime(m.group(3), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            files.append({
                "filename": name,
                "timestamp_utc": dt.isoformat(),
                "version": m.group(4),
                "level": int(m.group(1)),
                "code": m.group(2),
                "url": url + name,
            })
        return status, files, None
    except Exception as exc:
        return None, [], repr(exc)


def summarize(files):
    inwin = []
    for f in files:
        dt = datetime.fromisoformat(f["timestamp_utc"])
        if START <= dt <= END:
            inwin.append(f)

    by_time = {}
    for f in inwin:
        by_time.setdefault(f["timestamp_utc"], []).append(f)
    unique_times = sorted(by_time)
    selected = []
    for t in unique_times:
        selected.append(sorted(by_time[t], key=lambda x: x["version"])[-1])

    dts = [datetime.fromisoformat(x) for x in unique_times]
    gaps = [(b-a).total_seconds()/60 for a,b in zip(dts[:-1], dts[1:])]
    gaps_sorted = sorted(gaps)
    return {
        "n_fits_all_versions_in_window": len(inwin),
        "n_unique_epochs": len(unique_times),
        "versions": sorted({f["version"] for f in inwin}),
        "first_epoch_utc": unique_times[0] if unique_times else None,
        "last_epoch_utc": unique_times[-1] if unique_times else None,
        "median_cadence_min": gaps_sorted[len(gaps_sorted)//2] if gaps_sorted else None,
        "max_gap_min": max(gaps) if gaps else None,
        "selected_newest_per_epoch": selected,
    }


def main():
    result = {
        "information_barrier": "SDAC HTML directory listings only; no FITS bytes downloaded/opened",
        "interval_utc": [START.isoformat(), END.isoformat()],
        "products": {},
    }

    jobs = []
    for label, level, code in PRODUCTS:
        for day in DATES:
            url = f"{ROOT}/{level}/{code}/{day}/"
            jobs.append((label, day, url))

    fetched = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        future_map = {pool.submit(parse_listing, url): (label, day, url) for label, day, url in jobs}
        for fut in as_completed(future_map):
            label, day, url = future_map[fut]
            status, files, error = fut.result()
            fetched[(label, day)] = {
                "url": url,
                "http_status": status,
                "n_fits_links": len(files),
                "error": error,
                "files": files,
            }

    for label, _, _ in PRODUCTS:
        all_files = []
        listings = []
        for day in DATES:
            rec = fetched.get((label, day), {
                "url": "missing", "http_status": None, "n_fits_links": 0,
                "error": "future missing", "files": [],
            })
            listings.append({k: rec[k] for k in ["url", "http_status", "n_fits_links", "error"]})
            all_files.extend(rec["files"])
        result["products"][label] = {"listings": listings, **summarize(all_files)}

    l2 = result["products"]["L2_CTM"]
    l1_best = max(result["products"][f"L1_CR{i}"]["n_unique_epochs"] for i in range(1,5))
    l0_best = max(result["products"][f"L0_CR{i}"]["n_unique_epochs"] for i in range(1,5))
    l3_best = max(result["products"][x]["n_unique_epochs"] for x in ["L3_CIM","L3_CTM","L3_CAM"])

    if l2["n_unique_epochs"] >= 45 and (l2["median_cadence_min"] or 999) <= 12:
        classification = "PRIMARY_L2_ACCESS_PASS"
    elif l1_best >= 45:
        classification = "OFFICIAL_L1_FALLBACK_EXISTS"
    elif l0_best >= 45:
        classification = "PUBLIC_L0_RECONSTRUCTION_FALLBACK_EXISTS"
    elif l3_best >= 45:
        classification = "L3_ONLY_SEQUENCE_EXISTS"
    else:
        classification = "PUBLIC_SEQUENCE_ACCESS_FAIL"

    result["classification"] = classification
    result["best_epoch_counts"] = {
        "L2_CTM": l2["n_unique_epochs"],
        "L1_any_CR": l1_best,
        "L0_any_CR": l0_best,
        "L3_any_clear": l3_best,
    }

    (OUT / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if classification != "PUBLIC_SEQUENCE_ACCESS_FAIL" else 3


if __name__ == "__main__":
    raise SystemExit(main())
