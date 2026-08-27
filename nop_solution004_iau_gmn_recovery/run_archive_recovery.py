from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from pathlib import Path

SOURCE = Path(__file__).with_name("recover_iau_gmn_archive_orbits.py")
EXPECTED_SOURCE_SHA256 = "b614eced0a596a7f940e654d50c7faeed756400471700f439bf7bcb046758e53"
OLD = '    "dec": {"dec", "de"},'
NEW = '    "dec": {"dec", "de", "decl"},'


def documented_columns(headers: list[str]) -> dict[str, str]:
    exact = {
        "year": "Yr",
        "month": "Mn",
        "day": "Day",
        "sol": "LS",
        "ra": "RA",
        "dec": "DECL",
        "vg": "Vg",
        "q": "q",
        "e": "e",
        "i": "i",
        "peri": "arg",
        "node": "nod",
        "id": "Ano",
    }
    available = set(headers)
    missing = [column for column in exact.values() if column not in available]
    if missing:
        raise RuntimeError(f"IAU-GMN archive is missing documented columns: {missing}")
    return exact


def mixed_format_member_rows(archive: Path):
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            if member.is_dir() or not member.filename.lower().endswith((".csv", ".txt")):
                continue
            with bundle.open(member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
                header_line = next(text, "")
                headers = header_line.split()
                columns = documented_columns(headers)
                schema = {
                    "member": member.filename,
                    "compressed_bytes": member.compress_size,
                    "uncompressed_bytes": member.file_size,
                    "delimiter": ",",
                    "header_index": 0,
                    "headers": headers,
                    "columns": columns,
                    "format": "fixed-width whitespace header with comma-delimited rows",
                }
                reader = csv.DictReader(
                    text,
                    fieldnames=headers,
                    delimiter=",",
                    skipinitialspace=True,
                )
                for row in reader:
                    yield member.filename, row, columns, schema


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
    source_name = "nop_solution004_iau_gmn_recovery/recover_iau_gmn_archive_orbits_format_corrected.py"
    namespace = {"__name__": "archive_recovery_module", "__file__": source_name}
    exec(compile(corrected, source_name, "exec"), namespace)
    namespace["map_columns"] = documented_columns
    namespace["member_rows"] = mixed_format_member_rows
    namespace["main"]()


if __name__ == "__main__":
    main()
