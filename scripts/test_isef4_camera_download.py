#!/usr/bin/env python3
"""Offline scientific-source integrity tests for strict PDS byte-range recovery.

No NASA network access, scientific imagery, or source-camera model is needed.
A passing test establishes transfer invariants, NOT lunar event sensitivity.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ["ISEF4_PRODUCT_ROLE"] = "after"
os.environ["ISEF4_DIAGNOSTIC_SUFFIX"] = "range_selftest"
SCRIPT = Path(__file__).resolve().parent / "isef4_isis_camera_triage.py"
spec = importlib.util.spec_from_file_location("lunar_camera_triage", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

header = (b"PDS_VERSION_ID = PDS3\\nPRODUCT_ID = M1200206882LE\\n"
          + b" " * 5064)[:5064]
assert len(header) == 5064
payload = header + bytes(i % 251 for i in range(12043))
known_hash = hashlib.sha256(header).hexdigest()
requested = []


class FakeResponse:
    def __init__(self, data, start, end, total, *,
                 status=206, content_range=None):
        self.data = data
        self.cursor = 0
        self.status = status
        self.headers = {
            "Content-Range": (
                content_range if content_range is not None
                else f"bytes {start}-{end}/{total}"
            )
        }

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, n=-1):
        n = len(self.data) if n < 0 else n
        out = self.data[self.cursor:self.cursor+n]
        self.cursor += len(out)
        return out


def make_opener(fault=None):
    def opener(req, timeout):
        assert timeout == 240
        r = req.get_header("Range")
        m = re.fullmatch(r"bytes=(\\d+)-(\\d+)", r or "")
        assert m is not None, r
        start, end = map(int, m.groups())
        requested.append((start, end))
        data = payload[start:end+1]
        kw = {}
        if fault == "status":
            kw["status"] = 200
        elif fault == "shift":
            kw["content_range"] = f"bytes {start+1}-{end+1}/{len(payload)}"
        elif fault == "wrong-total":
            kw["content_range"] = f"bytes {start}-{end}/{len(payload)+1}"
        elif fault == "truncated":
            data = data[:-1]
        elif fault == "extra":
            data += b"X"
        return FakeResponse(data, start, end, len(payload), **kw)
    return opener


def run(destination, known_hash_value=known_hash):
    return module.fetch_verified_after_ranges(
        "https://example.invalid/original.IMG",
        destination,
        expected_size=len(payload),
        chunk_bytes=6000,
        known_first_5064_sha=known_hash_value,
    )


with tempfile.TemporaryDirectory() as temp:
    folder = Path(temp)
    output = folder / "original.IMG"
    with patch.object(module.urllib.request, "urlopen",
                      side_effect=make_opener()):
        count, digest = run(output)
    assert count == len(payload)
    assert digest == hashlib.sha256(payload).hexdigest()
    assert output.read_bytes() == payload
    assert requested == [(0, 5999), (6000, 11999), (12000, len(payload)-1)]
    assert not output.with_suffix(".IMG.part").exists()
    print("PASS: strict sequential ranges reconstruct the exact source")

    for fault in ("status", "shift", "wrong-total", "truncated", "extra"):
        requested.clear()
        output.write_bytes(b"DO_NOT_OVERWRITE")
        with patch.object(module.urllib.request, "urlopen",
                          side_effect=make_opener(fault)):
            try:
                run(output)
            except ValueError:
                pass
            else:
                raise AssertionError(f"accepted invalid scientific transfer: {fault}")
        assert output.read_bytes() == b"DO_NOT_OVERWRITE", fault
        assert not output.with_suffix(".IMG.part").exists(), fault
        print("PASS: reject", fault)

    with patch.object(module.urllib.request, "urlopen",
                      side_effect=make_opener()):
        try:
            run(output, known_hash_value="0"*64)
        except ValueError as exc:
            assert "header differs" in str(exc)
        else:
            raise AssertionError("accepted an unverified PDS3 source header")
    assert output.read_bytes() == b"DO_NOT_OVERWRITE"
    print("PASS: reject unverified source identity and preserve prior output")

print("Strict original PDS byte-range self-test: PASS")
