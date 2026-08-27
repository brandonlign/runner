from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from pathlib import Path

SOURCE = Path(__file__).with_name("recover_official_cams_orbits.py")
EXPECTED_SOURCE_SHA256 = "f14ef9b263eb9b973f64be207c40a1d4d4cc97daa9b70f1f77c5ec2cdd9f4845"


def documented_columns(headers: list[str]) -> dict[str, str]:
    options = {
        "year": ("Yr", "YEAR", "Year"),
        "month": ("Mn", "MONTH", "Month"),
        "day": ("Dayy", "Day", "DAY"),
        "sol": ("LS", "Sol", "SOL"),
        "ra": ("RA",),
        "dec": ("DECL", "DEC", "DE"),
        "vg": ("Vg", "VG"),
        "q": ("q",),
        "e": ("e",),
        "i": ("i",),
        "peri": ("arg", "peri"),
        "node": ("nod", "node"),
        "id": ("Ano", "ID", "Id"),
    }
    available = set(headers)
    mapping: dict[str, str] = {}
    for target, candidates in options.items():
        match = next((candidate for candidate in candidates if candidate in available), None)
        if match is None:
            raise RuntimeError(f"CAMS archive is missing documented `{target}` column; headers={headers}")
        mapping[target] = match
    return mapping


def main() -> None:
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"Frozen CAMS recovery source SHA-256 mismatch: expected {EXPECTED_SOURCE_SHA256}, got {digest}"
        )
    source_name = "nop_solution004_cams_recovery/recover_official_cams_orbits_schema_corrected.py"
    namespace = {"__name__": "cams_recovery_module", "__file__": source_name}
    exec(compile(raw, source_name, "exec"), namespace)

    as_float = namespace["as_float"]
    fractional_day_time = namespace["fractional_day_time"]

    def read_archive(path: Path, expected_year: int, allowed_months: set[int]):
        events = []
        schemas = []
        with zipfile.ZipFile(path) as bundle:
            members = [
                member
                for member in bundle.infolist()
                if not member.is_dir()
                and member.filename.lower().endswith((".csv", ".txt"))
                and "__MACOSX/" not in member.filename
                and not Path(member.filename).name.startswith("._")
            ]
            if not members:
                raise RuntimeError(f"No data CSV/TXT members in {path.name}")
            for member in members:
                with bundle.open(member) as raw_member:
                    text = io.TextIOWrapper(
                        raw_member,
                        encoding="utf-8-sig",
                        errors="replace",
                        newline="",
                    )
                    header_line = next(text, "")
                    first_data_line = next(text, "")
                header_delimiter = max((";", ",", "\t", "|"), key=header_line.count)
                if header_line.count(header_delimiter) >= 4:
                    headers = [
                        value.strip()
                        for value in next(csv.reader([header_line], delimiter=header_delimiter))
                    ]
                else:
                    headers = header_line.split()
                columns = documented_columns(headers)
                row_delimiter = max((";", ",", "\t", "|"), key=first_data_line.count)
                if first_data_line.count(row_delimiter) < 4:
                    raise RuntimeError(f"Could not identify CAMS row delimiter in {member.filename}")
                schemas.append(
                    {
                        "archive": path.name,
                        "member": member.filename,
                        "compressed_bytes": member.compress_size,
                        "uncompressed_bytes": member.file_size,
                        "headers": headers,
                        "columns": columns,
                        "header_delimiter": header_delimiter,
                        "row_delimiter": row_delimiter,
                        "format": "delimited header and rows",
                    }
                )
                with bundle.open(member) as raw_member:
                    text = io.TextIOWrapper(
                        raw_member,
                        encoding="utf-8-sig",
                        errors="replace",
                        newline="",
                    )
                    next(text, None)
                    reader = csv.DictReader(
                        text,
                        fieldnames=headers,
                        delimiter=row_delimiter,
                        skipinitialspace=True,
                    )
                    for row in reader:
                        year_value = as_float(row.get(columns["year"]))
                        month_value = as_float(row.get(columns["month"]))
                        day_value = as_float(row.get(columns["day"]))
                        if year_value is None or month_value is None or day_value is None:
                            continue
                        year = int(round(year_value))
                        month = int(round(month_value))
                        if year != expected_year or month not in allowed_months:
                            continue
                        values = {
                            key: as_float(row.get(columns[key]))
                            for key in ("sol", "ra", "dec", "vg", "q", "e", "i", "peri", "node")
                        }
                        if any(values[key] is None for key in ("sol", "ra", "dec", "vg")):
                            continue
                        timestamp = fractional_day_time(year, month, day_value)
                        events.append(
                            {
                                "archive": path.name,
                                "member": member.filename,
                                "id": (row.get(columns["id"]) or "").strip(),
                                "time": timestamp,
                                "time_text": timestamp.isoformat(),
                                "sol": float(values["sol"]),
                                "ra": float(values["ra"]),
                                "dec": float(values["dec"]),
                                "vg": float(values["vg"]),
                                "orbit": {
                                    "q": values["q"],
                                    "e": values["e"],
                                    "i": values["i"],
                                    "peri": values["peri"],
                                    "node": values["node"],
                                },
                            }
                        )
        return events, schemas

    namespace["documented_columns"] = documented_columns
    namespace["read_archive"] = read_archive
    namespace["main"]()


if __name__ == "__main__":
    main()
