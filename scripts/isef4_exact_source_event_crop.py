#!/usr/bin/env python3
"""Extract exact raw-byte neighborhood of Gambart C PUBLISHED location.

The ground-to-image coordinate comes from official ISIS CSM campt. The raw
uint8 array comes from the independently preserved original PDS EDR HTTP
byte range. Neither published figure nor derived score chooses this center.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image


def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--raw-folder",type=Path,required=True)
    parser.add_argument("--camera-json",type=Path,required=True)
    parser.add_argument("--out-folder",type=Path,required=True)
    args=parser.parse_args()
    camera=json.loads(args.camera_json.read_text(encoding="utf-8"))
    source=json.loads((args.raw_folder/"source_labels_and_windows.json").read_text())
    if camera.get("product")!="M1138987659LE" or camera.get("source_role")!="before":
        raise RuntimeError("wrong source camera: expected original Gambart C before")
    if camera["stages"]["csm_campt_event"]["returncode"]!=0:
        raise RuntimeError("CSI event camera did not pass")
    if camera["stages"]["csminit_linescan"]["returncode"]!=0:
        raise RuntimeError("CSM camera did not initialize")
    if camera["target_latitude_deg_n"]!=3.218 or camera["target_longitude_deg_e"]!=348.092:
        raise RuntimeError("source camera was not queried at published source coordinate")
    pvl=camera["stages"]["csm_event_pvl"]["pvl_tail"]
    def num(field):
        found=re.search(r"(?m)^\s*"+re.escape(field)+r"\s*=\s*([-+]?\d+(?:\.\d+)?)",pvl)
        if found is None:raise RuntimeError("missing PVL "+field)
        return float(found.group(1))
    sample=num("Sample");line=num("Line")
    if abs(num("PlanetocentricLatitude")-3.218)>1e-7 or abs(
            num("PositiveEast360Longitude")-348.092)>1e-7:
        raise RuntimeError("PVL ground point does not match published marker")
    if not math.isfinite(sample) or not math.isfinite(line):
        raise RuntimeError("nonfinite camera source location")
    ref=[x for x in source if x["role"]=="before" and x["edr_id"]=="M1138987659LE"]
    if len(ref)!=1 or len(ref[0]["screening_windows"])!=1:
        raise RuntimeError("source PDS original before artifact inconsistent")
    entry=ref[0];window=entry["screening_windows"][0]
    path=args.raw_folder/"M1138987659LE_mirror_raw_counts.npy"
    raw=np.load(path,mmap_mode="r",allow_pickle=False)
    if raw.shape!=(2048,5064) or raw.dtype!=np.uint8:
        raise RuntimeError("original EDR window shape changed")
    if sha(raw.tobytes())!=window["raw_window_sha256"]:
        raise RuntimeError("raw source byte window no longer matches preserved HTTP range")
    # ISIS campt samples/lines are one-based; artifact HTTP range starts at
    # zero-based first_line in the original PDS EDR 8-bit image payload.
    source_x=int(math.floor(sample+0.5))-1
    source_y=int(math.floor(line+0.5))-1
    local_y=source_y-int(window["first_line"])
    if not (0<=source_x<5064 and 0<=local_y<2048):
        raise RuntimeError("published marker does not lie in source byte-window footprint")
    args.out_folder.mkdir(parents=True,exist_ok=True)
    crops=[]
    for radius in (128,256,400):
        xa=max(0,source_x-radius);xb=min(raw.shape[1],source_x+radius+1)
        ya=max(0,local_y-radius);yb=min(raw.shape[0],local_y+radius+1)
        part=np.asarray(raw[ya:yb,xa:xb]).copy()
        path=args.out_folder/f"before_source_marker_r{radius}_original_dn.npy"
        np.save(path,part,allow_pickle=False)
        preview=args.out_folder/f"before_source_marker_r{radius}_preview.png"
        lo,hi=np.percentile(part,[1,99])
        if hi<=lo:raise RuntimeError("degenerate original DN source crop")
        visual=np.rint(255*np.clip((part.astype(np.float32)-lo)/(hi-lo),0,1)).astype(np.uint8)
        Image.fromarray(visual,mode="L").save(preview)
        crops.append({
            "radius_source_pixel":radius,
            "rect_window_zero_based_xyxy_exclusive":[xa,ya,xb,yb],
            "shape":list(part.shape),
            "raw_count_min_max":[int(part.min()),int(part.max())],
            "raw_count_p01_p50_p99":[float(x) for x in np.percentile(part,[1,50,99])],
            "exact_original_dn_array_filename":path.name,
            "exact_original_dn_array_sha256":sha(path.read_bytes()),
            "visualization_only_png_filename":preview.name,
            "visualization_only_png_sha256":sha(preview.read_bytes()),
            "visualization_percentile_clip":[float(lo),float(hi)],
            "scientific_scope":"raw uncalibrated DN crop, visualization is contrast stretched"
        })
    out={
        "schema":"original-Gambart-C-before-campt-source-byte-crop-v1",
        "figure":"Xiao 2025 original supplementary S5",
        "source_product":"M1138987659LE",
        "source_pds3_label_sha256":entry["source_label_sha256"],
        "source_raw_range_sha256":window["raw_window_sha256"],
        "original_raw_artifact_run_id":"35422390895",
        "camera_diagnostic_run_id":camera["run_id"],
        "camera_source_commit":camera["commit_sha"],
        "source_ground_coord_lat_lon_e360":[3.218,348.092],
        "campt_sample_line_one_based":[sample,line],
        "nearest_original_edr_index_zero_based_xy":[source_x,source_y],
        "raw_strip_first_line_zero_based":window["first_line"],
        "raw_strip_local_marker_xy":[source_x,local_y],
        "marker_inside_byte_window":True,
        "crops":crops,
        "caveat":"ISIS cube-to-native PDS byte orientation/decompanding still needs independent cross-check. Published coordinate is rounded, NOT a landslide centroid. Raw uncalibrated DN is not a change detection.",
    }
    (args.out_folder/"source_crop_manifest.json").write_text(json.dumps(out,indent=2)+"\n")
    Path("diagnostics/isef4_gambart_before_grounded_raw_crop.json").write_text(json.dumps(
        {**out,"crops":[{k:v for k,v in p.items() if k not in (
            "exact_original_dn_array_filename","visualization_only_png_filename"
        )} for p in crops]},indent=2)+"\n")
    print(json.dumps(out,indent=2),flush=True)

if __name__=="__main__":
    main()
