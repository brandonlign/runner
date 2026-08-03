from __future__ import annotations

import base64
import gzip
import hashlib
import urllib.request

SOURCE_PAYLOAD_URL = (
    "https://raw.githubusercontent.com/brandonlign/runner/"
    "b271d61309fd0bf7f20e97263749e5179ecd3509/"
    "nop_solution004_audit/audit_nop_solution004.py.gz.b64"
)
ORIGINAL_BYTES = 23611
ORIGINAL_SHA256 = "30888093854f1a90634b9f1f0a74e0c83db68eec15194f9ffae843fabb2d5229"
PATCHED_BYTES = 24170
PATCHED_SHA256 = "c0c69b569c6fe84cf2223e017346e13843a05d3ef4d40ed897494a4187f2a693"

REPLACEMENTS = (
    (
        '        "sol_begin": finite(target_solution.get("Beg")),',
        '        "sol_begin": finite(target_solution.get("LoSb") if target_solution.get("LoSb") is not None else target_solution.get("Beg")),',
    ),
    (
        '        "sol_end": finite(target_solution.get("End")),',
        '        "sol_end": finite(target_solution.get("LoSe") if target_solution.get("LoSe") is not None else target_solution.get("End")),',
    ),
    (
        '        "ra": finite(target_solution.get("RA")),',
        '        "ra": finite(target_solution.get("Ra") if target_solution.get("Ra") is not None else target_solution.get("RA")),',
    ),
    (
        '        "dec": finite(target_solution.get("DE")),',
        '        "dec": finite(target_solution.get("De") if target_solution.get("De") is not None else target_solution.get("DE")),',
    ),
    (
        '        "peri": finite(target_solution.get("Peri")),',
        '        "peri": finite(target_solution.get("peri") if target_solution.get("peri") is not None else target_solution.get("Peri")),',
    ),
    (
        '        "node": finite(target_solution.get("Node")),',
        '        "node": finite(target_solution.get("node") if target_solution.get("node") is not None else target_solution.get("Node")),',
    ),
    (
        '        "inc": finite(target_solution.get("Inc")),',
        '        "inc": finite(target_solution.get("inc") if target_solution.get("inc") is not None else target_solution.get("Inc")),',
    ),
    (
        '        "reference": target_solution.get("Ref"),',
        '        "reference": target_solution.get("References") or target_solution.get("Ref"),',
    ),
)


def checked_source() -> bytes:
    request = urllib.request.Request(
        SOURCE_PAYLOAD_URL,
        headers={"User-Agent": "ghoststream-nop-solution004-audit-source/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    encoded = "".join(payload.decode("ascii").split()).rstrip("=")
    encoded += "=" * (-len(encoded) % 4)
    original = gzip.decompress(base64.b64decode(encoded, validate=True))
    if len(original) != ORIGINAL_BYTES:
        raise RuntimeError(f"Original source size mismatch: {len(original)}")
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256:
        raise RuntimeError("Original source SHA-256 mismatch")

    source = original.decode("utf-8")
    for old, new in REPLACEMENTS:
        if source.count(old) != 1:
            raise RuntimeError(f"Expected one schema patch target, found {source.count(old)}: {old}")
        source = source.replace(old, new)
    patched = source.encode("utf-8")
    if len(patched) != PATCHED_BYTES:
        raise RuntimeError(f"Patched source size mismatch: {len(patched)}")
    if hashlib.sha256(patched).hexdigest() != PATCHED_SHA256:
        raise RuntimeError("Patched source SHA-256 mismatch")
    return patched


def main() -> None:
    raw = checked_source()
    source_name = "nop_solution004_audit/audit_nop_solution004_source.py"
    namespace = {"__name__": "__main__", "__file__": source_name}
    exec(compile(raw, source_name, "exec"), namespace)


if __name__ == "__main__":
    main()
