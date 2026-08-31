#!/usr/bin/env python3
"""Header-only structural audit of fixed C/2025 R3 PUNCH L2 CTM files.

Uses HTTP Range requests to read FITS headers and skips each data payload by
computing its byte length from header keywords. Science/uncertainty pixel arrays
are never requested or decoded.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import requests

OUT = Path("results/punch_r3_l2_header_audit")
OUT.mkdir(parents=True, exist_ok=True)
ROOT = "https://umbra.nascom.nasa.gov/punch/2/CTM/2026"

# Prospectively fixed representative epochs: start, externally anchored 23:20
# neighborhood, and end of the frozen inventory window. All are v0l.
FILES = [
    f"{ROOT}/04/21/PUNCH_L2_CTM_20260421180029_v0l.fits",
    f"{ROOT}/04/21/PUNCH_L2_CTM_20260421232029_v0l.fits",
    f"{ROOT}/04/22/PUNCH_L2_CTM_20260422115229_v0l.fits",
]

BLOCK = 2880
CARD = 80


def get_range(url: str, start: int, end: int) -> bytes:
    r = requests.get(url, headers={"Range": f"bytes={start}-{end}"}, timeout=(10, 60))
    if r.status_code not in (200, 206):
        raise RuntimeError(f"HTTP {r.status_code} for {url} range {start}-{end}")
    data = r.content
    # Some servers ignore Range and return the full file. Never retain/read beyond
    # the requested header-sized prefix in that case.
    if r.status_code == 200 and start == 0:
        return data[: end-start+1]
    if r.status_code == 200 and start > 0:
        raise RuntimeError("server ignored nonzero Range request; aborting to avoid array transfer")
    return data


def parse_value(raw: str):
    s = raw.strip()
    if not s:
        return None
    # Remove FITS comment outside quoted strings, sufficient for structural cards.
    if s.startswith("'"):
        end = s.find("'", 1)
        while end != -1 and end + 1 < len(s) and s[end+1] == "'":
            end = s.find("'", end+2)
        return s[1:end].replace("''", "'") if end != -1 else s.strip("'")
    token = s.split("/", 1)[0].strip()
    if token in ("T", "F"):
        return token == "T"
    try:
        if any(c in token for c in ".EeDd"):
            return float(token.replace("D", "E"))
        return int(token)
    except Exception:
        return token


def read_header(url: str, offset: int):
    cards = []
    pos = offset
    found_end = False
    while not found_end:
        chunk = get_range(url, pos, pos + BLOCK - 1)
        if len(chunk) < BLOCK:
            raise RuntimeError(f"short FITS header block at {pos}: {len(chunk)}")
        for i in range(0, BLOCK, CARD):
            text = chunk[i:i+CARD].decode("ascii", "replace")
            cards.append(text)
            if text[:8].strip() == "END":
                found_end = True
                break
        pos += BLOCK
        if len(cards) > 10000:
            raise RuntimeError("implausibly large FITS header")

    header_bytes = pos - offset
    kv = {}
    history = []
    comments = []
    for card in cards:
        key = card[:8].strip()
        if key == "END":
            break
        if key == "HISTORY":
            history.append(card[8:].strip())
        elif key == "COMMENT":
            comments.append(card[8:].strip())
        elif card[8:10] == "= ":
            kv[key] = parse_value(card[10:])
    return kv, history, comments, header_bytes


def data_bytes(kv: dict) -> int:
    bitpix = abs(int(kv.get("BITPIX", 8)))
    naxis = int(kv.get("NAXIS", 0))
    n = 1
    if naxis == 0:
        n = 0
    else:
        for i in range(1, naxis + 1):
            n *= int(kv.get(f"NAXIS{i}", 0))
    pcount = int(kv.get("PCOUNT", 0))
    gcount = int(kv.get("GCOUNT", 1))
    raw = ((bitpix * n + 7) // 8 + pcount) * gcount
    return int(math.ceil(raw / BLOCK) * BLOCK) if raw else 0


def structural_subset(kv: dict):
    keep_prefixes = (
        "NAXIS", "CTYPE", "CRVAL", "CRPIX", "CDELT", "CD", "PC", "CUNIT",
    )
    keep_exact = {
        "SIMPLE", "XTENSION", "BITPIX", "EXTNAME", "PCOUNT", "GCOUNT",
        "DATE-OBS", "DATE-BEG", "DATE-END", "DATE", "TIMESYS", "MJD-OBS",
        "BUNIT", "BZERO", "BSCALE", "PIPEVRSN", "LEVEL", "TYPECODE",
        "OBSCODE", "PRODTYPE", "DATAVERS", "VERSION", "TELESCOP", "INSTRUME",
    }
    return {k: v for k, v in kv.items() if k in keep_exact or k.startswith(keep_prefixes)}


def audit_file(url: str):
    h = requests.head(url, allow_redirects=True, timeout=(10, 30))
    if h.status_code != 200:
        raise RuntimeError(f"HEAD HTTP {h.status_code}: {url}")
    size = int(h.headers.get("Content-Length", "0") or 0)
    accept_ranges = h.headers.get("Accept-Ranges")

    hdus = []
    offset = 0
    total_header_bytes = 0
    while offset < size:
        kv, history, comments, hbytes = read_header(url, offset)
        dbytes = data_bytes(kv)
        hdus.append({
            "index": len(hdus),
            "offset": offset,
            "header_bytes_requested": hbytes,
            "data_bytes_skipped_without_request": dbytes,
            "header": structural_subset(kv),
            "history_tail": history[-10:],
        })
        total_header_bytes += hbytes
        offset += hbytes + dbytes
        if len(hdus) > 20:
            raise RuntimeError("too many HDUs; structural parser likely lost sync")
        if dbytes == 0 and hbytes == 0:
            break
        # FITS files can contain trailing padding; stop if less than one header block.
        if size - offset < BLOCK:
            break

    return {
        "url": url,
        "content_length_bytes": size,
        "accept_ranges": accept_ranges,
        "n_hdus": len(hdus),
        "total_header_bytes_requested": total_header_bytes,
        "fraction_file_requested": total_header_bytes / size if size else None,
        "hdus": hdus,
    }


def main():
    report = {
        "information_barrier": "HTTP Range FITS headers only; image/uncertainty array bytes skipped and never requested",
        "files": [],
    }
    for url in FILES:
        report["files"].append(audit_file(url))

    # Mechanical structure checks, no science pixels.
    structures = []
    for f in report["files"]:
        extnames = [str(h["header"].get("EXTNAME", "PRIMARY")) for h in f["hdus"]]
        shapes = [
            [h["header"].get(f"NAXIS{i}") for i in range(1, int(h["header"].get("NAXIS", 0)) + 1)]
            for h in f["hdus"]
        ]
        structures.append((f["n_hdus"], extnames, shapes))
    report["identical_hdu_structure"] = all(s == structures[0] for s in structures[1:])

    # WCS presence: primary/first image HDU needs at least CTYPE1/2 and CRPIX1/2.
    report["wcs_present_all"] = all(
        any(all(k in h["header"] for k in ["CTYPE1", "CTYPE2", "CRPIX1", "CRPIX2"])
            for h in f["hdus"])
        for f in report["files"]
    )

    # We do not assume uncertainty extension naming; record likely error/variance names.
    report["uncertainty_like_extnames"] = sorted({
        str(h["header"].get("EXTNAME"))
        for f in report["files"] for h in f["hdus"]
        if h["header"].get("EXTNAME") is not None
        and any(tok in str(h["header"].get("EXTNAME")).upper() for tok in ["ERR", "UNC", "VAR", "SIGMA"])
    })

    (OUT / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["identical_hdu_structure"]:
        return 2
    if not report["wcs_present_all"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
