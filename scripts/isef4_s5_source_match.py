#!/usr/bin/env python3
"""Exploratory source-raster location of *published* Xiao 2025 Figure S5.

Uses the unaltered original Word embedded image and the exact PDS3 EDR
byte windows from a separately documented GitHub Actions artifact. This is
NOT camera geolocation, calibrated change, new discovery, or holdout work.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import urllib.request
import zipfile
from pathlib import Path

import cv2
import numpy as np


SOURCE_ZIP_HASH = "132f3d2c2d6c8a5fcb102fe9dcfa5e2d33c6e60b6600c1c94d0d2bafb282c233"
S5_HASH = "3d0e494c40b92e7de66ce54f8317c646ad1d8a19e328bc2811cd7cc13d48dc7f"


def original_s5(manifest: Path) -> np.ndarray:
    meta = json.loads(manifest.read_text(encoding="utf-8").replace("\\n", ""))
    if meta["sha256"] != SOURCE_ZIP_HASH:
        raise RuntimeError("supplemental ZIP SHA differs from frozen original")
    req = urllib.request.Request(
        meta["source_url"],
        headers={"User-Agent": "LUNARSHIFT-published-S5-raw-matching/1.0"},
    )
    with urllib.request.urlopen(req, timeout=150) as response:
        content = response.read(40_000_001)
    if len(content) > 40_000_000 or hashlib.sha256(content).hexdigest() != SOURCE_ZIP_HASH:
        raise RuntimeError("supplemental ZIP bytes fail original published source hash")
    with zipfile.ZipFile(io.BytesIO(content)) as outer:
        docx = outer.read("2025-434-supplementarymaterials.docx")
    with zipfile.ZipFile(io.BytesIO(docx)) as doc:
        image = doc.read("word/media/image5.jpeg")
    if hashlib.sha256(image).hexdigest() != S5_HASH:
        raise RuntimeError("Word relationship image6 is not the original verified S5")
    raster = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
    if raster is None or raster.shape[1] != 1430 or raster.shape[0] != 469:
        raise RuntimeError("original published S5 raster dimensions changed")
    return raster


def normalize(gray: np.ndarray) -> np.ndarray:
    gray = np.asarray(gray)
    if gray.dtype != np.uint8:
        raise TypeError("expect native raw bytes or decoded 8-bit published panel")
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)


def panel(raster: np.ndarray, index: int, trim: float = 0.04) -> np.ndarray:
    """Return the published before/after panel, no ratio-image ingestion."""
    if index not in (0, 1):
        raise ValueError("only original pre/post panels, never ratio panel")
    w = raster.shape[1]
    a, b = round(index * w / 3), round((index + 1) * w / 3)
    image = cv2.cvtColor(raster[:, a:b], cv2.COLOR_BGR2GRAY)
    # Ignore panel divider and printed labels, not central geological pixels.
    margin_x = max(1, round(image.shape[1] * trim))
    margin_y = max(1, round(image.shape[0] * trim))
    return image[margin_y:-margin_y, margin_x:-margin_x]


def extract(image: np.ndarray, features: int) -> tuple[list, np.ndarray | None]:
    sift = cv2.SIFT_create(
        nfeatures=features, contrastThreshold=0.008, edgeThreshold=18, sigma=1.3
    )
    return sift.detectAndCompute(normalize(image), None)


def compare(
    panel_kp: list, panel_desc: np.ndarray | None,
    raw_kp: list, raw_desc: np.ndarray | None, *,
    ratio: float, panel_shape: tuple[int, int], raw_shape: tuple[int, int],
    raw_scale: float,
) -> dict:
    out = {
        "ratio_threshold": ratio,
        "panel_keypoints": len(panel_kp),
        "raw_keypoints": len(raw_kp),
        "tentative_unique_matches": 0,
        "inliers": 0,
        "status": "no feature-based source location",
    }
    if panel_desc is None or raw_desc is None or len(panel_desc) < 3 or len(raw_desc) < 3:
        return out
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    pairs = matcher.knnMatch(panel_desc, raw_desc, k=2)
    valid = [a for a, b in pairs if a.distance < ratio * b.distance]
    # One raw keypoint may be the closest for several marked source-panel features.
    selected = {}
    for m in sorted(valid, key=lambda x: x.distance):
        if m.trainIdx not in selected:
            selected[m.trainIdx] = m
    unique = list(selected.values())
    out["tentative_unique_matches"] = len(unique)
    if len(unique) < 5:
        return out
    src = np.array([panel_kp[m.queryIdx].pt for m in unique], np.float32)
    dst = np.array([raw_kp[m.trainIdx].pt for m in unique], np.float32)
    matrix, inlier = cv2.estimateAffinePartial2D(
        src, dst, method=cv2.RANSAC, ransacReprojThreshold=5.0,
        maxIters=12000, confidence=0.999, refineIters=15,
    )
    if matrix is None or inlier is None:
        return out
    selected_idx = inlier.reshape(-1).astype(bool)
    count = int(selected_idx.sum())
    out["inliers"] = count
    if count < 5:
        return out
    residual = np.linalg.norm(
        np.column_stack([src, np.ones(len(src), np.float32)]) @ matrix.T - dst,
        axis=1,
    )[selected_idx]
    coords = src[selected_idx]
    ph, pw = panel_shape
    x_cell = np.clip((coords[:, 0] / pw * 6).astype(int), 0, 5)
    y_cell = np.clip((coords[:, 1] / ph * 6).astype(int), 0, 5)
    out.update(
        median_residual_px_raw_half=float(np.median(residual)),
        p95_residual_px_raw_half=float(np.percentile(residual, 95)),
        spatial_occupied_6x6_cells=len(set(zip(x_cell.tolist(), y_cell.tolist()))),
        image_to_raw_half_affine=matrix.tolist(),
        panel_center_raw_full_xy=(
            (matrix @ np.array([pw / 2, ph / 2, 1.0])) / raw_scale
        ).tolist(),
    )
    # These are *correspondence* indicators, not lunar event validation.
    if count >= 8 and out["spatial_occupied_6x6_cells"] >= 3 and out["p95_residual_px_raw_half"] < 5:
        out["status"] = "provisional figure-to-raw terrain correspondence; visual review required"
    return out



def anchored_search(panel_features, raw_images):
    """Fixed source-camera marker ROI, rotations and mirrors; development only."""
    markers={"before":(3945.112,9406.253,8356),
             "after":(4475.082,1920.066,993)}
    rows=[]
    for role,(sample,line,firstrow) in markers.items():
        image=raw_images[role]
        cx,cy=sample*0.5,(line-1-firstrow)*0.5
        x0=max(0,int(cx-850));x1=min(image.shape[1],int(cx+850))
        y0=max(0,int(cy-480));y1=min(image.shape[0],int(cy+480))
        crop=image[y0:y1,x0:x1]
        pk,pd,pshape=panel_features[role]
        for rot in range(4):
            rotated=np.ascontiguousarray(np.rot90(crop,rot))
            for flip in (False,True):
                oriented=np.ascontiguousarray(np.fliplr(rotated)) if flip else rotated
                rk,rd=extract(oriented,12000)
                pairs=cv2.BFMatcher(cv2.NORM_L2).knnMatch(pd,rd,k=2)
                for ratio in (.78,.88):
                    match=[a for a,b in pairs if a.distance<ratio*b.distance]
                    x=np.float32([pk[m.queryIdx].pt for m in match])
                    y=np.float32([rk[m.trainIdx].pt for m in match])
                    entry={"role":role,"source_id":("M1138987659LE" if role=="before" else "M1200206882LE"),
                           "rotation_90_ccw":rot,"flip_after_rotation":flip,
                           "ratio":ratio,"tentative":len(match),
                           "marker_half_source_xy":[cx,cy],"crop_xyxy_half_source":[x0,y0,x1,y1],
                           "models":{}}
                    if len(x)>=6:
                        for model,fn in (("partial",cv2.estimateAffinePartial2D),
                                         ("full",cv2.estimateAffine2D)):
                            cv2.setRNGSeed(20260919)
                            M,mask=fn(x,y,method=cv2.RANSAC,
                                      ransacReprojThreshold=4.,maxIters=15000,
                                      confidence=.999,refineIters=20)
                            n=int(mask.sum()) if M is not None and mask is not None else 0
                            cells=0;p95=None
                            if n:
                                keep=mask.reshape(-1).astype(bool)
                                a=x[keep]
                                occupied=np.stack([np.clip((a[:,0]/pshape[1]*6).astype(int),0,5),
                                                   np.clip((a[:,1]/pshape[0]*6).astype(int),0,5)],axis=1)
                                cells=len({tuple(z) for z in occupied})
                                err=np.linalg.norm(a@M[:,:2].T+M[:,2]-y[keep],axis=1)
                                p95=float(np.percentile(err,95))
                            entry["models"][model]={"inliers":n,"occupied_6x6_cells":cells,
                                 "p95_px":p95,
                                 "matrix":M.tolist() if M is not None else None,
                                 "provisional":bool(n>=12 and cells>=4 and p95 is not None and p95<4)}
                    rows.append(entry)
    return {"scope":"exploratory source-camera anchored same-epoch source match, not event recovery",
            "test_count":len(rows),
            "maximum_inliers":max((v.get("inliers",0) for z in rows for v in z["models"].values()),default=0),
            "cases":rows}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-folder", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--scale", type=float, default=0.5)
    args = parser.parse_args()
    if not 0 < args.scale <= 1:
        raise ValueError("raw pyramid scale must be in (0,1]")
    original = original_s5(args.source_manifest)
    arrays = {
        "before": ("M1138987659LE_mirror_raw_counts.npy", 8356),
        "after": ("M1200206882LE_mirror_raw_counts.npy", 993),
    }
    record = {
        "schema_version": "isef4-correct-caption-adjacency-S5-vs-EDR-v4-anchored-orientation",
        "figure_media": "word/media/image5.jpeg",
        "figure_sha256": S5_HASH,
        "prior_v1_invalid": "v1 used correct Figure S5 image5.jpeg. v2/v3 used image6.jpeg, which is Figure S6 Naumann; discard v2/v3 figure-crosswalk results.",
        "original_figure_sha256": S5_HASH,
        "original_fig5_shape": list(original.shape),
        "EDR_pixel_units": "original uncalibrated unsigned 8-bit counts",
        "scientific_status": "exploratory figure-to-raw correspondence, NOT mapped event recovery",
        "raw_scale": args.scale,
        "pairs": [],
    }
    panel_features = {}
    for label, idx in (("before", 0), ("after", 1)):
        image = panel(original, idx)
        keypoints, desc = extract(image, 7000)
        panel_features[label] = (keypoints, desc, image.shape)
    raw_features = {}
    raw_images = {}
    for label, (filename, row_start) in arrays.items():
        path = args.raw_folder / filename
        if not path.is_file():
            raise FileNotFoundError(f"raw window artifact lacks exact source {filename}")
        arr = np.load(path, mmap_mode="r", allow_pickle=False)
        if arr.dtype != np.uint8 or arr.shape != (2048, 5064):
            raise ValueError(f"wrong EDR raw array: {filename} {arr.shape} {arr.dtype}")
        thumb = cv2.resize(
            arr, (round(arr.shape[1] * args.scale), round(arr.shape[0] * args.scale)),
            interpolation=cv2.INTER_AREA,
        )
        kps, desc = extract(thumb, 18000)
        raw_images[label] = thumb
        raw_features[label] = (kps, desc, thumb.shape, row_start)
    for source_label in ("before", "after"):
        panel_kp, panel_desc, panel_shape = panel_features[source_label]
        for raw_label in ("before", "after"):
            raw_kp, raw_desc, raw_shape, row_start = raw_features[raw_label]
            for ratio in (0.72, 0.82):
                out = compare(
                    panel_kp, panel_desc, raw_kp, raw_desc,
                    ratio=ratio, panel_shape=panel_shape, raw_shape=raw_shape,
                    raw_scale=args.scale,
                )
                out.update(
                    figure_panel=source_label, raw_epoch=raw_label,
                    raw_edr=arrays[raw_label][0].split("_")[0],
                    raw_full_row_window=[row_start, row_start + 2047],
                    note="raw band may not contain the published event; no claim from zero matches",
                )
                if "panel_center_raw_full_xy" in out:
                    out["panel_center_source_EDR_sample_line_estimate"] = [
                        out["panel_center_raw_full_xy"][0],
                        out["panel_center_raw_full_xy"][1] + row_start,
                    ]
                record["pairs"].append(out)
    record["anchored_search"]=anchored_search(panel_features,raw_images)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
