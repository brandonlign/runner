from __future__ import annotations

import csv
import hashlib
import json
import urllib.request
from pathlib import Path

FILES = {
    "CAMS": ("https://zenodo.org/records/18664293/files/CAMS_shober_2026_subset.csv?download=1", "65dcaefe0a4a3231388ddeda9b0ed9cf"),
    "GMN": ("https://zenodo.org/records/18664293/files/GMN_shober_2026_subset.csv?download=1", "a1890dcb0ca11baa0e49c21c2133dc55"),
    "EDMOND": ("https://zenodo.org/records/18664293/files/EDMOND_shober_2026_subset.csv?download=1", "c5a3ee2c89cdff792bd114a39179350b"),
    "SonotaCo": ("https://zenodo.org/records/18664293/files/SonotaCo_shober_2026_subset.csv?download=1", "f57a2ac71832ceca9227441c00b8cd58"),
}
ROOT = Path("invariant_streamnet_stage0")
DATA = ROOT / "data"
RESULTS = ROOT / "results"


def inspect(name: str, url: str, expected_md5: str) -> dict[str, object]:
    path = DATA / f"{name}.csv"
    if not path.exists():
        print(f"Downloading {name}...", flush=True)
        urllib.request.urlretrieve(url, path)
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    if digest != expected_md5:
        raise SystemExit(f"{name} MD5 mismatch: expected {expected_md5}, got {digest}")
    rows = 0
    first_rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        for row in reader:
            rows += 1
            if len(first_rows) < 3:
                first_rows.append({key: row.get(key, "") for key in header})
    return {
        "url": url,
        "md5": digest,
        "bytes": path.stat().st_size,
        "rows": rows,
        "header": header,
        "first_rows": first_rows,
    }


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    result = {name: inspect(name, *source) for name, source in FILES.items()}
    (RESULTS / "network_schema.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({name: {"rows": item["rows"], "header": item["header"]} for name, item in result.items()}, indent=2))


if __name__ == "__main__":
    main()
