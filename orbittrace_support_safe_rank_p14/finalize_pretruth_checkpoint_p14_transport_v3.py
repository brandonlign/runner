#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import pickle
import subprocess
import sys
from pathlib import Path

PARENT_TRANSPORT_SHA256 = "f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae"
TECHNICAL_TRANSPORT_SHA256 = "55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415"
REPAIR_AUDIT_RUN = 31326543587


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-p14-finalizer", required=True, type=Path)
    p.add_argument("--base-finalizer", required=True, type=Path)
    p.add_argument("--panel", required=True, choices=("hdbscan", "sugar"))
    p.add_argument("--core-input", required=True, type=Path)
    p.add_argument("--halo-pretruth", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    subprocess.run([
        sys.executable, str(a.base_p14_finalizer),
        "--base-finalizer", str(a.base_finalizer),
        "--panel", a.panel,
        "--core-input", str(a.core_input),
        "--halo-pretruth", str(a.halo_pretruth),
        "--output", str(a.output),
    ], check=True)

    raw = a.output.read_bytes()
    cp = pickle.loads(raw)
    require(cp["panel"] == a.panel, "P14 technical-finalizer panel mismatch")
    require(cp.get("p13_transport_source_sha256") == PARENT_TRANSPORT_SHA256, "unexpected parent P12 transport source")
    require(cp.get("competitor_cluster_values_accessed") is False, "competitor values entered technical finalizer")
    require(cp.get("known_shower_truth_accessed") is False, "truth entered technical finalizer")
    require(cp.get("p14_rank_frozen_before_truth") is True, "P14 rank not pretruth frozen")

    cp["p13_transport_parent_source_sha256"] = PARENT_TRANSPORT_SHA256
    cp["p13_transport_source_sha256"] = TECHNICAL_TRANSPORT_SHA256
    cp["p14_p12_snm_id_transport_repair_audit_run"] = REPAIR_AUDIT_RUN
    cp["p14_p12_snm_id_transport_scope"] = "audit-only source_seed_years derives from existing explicit source_year; numerical P12 science and membership unchanged"
    cp["p14_p12_snm_id_transport_scientific_delta"] = False

    out = pickle.dumps(cp, protocol=pickle.HIGHEST_PROTOCOL)
    a.output.write_bytes(out)
    a.output.with_suffix(a.output.suffix + ".sha256").write_text(hashlib.sha256(out).hexdigest() + "\n")
    print("P14_MATCHED_TECHNICAL_TRANSPORT_CHECKPOINT_FROZEN", a.panel, hashlib.sha256(out).hexdigest(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
