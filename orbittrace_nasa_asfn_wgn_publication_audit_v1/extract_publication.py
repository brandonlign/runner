#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

TITLE = "seven years of bright meteor data from the nasa all sky fireball network"
TOKENS = (
    "data release", "available", "availability", "download", "database", "website",
    "fireballs.ndc.nasa.gov", "supplement", "catalog", "catalogue", "repository",
    "33,660", "33660",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def main() -> int:
    root = Path("wgn")
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    matches = []
    inventory = []
    for pdf in sorted(root.rglob("*.pdf")):
        txt = out / (pdf.name + ".txt")
        subprocess.check_call(["pdftotext", "-layout", str(pdf), str(txt)])
        text = txt.read_text(errors="replace")
        inventory.append({"path": str(pdf), "sha256": sha(pdf), "bytes": pdf.stat().st_size})
        if TITLE in norm(text):
            matches.append((pdf, txt, text))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one WGN issue containing title; found {len(matches)}")
    pdf, txt, text = matches[0]
    lines = text.splitlines()
    rx = re.compile("|".join(re.escape(t) for t in TOKENS), re.I)
    contexts = []
    seen = set()
    for i, line in enumerate(lines):
        if not rx.search(line):
            continue
        lo, hi = max(0, i - 4), min(len(lines), i + 5)
        key = (lo, hi)
        if key in seen:
            continue
        seen.add(key)
        contexts.append({"line_start": lo + 1, "line_end": hi, "lines": lines[lo:hi]})
    preserved_pdf = out / "KINGERY_WGN_2020_MATCHING_ISSUE.pdf"
    preserved_pdf.write_bytes(pdf.read_bytes())
    preserved_text = out / "KINGERY_WGN_2020_MATCHING_ISSUE.txt"
    preserved_text.write_text(text)
    report = {
        "stage": "NASA_ASFN_WGN_PUBLICATION_AUDIT_V1",
        "matching_issue_path": str(pdf),
        "matching_issue_sha256": sha(pdf),
        "matching_issue_bytes": pdf.stat().st_size,
        "archive_pdf_inventory": inventory,
        "fixed_tokens": list(TOKENS),
        "contexts": contexts,
        "wgn_publication_access": True,
        "asfn_event_data_access": False,
        "asfn_bulk_catalogue_access": False,
        "fireballs_site_access": False,
        "discovered_links_followed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (out / "NASA_ASFN_WGN_PUBLICATION_AUDIT_V1.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("stage", "matching_issue_path", "matching_issue_sha256")}, indent=2))
    print("contexts", len(contexts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
