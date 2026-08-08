#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import zlib
from pathlib import Path

EXPECTED_DIRS = ["data/2016/", "data/2016/03/"]
EXPECTED_NAME = "data/2016/03/kep_collect.h5"
EXPECTED_SIZE = 139_028_822
EXPECTED_EMITTED = 3 * 512 + EXPECTED_SIZE


def parse_octal(bs: bytes) -> int:
    s = bs.split(b"\0", 1)[0].strip(b" ")
    return int(s or b"0", 8)


def parse_header(block: bytes) -> dict:
    if len(block) != 512:
        raise RuntimeError("short tar header")
    name = block[0:100].split(b"\0", 1)[0].decode("utf-8", "replace")
    prefix = block[345:500].split(b"\0", 1)[0].decode("utf-8", "replace")
    if prefix:
        name = f"{prefix}/{name}"
    stored = parse_octal(block[148:156])
    chk = bytearray(block)
    chk[148:156] = b"        "
    if stored != sum(chk):
        raise RuntimeError(f"tar checksum mismatch for {name!r}")
    return {
        "name": name,
        "size": parse_octal(block[124:136]),
        "typeflag": block[156:157].decode("latin1"),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--compressed-range", required=True, type=Path)
    p.add_argument("--hdf5-output", required=True, type=Path)
    p.add_argument("--audit-output", required=True, type=Path)
    a = p.parse_args()

    comp = a.compressed_range.read_bytes()
    dec = zlib.decompressobj(16 + zlib.MAX_WBITS)
    state = {"ci": 0, "pending": b"", "emitted": 0}

    def exact_uncompressed(n: int) -> bytes:
        out = bytearray()
        while len(out) < n:
            need = n - len(out)
            if state["pending"]:
                src = state["pending"]
                state["pending"] = b""
            elif state["ci"] < len(comp):
                end = min(state["ci"] + 65_536, len(comp))
                src = comp[state["ci"]:end]
                state["ci"] = end
            else:
                raise RuntimeError(
                    f"bounded compressed range exhausted while needing {need} uncompressed bytes"
                )
            produced = dec.decompress(src, need)
            out.extend(produced)
            state["emitted"] += len(produced)
            if dec.unconsumed_tail:
                state["pending"] = bytes(dec.unconsumed_tail)
            if not produced and not state["pending"] and state["ci"] >= len(comp):
                raise RuntimeError("gzip stream made no progress before requested output completed")
        if len(out) != n:
            raise RuntimeError("exact decompression length invariant failed")
        return bytes(out)

    headers = []
    for expected in EXPECTED_DIRS:
        h = parse_header(exact_uncompressed(512))
        if h["name"] != expected or h["size"] != 0 or h["typeflag"] != "5":
            raise RuntimeError(f"leading directory header changed: {h!r}")
        headers.append(h)

    h = parse_header(exact_uncompressed(512))
    if (
        h["name"] != EXPECTED_NAME
        or h["size"] != EXPECTED_SIZE
        or h["typeflag"] not in ("0", "\x00")
    ):
        raise RuntimeError(f"first HDF5 header changed: {h!r}")
    headers.append(h)

    a.hdf5_output.parent.mkdir(parents=True, exist_ok=True)
    remaining = EXPECTED_SIZE
    with a.hdf5_output.open("wb") as out:
        while remaining:
            take = min(1_048_576, remaining)
            out.write(exact_uncompressed(take))
            remaining -= take

    if state["emitted"] != EXPECTED_EMITTED:
        raise RuntimeError(
            f"uncompressed byte boundary violated: {state['emitted']} != {EXPECTED_EMITTED}"
        )
    if a.hdf5_output.stat().st_size != EXPECTED_SIZE:
        raise RuntimeError("materialized first HDF5 size mismatch")

    audit = {
        "headers": headers,
        "member_name": EXPECTED_NAME,
        "member_size": EXPECTED_SIZE,
        "member_payload_materialized": True,
        "uncompressed_bytes_emitted_exactly": state["emitted"],
        "expected_uncompressed_boundary": EXPECTED_EMITTED,
        "tar_padding_after_member_decompressed": False,
        "next_tar_header_decompressed": False,
        "dataset_value_read": False,
        "attribute_value_read": False,
    }
    a.audit_output.parent.mkdir(parents=True, exist_ok=True)
    a.audit_output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
