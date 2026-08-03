from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE = Path(__file__).with_name("recover_iau_gmn_archive_orbits.py")
EXPECTED_SOURCE_SHA256 = "b614eced0a596a7f940e654d50c7faeed756400471700f439bf7bcb046758e53"
OLD = '    "dec": {"dec", "de"},'
NEW = '    "dec": {"dec", "de", "decl"},'


def main() -> None:
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"Frozen archive-recovery source SHA-256 mismatch: expected {EXPECTED_SOURCE_SHA256}, got {digest}"
        )
    text = raw.decode("utf-8")
    if text.count(OLD) != 1:
        raise RuntimeError("Expected exactly one declination alias declaration")
    corrected = text.replace(OLD, NEW)
    source_name = "nop_solution004_iau_gmn_recovery/recover_iau_gmn_archive_orbits_decl_corrected.py"
    namespace = {"__name__": "__main__", "__file__": source_name}
    exec(compile(corrected, source_name, "exec"), namespace)


if __name__ == "__main__":
    main()
