#!/usr/bin/env python3
"""Deterministic HTTP-range probe for a Euclid Q2 VIS exposure.

Scans FITS headers using byte ranges, finds the first 2-D image extension,
and reads a small center window without downloading the multi-GB exposure.
"""
from __future__ import annotations

import json
import math
import re
import struct
import time
import urllib.request
from pathlib import Path

import numpy as np

URL = "https://irsa.ipac.caltech.edu/data/Euclid/q2/data/EUC_VIS_SWL-DET-067070-00-1__20250621T020155.487037Z_sci.fits"
OUT = Path("results/euclid_range_probe.json")
BLOCK = 2880
CARD = 80


def http_range(start: int, end: int) -> tuple[bytes, dict[str, str], int]:
    req = urllib.request.Request(URL, headers={"Range": f"bytes={start}-{end}", "User-Agent": "isef-euclid-feasibility/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), dict(r.headers.items()), r.status


def parse_value(raw: str):
    raw = raw.strip()
    if not raw:
        return None
    # strip FITS comment, respecting quoted strings
    in_quote = False
    cut = len(raw)
    for i, ch in enumerate(raw):
        if ch == "'": in_quote = not in_quote
        elif ch == "/" and not in_quote:
            cut = i
            break
    s = raw[:cut].strip()
    if s.startswith("'"):
        m = re.match(r"'((?:''|[^'])*)'", s)
        return m.group(1).replace("''", "'").strip() if m else s.strip("'").strip()
    if s == "T": return True
    if s == "F": return False
    try:
        if any(c in s for c in ".EDed"):
            return float(s.replace("D", "E").replace("d", "e"))
        return int(s)
    except ValueError:
        return s


def parse_header_cards(buf: bytes) -> tuple[dict, int]:
    hdr = {}
    for off in range(0, len(buf), CARD):
        card = buf[off:off+CARD].decode("ascii", errors="replace")
        key = card[:8].strip()
        if key == "END":
            return hdr, off + CARD
        if len(card) >= 10 and card[8:10] == "= ":
            hdr[key] = parse_value(card[10:])
    raise RuntimeError("END card not found in supplied header bytes")


def read_header(offset: int) -> tuple[dict, int, int]:
    # Headers are typically a few blocks. Expand only until END appears.
    blocks = 1
    while blocks <= 32:
        b, _, status = http_range(offset, offset + blocks*BLOCK - 1)
        if status not in (200, 206):
            raise RuntimeError(f"range header status {status}")
        try:
            hdr, used = parse_header_cards(b)
            padded = math.ceil(used / BLOCK) * BLOCK
            return hdr, padded, status
        except RuntimeError:
            blocks *= 2
    raise RuntimeError("FITS header exceeds 32 blocks")


def data_nbytes(h: dict) -> int:
    naxis = int(h.get("NAXIS", 0) or 0)
    n = 1
    if naxis == 0:
        n = 0
    else:
        for i in range(1, naxis+1):
            n *= int(h.get(f"NAXIS{i}", 0) or 0)
    bitpix = abs(int(h.get("BITPIX", 8) or 8))
    pcount = int(h.get("PCOUNT", 0) or 0)
    gcount = int(h.get("GCOUNT", 1) or 1)
    return (n * bitpix // 8 + pcount) * gcount


def dtype_for(bitpix: int):
    return {8: ">u1", 16: ">i2", 32: ">i4", 64: ">i8", -32: ">f4", -64: ">f8"}[bitpix]


def main():
    t0 = time.time()
    result = {"url": URL, "success": False, "purpose": "byte-range FITS access feasibility"}
    try:
        # First explicitly establish server range behavior.
        probe, headers, status = http_range(0, 1023)
        result["http"] = {
            "status": status,
            "bytes_received": len(probe),
            "content_range": headers.get("Content-Range"),
            "accept_ranges": headers.get("Accept-Ranges"),
            "content_length": headers.get("Content-Length"),
        }
        if status != 206 or len(probe) > 2048:
            raise RuntimeError(f"origin did not honor byte range cleanly: status={status}, bytes={len(probe)}")

        offset = 0
        hdus = []
        selected = None
        for idx in range(0, 600):
            h, hbytes, _ = read_header(offset)
            dn = data_nbytes(h)
            padded_data = math.ceil(dn / BLOCK) * BLOCK if dn else 0
            entry = {
                "index": idx,
                "offset": offset,
                "header_bytes": hbytes,
                "data_offset": offset + hbytes,
                "data_bytes": dn,
                "extname": h.get("EXTNAME"),
                "xtension": h.get("XTENSION"),
                "bitpix": h.get("BITPIX"),
                "naxis": h.get("NAXIS"),
                "naxis1": h.get("NAXIS1"),
                "naxis2": h.get("NAXIS2"),
                "crval1": h.get("CRVAL1"),
                "crval2": h.get("CRVAL2"),
                "date_obs": h.get("DATE-OBS"),
                "mjd_obs": h.get("MJD-OBS"),
                "bunit": h.get("BUNIT"),
                "bscale": h.get("BSCALE"),
                "bzero": h.get("BZERO"),
            }
            hdus.append(entry)
            n1, n2 = h.get("NAXIS1"), h.get("NAXIS2")
            if selected is None and isinstance(n1, int) and isinstance(n2, int) and n1 >= 128 and n2 >= 128 and int(h.get("NAXIS",0) or 0)==2:
                selected = (entry, h)
            next_offset = offset + hbytes + padded_data
            if next_offset <= offset:
                raise RuntimeError("non-advancing FITS offset")
            offset = next_offset
            # Stop once we have scanned enough to prove the layout. A full science file is expected ~144 quadrants.
            if idx >= 180:
                break
            # If known total file size exists and reached it, stop.
            # (Content-Range is of the form bytes 0-1023/TOTAL.)
            cr = headers.get("Content-Range", "")
            m = re.search(r"/(\d+)$", cr)
            if m and offset >= int(m.group(1)):
                break

        result["hdu_count_scanned"] = len(hdus)
        result["hdus_preview"] = hdus[:8]
        if selected is None:
            raise RuntimeError("no 2-D image extension found")

        e, h = selected
        nx, ny = int(h["NAXIS1"]), int(h["NAXIS2"])
        bitpix = int(h["BITPIX"])
        bpp = abs(bitpix)//8
        cx, cy = nx//2, ny//2
        half = 32
        y0, y1 = cy-half, cy+half
        # Fetch complete rows y0:y1 contiguously; then crop x locally. This is still only ~0.5 MB for a 2k-wide float image.
        row0 = e["data_offset"] + y0 * nx * bpp
        row1 = e["data_offset"] + y1 * nx * bpp - 1
        raw, rh, rs = http_range(row0, row1)
        expected = (y1-y0)*nx*bpp
        if rs != 206 or len(raw) != expected:
            raise RuntimeError(f"pixel range mismatch status={rs} got={len(raw)} expected={expected}")
        arr = np.frombuffer(raw, dtype=dtype_for(bitpix)).reshape(y1-y0, nx)
        x0, x1 = cx-half, cx+half
        cut = arr[:, x0:x1].astype(float)
        bscale = float(h.get("BSCALE", 1.0) or 1.0)
        bzero = float(h.get("BZERO", 0.0) or 0.0)
        cut = cut*bscale + bzero
        result["selected_hdu"] = e
        result["sample"] = {
            "x0": x0, "x1": x1, "y0": y0, "y1": y1,
            "shape": list(cut.shape),
            "range_bytes": len(raw),
            "finite_fraction": float(np.isfinite(cut).mean()),
            "median": float(np.nanmedian(cut)),
            "mad": float(np.nanmedian(np.abs(cut-np.nanmedian(cut)))),
            "min": float(np.nanmin(cut)), "max": float(np.nanmax(cut)),
        }
        result["success"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        result["elapsed_seconds"] = round(time.time()-t0, 3)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
        print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
