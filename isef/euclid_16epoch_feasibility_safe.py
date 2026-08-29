#!/usr/bin/env python3
"""Safe/fast wrapper for the Euclid Q2 16-epoch Stage-0 test.

All network reads are strictly bounded. FITS headers are fetched in one bounded
92-KB request rather than repeated doubling requests, reducing remote round trips
without changing the underlying Stage-0 analysis.
"""
import math
import urllib.request
import euclid_16epoch_feasibility as m


def safe_http_range(url, start, end, timeout=90):
    want = end - start + 1
    req = urllib.request.Request(
        url,
        headers={
            "Range": f"bytes={start}-{end}",
            "User-Agent": "isef-euclid-feasibility/1.3",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(want + 1)
        headers = dict(r.headers.items())
        status = r.status
    if status != 206:
        raise RuntimeError(
            f"origin ignored byte range {start}-{end}: HTTP {status}; "
            f"bounded read stopped at {len(data)} bytes"
        )
    if len(data) != want:
        raise RuntimeError(
            f"byte-range length mismatch {start}-{end}: got {len(data)}, expected {want}"
        )
    return data, headers, status


def fast_read_header(url, offset):
    # The canonical implementation permits at most 32 FITS blocks, so request
    # exactly that bound once. parse_header() tells us where END occurred.
    max_bytes = 32 * m.BLOCK
    buf, _, status = safe_http_range(url, offset, offset + max_bytes - 1)
    hdr, cards, used = m.parse_header(buf)
    padded = math.ceil(used / m.BLOCK) * m.BLOCK
    return hdr, cards, padded


m.http_range = safe_http_range
m.read_header = fast_read_header
m.main()
