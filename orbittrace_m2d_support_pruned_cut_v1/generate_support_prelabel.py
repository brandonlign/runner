#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    here = Path(__file__).resolve().parent
    parent_path = here.parent / "orbittrace_topomodal_support_resolved_cut_v1" / "generate_prelabel.py"
    parent = load(parent_path, "support_cut_parent_exact")
    refined = load(here / "support_pruned_cut.py", "support_pruned_cut_exact")
    if float(parent.RADIUS) != 1.0 or int(parent.MIN_SUPPORT) != 4:
        raise RuntimeError("parent constants changed")
    parent.support_resolved_cut = refined.support_pruned_cut
    rc = int(parent.main())
    outdir = None
    import sys
    for i, x in enumerate(sys.argv):
        if x == "--output" and i + 1 < len(sys.argv):
            outdir = Path(sys.argv[i + 1])
            break
    if outdir is None:
        raise RuntimeError("missing --output")
    src = outdir / "TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL.json"
    payload = json.loads(src.read_text())
    if payload.get("shower_truth_used") is not False or payload.get("target_information_access") is not False or payload.get("target_region_events_accessed") is not False:
        raise RuntimeError("firewall flags changed")
    cfg = dict(payload.get("configuration", {}))
    cfg["cut_rule"] = "recurse_reportable_child_discard_immediate_subsupport_sibling_else_parent_when_both_children_subsupport"
    cfg["minimum_support"] = 4
    cfg["radius"] = 1.0
    cfg["ranking"] = "modal_contrast_desc_then_family_hash_asc"
    cfg["new_tuned_parameters"] = []
    payload["schema"] = "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_SUPPORT_PRELABEL"
    payload["scientific_role"] = "PRELABEL_TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_CUT_V1"
    payload["configuration"] = cfg
    payload["parent_cut_source_blob"] = "4988997c023d9df2b504372b4290dcab379a6dcc"
    payload["method_parameter_selection_from_result"] = False
    dst = outdir / "M2D_SUPPORT_PRUNED_CUT_V1_SUPPORT_PRELABEL.json"
    dst.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True, allow_nan=False) + "\n")
    src.unlink()
    print(json.dumps({"verdict": "PASS_SUPPORT_PRUNED_CUT_V1_PRELABEL", "subsets": len(payload["subsets"]), "cut_rule": cfg["cut_rule"]}, sort_keys=True), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
