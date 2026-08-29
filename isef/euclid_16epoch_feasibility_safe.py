#!/usr/bin/env python3
"""Safety wrapper for the Euclid Q2 16-epoch Stage-0 test.

Caps every HTTP response read at requested byte count + 1 so an origin that
ignores Range can never stream an entire multi-GB exposure into the runner.
"""
import urllib.request
import euclid_16epoch_feasibility as m


def safe_http_range(url, start, end, timeout=90):
    want = end - start + 1
    req = urllib.request.Request(
        url,
        headers={
            "Range": f"bytes={start}-{end}",
            "User-Agent": "isef-euclid-feasibility/1.2",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(want + 1), dict(r.headers.items()), r.status


m.http_range = safe_http_range
m.main()
