from __future__ import annotations

import csv
import hashlib
import json
import urllib.request
from pathlib import Path

URL = "https://zenodo.org/records/18664293/files/SonotaCo_shober_2026_subset.csv?download=1"
EXPECTED_MD5 = "f57a2ac71832ceca9227441c00b8cd58"
OUT = Path("stream_fdr_stage0/results")
DATA = Path("stream_fdr_stage0/data/SonotaCo_shober_2026_subset.csv")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    if not DATA.exists():
        urllib.request.urlretrieve(URL, DATA)
    digest = hashlib.md5(DATA.read_bytes()).hexdigest()
    if digest != EXPECTED_MD5:
        raise SystemExit(f"MD5 mismatch: expected {EXPECTED_MD5}, got {digest}")

    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = [next(reader) for _ in range(3)]

    line_count = sum(1 for _ in DATA.open("r", encoding="utf-8-sig", errors="replace")) - 1
    payload = {
        "url": URL,
        "md5": digest,
        "bytes": DATA.stat().st_size,
        "rows": line_count,
        "header": header,
        "first_rows": rows,
    }
    (OUT / "data_header.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
