#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py

EXPECTED_NAME = "data/2016/03/kep_collect.h5"
EXPECTED_SIZE = 139_028_822


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--hdf5", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    if a.hdf5.stat().st_size != EXPECTED_SIZE:
        raise RuntimeError("first HDF5 size changed")

    records: list[dict] = []
    with h5py.File(a.hdf5, "r") as f:
        records.append(
            {
                "path": "/",
                "object_type": "group",
                "attribute_names": sorted(str(k) for k in f.attrs.keys()),
            }
        )

        def visitor(name: str, obj: object) -> None:
            rec = {
                "path": "/" + name,
                "object_type": (
                    "dataset"
                    if isinstance(obj, h5py.Dataset)
                    else "group"
                    if isinstance(obj, h5py.Group)
                    else type(obj).__name__
                ),
                "attribute_names": sorted(str(k) for k in obj.attrs.keys()),
            }
            if isinstance(obj, h5py.Dataset):
                rec.update(
                    {
                        "shape": [int(x) for x in obj.shape],
                        "rank": len(obj.shape),
                        "dtype": str(obj.dtype),
                        "chunks": None
                        if obj.chunks is None
                        else [int(x) for x in obj.chunks],
                        "compression": obj.compression,
                        "shuffle": bool(obj.shuffle),
                        "fletcher32": bool(obj.fletcher32),
                    }
                )
            records.append(rec)

        f.visititems(visitor)

    result = {
        "schema": "orbittrace-v8-maarsy-rcs-stage0g-hdf5-structure-v1",
        "member_name": EXPECTED_NAME,
        "member_size": EXPECTED_SIZE,
        "h5py_version": h5py.__version__,
        "objects": records,
        "scientific_member_payload_materialized": True,
        "hdf5_structural_metadata_inspected": True,
        "hdf5_dataset_value_read": False,
        "hdf5_attribute_value_read": False,
        "event_scientific_value_interpreted": False,
        "v8_scientific_evaluation_performed": False,
        "target_information_access": False,
        "gmn_stage_a_or_b_access": False,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "object_count": len(records),
                "dataset_paths": [
                    r["path"] for r in records if r["object_type"] == "dataset"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
