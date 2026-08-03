#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import requests

OUT = Path(__file__).resolve().parent / "results"
CACHE = Path(__file__).resolve().parent / "cache"
BASE = "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline"
SOURCES = {
    "CAMS": [BASE + "/iaumdcCAMSv3_2012.csv.zip", BASE + "/iaumdcCAMSv3_2016.csv.zip"],
    "SonotaCo": [BASE + "/iaumdcSNMv3_S12.csv.zip", BASE + "/iaumdcSNMv3_S23.csv.zip"],
    "EDMOND": [BASE + "/iaumdcedmond2014.csv.zip", BASE + "/iaumdcedmond2017.csv.zip"],
}

KNOWN_CODES = {
    "PER", "GEM", "QUA", "LEO", "ORI", "ETA", "DRA", "LYR", "URS",
    "CAP", "STA", "NTA", "AND", "JBO", "TAH", "CAM", "PHO", "PPU",
}
COLUMN_TERMS = ("shower", "stream", "iau", "code", "association", "assoc", "class", "group")


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lstrip("\ufeff").strip().lower())


def get(url: str, path: Path) -> tuple[bytes, dict[str, object]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        raw = path.read_bytes()
        cached = True
    else:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        raw = response.content
        path.write_bytes(raw)
        cached = False
    return raw, {
        "url": url,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "cached": cached,
    }


def read_zip(raw: bytes) -> tuple[pd.DataFrame, str, str]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = [
            name for name in archive.namelist()
            if name.lower().endswith((".csv", ".txt")) and not name.startswith("__MACOSX/")
        ]
        if not members:
            raise RuntimeError("archive contains no CSV/TXT member")
        member = max(members, key=lambda name: archive.getinfo(name).file_size)
        data = archive.read(member)
    sample = data[:16384].decode("utf-8-sig", errors="replace")
    first = next((line for line in sample.splitlines() if line.strip()), "")
    separator = ";" if first.count(";") > first.count(",") else ","
    frame = pd.read_csv(io.BytesIO(data), sep=separator, low_memory=False, encoding="utf-8-sig")
    frame.columns = [str(column).lstrip("\ufeff").strip() for column in frame.columns]
    return frame, member, separator


def code_hits(series: pd.Series) -> dict[str, object]:
    values = series.dropna().astype(str).str.upper().str.strip()
    values = values[values.ne("")]
    counts: dict[str, int] = {}
    for value in values.head(100000):
        tokens = set(re.findall(r"[A-Z]{3}", value))
        for code in tokens & KNOWN_CODES:
            counts[code] = counts.get(code, 0) + 1
    return {
        "nonempty": int(len(values)),
        "unique": int(values.nunique()),
        "known_code_hits": int(sum(counts.values())),
        "known_codes": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
        "examples": values.drop_duplicates().head(20).tolist(),
    }


def inspect(source: str, url: str, index: int) -> dict[str, object]:
    raw, download = get(url, CACHE / source.lower() / f"sample_{index}.zip")
    frame, member, separator = read_zip(raw)
    normalized = {column: norm(column) for column in frame.columns}
    candidates = []
    for column, normalized_name in normalized.items():
        if any(term in normalized_name for term in COLUMN_TERMS):
            stats = code_hits(frame[column])
            candidates.append({"column": column, "normalized": normalized_name, **stats})
    candidates.sort(key=lambda row: (row["known_code_hits"], row["nonempty"]), reverse=True)
    return {
        "source": source,
        "download": download,
        "archive_member": member,
        "separator": separator,
        "rows": int(len(frame)),
        "columns": list(map(str, frame.columns)),
        "dtypes": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        "label_candidates": candidates,
        "head": frame.head(3).where(pd.notna(frame.head(3)), None).to_dict(orient="records"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    failures = []
    for source, urls in SOURCES.items():
        for index, url in enumerate(urls):
            try:
                results.append(inspect(source, url, index))
            except Exception as error:
                failures.append({"source": source, "url": url, "error": repr(error)})

    viable = []
    for result in results:
        best = result["label_candidates"][0] if result["label_candidates"] else None
        if best and best["known_code_hits"] >= 20:
            viable.append({
                "source": result["source"],
                "url": result["download"]["url"],
                "column": best["column"],
                "known_code_hits": best["known_code_hits"],
                "known_codes": best["known_codes"],
            })

    distinct_sources = sorted({entry["source"] for entry in viable})
    verdict = "DATA_LABEL_GATE_PASS" if len(distinct_sources) >= 2 else "DATA_LABEL_GATE_NO_GO"
    payload = {
        "verdict": verdict,
        "purpose": "Determine whether public orbit catalogues expose enough independent shower labels for a parent-body-disjoint Stage-0 pilot.",
        "results": results,
        "failures": failures,
        "viable_label_sources": viable,
        "distinct_viable_sources": distinct_sources,
        "gate": {
            "required_distinct_sources": 2,
            "minimum_known_code_hits_per_sample": 20,
            "passed": verdict == "DATA_LABEL_GATE_PASS",
        },
        "claim_boundary": "A pass only establishes label/data feasibility. It does not validate simulation-trained common-origin inference or methodological novelty.",
    }
    (OUT / "data_audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Common-origin pilot data audit",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        "This audit checks whether the public IAU MDC video-orbit catalogues expose usable shower-association labels in at least two independent networks.",
        "",
    ]
    for result in results:
        lines.extend([f"## {result['source']}", "", f"- Rows: **{result['rows']:,}**", f"- Columns: `{', '.join(result['columns'])}`"])
        if result["label_candidates"]:
            best = result["label_candidates"][0]
            lines.extend([
                f"- Best label candidate: `{best['column']}`",
                f"- Known-code hits: **{best['known_code_hits']:,}**",
                f"- Recognized codes: `{best['known_codes']}`",
            ])
        else:
            lines.append("- No plausible label column found.")
        lines.append("")
    if failures:
        lines.extend(["## Failures", "", "```json", json.dumps(failures, indent=2), "```", ""])
    lines.extend([
        "## Interpretation boundary",
        "",
        "Passing this gate means a parent-body-disjoint empirical/surrogate simulation pilot can be constructed. It does not mean that the public labels are perfect, that the parent mappings are unambiguous, or that a learned metric will outperform D-criteria.",
    ])
    (OUT / "DATA_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "viable_sources": distinct_sources, "failures": failures}, indent=2))


if __name__ == "__main__":
    main()
