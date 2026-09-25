from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = Path(__file__).with_name("recover_multisource_orbits.py")
EXPECTED_SOURCE_SHA256 = "759b8e5276de4d941adab1e6fd978712bfbe255c57cd2b001e281e9dc7228498"


def select(headers: list[str], *candidates: str) -> str:
    available = set(headers)
    match = next((candidate for candidate in candidates if candidate in available), None)
    if match is None:
        raise RuntimeError(f"Archive is missing one of {candidates}; headers={headers}")
    return match


def parse_header_and_delimiter(header_line: str, first_data_line: str) -> tuple[list[str], str, str]:
    header_delimiter = max((",", ";", "\t", "|"), key=header_line.count)
    if header_line.count(header_delimiter) >= 4:
        headers = [value.strip() for value in next(csv.reader([header_line], delimiter=header_delimiter))]
    else:
        headers = header_line.split()
    row_delimiter = max((",", ";", "\t", "|"), key=first_data_line.count)
    if first_data_line.count(row_delimiter) < 4:
        raise RuntimeError("Could not identify archive row delimiter")
    return headers, header_delimiter, row_delimiter


def main() -> None:
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"Frozen multisource source SHA-256 mismatch: expected {EXPECTED_SOURCE_SHA256}, got {digest}"
        )
    source_name = "nop_solution004_multisource_recovery/recover_multisource_orbits_schema_corrected.py"
    namespace = {"__name__": "multisource_recovery_module", "__file__": source_name}
    exec(compile(raw, source_name, "exec"), namespace)
    as_float = namespace["as_float"]

    def read_archive(path: Path, expected_year: int, allowed_months: set[int], source: str):
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
                    text = io.TextIOWrapper(raw_member, encoding="utf-8-sig", errors="replace", newline="")
                    header_line = next(text, "")
                    first_data_line = next(text, "")
                headers, header_delimiter, row_delimiter = parse_header_and_delimiter(
                    header_line, first_data_line
                )

                if "_Y_ut" in headers:
                    schema_kind = "EDMOND native UTC components"
                    columns = {
                        "year": select(headers, "_Y_ut"),
                        "month": select(headers, "_M_ut"),
                        "day": select(headers, "_D_ut"),
                        "hour": select(headers, "_h_ut"),
                        "minute": select(headers, "_m_ut"),
                        "second": select(headers, "_s_ut"),
                        "sol": select(headers, "_sol"),
                        "ra": select(headers, "_ra_t", "_ra_o"),
                        "dec": select(headers, "_dc_t", "_dc_o"),
                        "vg": select(headers, "_vg"),
                        "q": select(headers, "_q"),
                        "e": select(headers, "_e"),
                        "i": select(headers, "_incl"),
                        "peri": select(headers, "_peri"),
                        "node": select(headers, "_node"),
                        "id": select(headers, "_#", "_ID1"),
                    }
                else:
                    schema_kind = "IAU annual fractional-day fields"
                    columns = {
                        "year": select(headers, "Yr", "YEAR", "Year"),
                        "month": select(headers, "Mn", "MONTH", "Month"),
                        "day": select(headers, "Dayy", "Day", "DAY"),
                        "sol": select(headers, "LS", "Sol", "SOL"),
                        "ra": select(headers, "RA"),
                        "dec": select(headers, "DECL", "DEC", "DE"),
                        "vg": select(headers, "Vg", "VG"),
                        "q": select(headers, "q"),
                        "e": select(headers, "e"),
                        "i": select(headers, "i"),
                        "peri": select(headers, "arg", "peri"),
                        "node": select(headers, "nod", "node"),
                        "id": select(headers, "Ano", "ID", "Id", "IC"),
                    }

                schemas.append(
                    {
                        "source": source,
                        "archive": path.name,
                        "member": member.filename,
                        "compressed_bytes": member.compress_size,
                        "uncompressed_bytes": member.file_size,
                        "headers": headers,
                        "columns": columns,
                        "header_delimiter": header_delimiter,
                        "row_delimiter": row_delimiter,
                        "schema_kind": schema_kind,
                    }
                )
                with bundle.open(member) as raw_member:
                    text = io.TextIOWrapper(raw_member, encoding="utf-8-sig", errors="replace", newline="")
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

                        if schema_kind.startswith("EDMOND"):
                            hour = as_float(row.get(columns["hour"]))
                            minute = as_float(row.get(columns["minute"]))
                            second = as_float(row.get(columns["second"]))
                            if hour is None or minute is None or second is None:
                                continue
                            timestamp = datetime(
                                year,
                                month,
                                int(round(day_value)),
                                tzinfo=timezone.utc,
                            ) + timedelta(
                                hours=hour,
                                minutes=minute,
                                seconds=second,
                            )
                        else:
                            timestamp = datetime(year, month, 1, tzinfo=timezone.utc) + timedelta(
                                days=day_value - 1.0
                            )

                        values = {
                            key: as_float(row.get(columns[key]))
                            for key in ("sol", "ra", "dec", "vg", "q", "e", "i", "peri", "node")
                        }
                        if any(values[key] is None for key in ("sol", "ra", "dec", "vg")):
                            continue
                        events.append(
                            {
                                "source": source,
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

    namespace["read_archive"] = read_archive
    namespace["main"]()


if __name__ == "__main__":
    main()
