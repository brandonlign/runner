#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ARCHIVE = Path("ASFN_2013_2019.zip")
OUT = Path("output")
README_BASENAME = "nasfn_2013-2019_readme.txt"
DATA_BASENAME = "nasfn_2013-2019_data.txt"
REQUIRED_FIELDS = ("slon", "lam_g", "bet_g", "v_g")
PARSER_TOKENS = ("date", "field", "column")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = ARCHIVE.read_bytes()
    archive_sha = sha_bytes(raw)
    with zipfile.ZipFile(ARCHIVE) as z:
        infos = z.infolist()
        listing = [
            {"filename": i.filename, "file_size": i.file_size, "compress_size": i.compress_size, "date_time": list(i.date_time)}
            for i in infos
        ]
        readmes = [i for i in infos if Path(i.filename).name == README_BASENAME]
        data_members = [i for i in infos if Path(i.filename).name == DATA_BASENAME]
        if len(readmes) != 1 or len(data_members) != 1:
            raise RuntimeError(f"expected one readme and one data member; got {len(readmes)} / {len(data_members)}")
        readme_info = readmes[0]
        data_info = data_members[0]
        # Binding safety rule: ONLY the readme member is opened/read.
        readme_bytes = z.read(readme_info.filename)
    try:
        text = readme_bytes.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = readme_bytes.decode("latin-1")
        encoding = "latin-1"
    low = text.lower()
    fields_present = {f: (f.lower() in low) for f in REQUIRED_FIELDS}
    parser_present = {t: (t.lower() in low) for t in PARSER_TOKENS}
    passed = all(fields_present.values()) and any(parser_present.values())
    (OUT / "NASA_ASFN_2013_2019_README.txt").write_bytes(readme_bytes)
    result = {
        "stage": "NASA_ASFN_README_RECURRENT_EOM_PREACCESS_V1",
        "verdict": "PASS_NASA_ASFN_README_RECURRENT_EOM_PREACCESS" if passed else "FAIL_NASA_ASFN_README_RECURRENT_EOM_PREACCESS",
        "archive_sha256": archive_sha,
        "archive_bytes": len(raw),
        "archive_listing": listing,
        "readme_member": readme_info.filename,
        "readme_sha256": sha_bytes(readme_bytes),
        "readme_bytes": len(readme_bytes),
        "readme_encoding": encoding,
        "data_member": data_info.filename,
        "data_member_uncompressed_bytes_from_central_directory": data_info.file_size,
        "data_member_compressed_bytes_from_central_directory": data_info.compress_size,
        "required_fields_present": fields_present,
        "parser_tokens_present": parser_present,
        "asfn_archive_download": True,
        "asfn_data_member_extracted": False,
        "asfn_data_member_opened": False,
        "asfn_event_value_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (OUT / "NASA_ASFN_README_RECURRENT_EOM_PREACCESS_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
