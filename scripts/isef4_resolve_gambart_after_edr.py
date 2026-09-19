#!/usr/bin/env python3
"""Find the exact PDS EDR image archive path from original product metadata.

Metadata-only range probe. Do not fetch a guessed entire 140 MB EDR,
do not inspect geographic holdout images, and do not infer geometry.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

PRODUCT = "M1200206882LE"
YEAR_DOY = "2015296"  # original published 2015-10-23T02:33:35 UTC
EXPECTED_IMAGE_BYTES = 140_014_536
EXPECTED_HEADER_BYTES = 5064
ROOT = "https://pds.lroc.im-ldi.com/data/LRO-L-LROC-2-EDR-V1.0"
OUT = Path("diagnostics/isef4_gambart_after_edr_source_resolution.json")


def probe(volume: int, phase: str) -> dict:
    url = (
        f"{ROOT}/LROLRC_{volume:04d}/DATA/{phase}/{YEAR_DOY}/"
        f"NAC/{PRODUCT}.IMG"
    )
    req = urllib.request.Request(
        url,
        headers={"Range": f"bytes=0-{EXPECTED_HEADER_BYTES-1}",
                 "User-Agent": "LUNARSHIFT-PDS-source-audit/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=18) as response:
            code = response.status
            content_range = response.headers.get("Content-Range")
            data = response.read(EXPECTED_HEADER_BYTES)
            content_type = response.headers.get("Content-Type", "")
        if code != 206:
            return {"url": url, "status": "not_range_supported",
                    "http_status": code}
        m = re.fullmatch(r"bytes 0-(\d+)/(\d+)", content_range or "")
        if not m or int(m.group(1)) != EXPECTED_HEADER_BYTES-1:
            return {"url": url, "status": "unexpected_content_range",
                    "content_range": content_range}
        if int(m.group(2)) != EXPECTED_IMAGE_BYTES:
            return {"url": url, "status": "unexpected_full_file_size",
                    "full_size": int(m.group(2))}
        label = data.decode("ascii", errors="replace")
        if PRODUCT not in label or "PDS_VERSION_ID" not in label:
            return {"url": url, "status": "not_matching_PDS3_label",
                    "first_100_chars": label[:100]}
        return {"url": url, "status": "verified",
                "http_status": code, "content_range": content_range,
                "content_type": content_type,
                "label_prefix_sha256": hashlib.sha256(data).hexdigest(),
                "label_prefix_bytes": len(data),
                "image_size_bytes": int(m.group(2)),
                "xml_url": url.removesuffix(".IMG") + ".xml"}
    except urllib.error.HTTPError as exc:
        return {"url": url, "status": "http_error", "http_status": exc.code}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"url": url, "status": "connection_error",
                "exception": type(exc).__name__, "message": str(exc)[:200]}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    candidates = [
        (volume, phase)
        for volume in range(23, 31)
        for phase in ("ESM2", "ESM", "ESM3")
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        tested = list(executor.map(lambda x: probe(*x), candidates))
    found = [entry for entry in tested if entry["status"] == "verified"]
    result = {
        "schema_version": "isef4-exact-published-Gambart-C-after-PDS3-v1",
        "product": PRODUCT,
        "image_date_UTC": "2015-10-23",
        "expected_file_bytes_from_previous_original_PDS_label": EXPECTED_IMAGE_BYTES,
        "candidates_checked": len(tested),
        "verified_matches": found,
        "nonmatches": tested if not found else [
            e for e in tested if e["status"] not in ("http_error",)
        ],
        "scientific_status": (
            "verified exact original AFTER EDR archive link only; "
            "NO camera mapping or event recovery"
            if found else
            "original AFTER EDR archive remains unresolved; "
            "do not guess a source file URL"
        ),
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    return 0 if len(found) == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
