#!/usr/bin/env python3
"""Height-only ray geometry sensitivity for a published LROC positive.

Read the TWO immutable passing source-camera PVLs and the predeclared local
source-strip match audit. Intersect each exact camera ray with concentric
spherical surfaces at declared heights. Compare *magnitude* of their relative
tangent-plane shifts to the independent camera-vs-raw-fit displacement.

This deliberately tests only a common radial height perturbation on fixed
CSM camera rays; it does not establish a site DEM, pointing error, controlled
geolocation, morphology, event recovery, or an explanation for the mismatch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

PUBLISHED = (3.218, 348.092)
HEIGHTS_M = (-3000, -1000, 0, 100, 500, 1000, 2000, 3000, 5000)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pv_num(pvl, field):
    m = re.search(
        r"^\s*" + re.escape(field) + r"\s*=\s*([-+]?\d+(?:\.\d+)?)",
        pvl, re.MULTILINE,
    )
    if m is None:
        raise ValueError("missing camera PVL " + field)
    v = float(m.group(1))
    if not math.isfinite(v):
        raise ValueError("nonfinite camera PVL " + field)
    return v


def pv_vec(pvl, field):
    m = re.search(r"^\s*" + re.escape(field) + r"\s*=\s*\(([^)]*)\)",
                  pvl, re.MULTILINE)
    if m is None:
        raise ValueError("missing camera PVL vector " + field)
    v = [float(x) for x in m.group(1).replace("\n", "").split(",")]
    if len(v) != 3 or not all(math.isfinite(x) for x in v):
        raise ValueError("invalid camera PVL vector " + field)
    return v


def sub(a, b):
    return [x-y for x,y in zip(a,b)]


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def length(x):
    return math.sqrt(dot(x,x))


def unit(x):
    n = length(x)
    if n <= 0:
        raise ValueError("zero vector")
    return [a/n for a in x]


def read_camera(path, role):
    d = json.loads(path.read_text())
    if d.get("source_role") != role:
        raise ValueError("wrong original camera role")
    required = {"before":("M1138987659LE","35453750360"),
                "after":("M1200206882LE","35454067791")}
    product, run = required[role]
    if d.get("product") != product or d.get("run_id") != run:
        raise ValueError("camera source or successful run is not pinned")
    for stage in ("csminit_linescan", "csm_campt_center", "csm_campt_event"):
        if d.get("stages",{}).get(stage,{}).get("returncode") != 0:
            raise ValueError("unverified camera stage " + stage)
    pvl = d["stages"]["csm_event_pvl"]["pvl_tail"]
    if (abs(pv_num(pvl,"PlanetocentricLatitude")-PUBLISHED[0])>1e-8 or
        abs(pv_num(pvl,"PositiveEast360Longitude")-PUBLISHED[1])>1e-8):
        raise ValueError("not the published source coordinate")
    pos = pv_vec(pvl,"SpacecraftPosition")
    ground = pv_vec(pvl,"BodyFixedCoordinate")
    direction = unit(sub(ground,pos))
    reported = pv_vec(pvl,"LookDirectionBodyFixed")
    if length(sub(direction,reported)) > 1e-7:
        raise ValueError("camera PVL optical ray disagrees with spacecraft and target")
    radius = pv_num(pvl,"LocalRadius")/1000
    if abs(length(ground)-radius) > 1e-7:
        raise ValueError("camera PVL radius and ground coordinate disagree")
    return {
        "role":role, "product":product, "run":run,
        "source_camera_json_sha256":sha(path),
        "spacecraft_km":pos, "sphere_ground_km":ground,
        "ray_unit":direction, "reference_radius_km":radius,
        "sample_resolution_m":pv_num(pvl,"SampleResolution"),
        "line_resolution_m":pv_num(pvl,"LineResolution"),
        "oblique_pixel_resolution_m":pv_num(pvl,"ObliquePixelResolution"),
        "off_nadir_deg":pv_num(pvl,"OffNadirAngle"),
    }


def intersection(cam, height_m):
    p,d = cam["spacecraft_km"],cam["ray_unit"]
    r = cam["reference_radius_km"] + height_m/1000.
    pd = dot(p,d)
    discriminant = pd*pd-dot(p,p)+r*r
    if discriminant < 0:
        raise ValueError("ray misses requested sphere")
    t = -pd-math.sqrt(discriminant)
    if t <= 0:
        raise ValueError("intersection not forward along observed ray")
    return [p[i]+t*d[i] for i in range(3)]


def sensitivity(before,after,h):
    g = before["sphere_ground_km"]
    east = unit([-g[1],g[0],0])
    up = unit(g)
    north = unit([up[1]*east[2]-up[2]*east[1],
                  up[2]*east[0]-up[0]*east[2],
                  up[0]*east[1]-up[1]*east[0]])
    def en(cam):
        displacement = [1000*x for x in sub(intersection(cam,h),g)]
        return [dot(displacement,east),dot(displacement,north)]
    b,a=en(before),en(after)
    delta=sub(a,b)
    return {
        "common_radial_height_m":h,
        "before_ray_tangent_east_north_m":b,
        "after_ray_tangent_east_north_m":a,
        "after_minus_before_tangent_east_north_m":delta,
        "differential_parallax_norm_m":length(delta),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--before",required=True,type=Path)
    ap.add_argument("--after",required=True,type=Path)
    ap.add_argument("--local-audit",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    before=read_camera(args.before,"before")
    after=read_camera(args.after,"after")
    if length(sub(before["sphere_ground_km"],
                  after["sphere_ground_km"]))>1e-7:
        raise ValueError("two CSM camera rays do not refer to identical sphere point")
    audit=json.loads(args.local_audit.read_text())
    if audit.get("schema") != "gambart-c-camera-marker-local-raw-registration-dev-v1":
        raise ValueError("local control diagnostic identity mismatch")
    radii={}
    for r in (128,256,512):
        fit=audit["local_fixed_radii"][str(r)]
        if fit.get("status")!="fit":
            radii[str(r)]={"status":"unassessable"}
            continue
        xy=fit["marker_minus_independent_camera_before_original_px"]
        meters=math.hypot(xy[0]*before["sample_resolution_m"],
                          xy[1]*before["line_resolution_m"])
        radii[str(r)]={"source_marker_discordance_original_px":xy,
            "source_marker_discordance_norm_original_px":math.hypot(*xy),
            "approx_before_camera_pixel_scale_m":meters,
            "fitted_off_marker_correspondences":fit["ransac_inliers"],
            "central_withheld_correspondences":fit["central_excluded_tentative_matches"]}
    samples=[sensitivity(before,after,h) for h in HEIGHTS_M]
    zero=next(x for x in samples if x["common_radial_height_m"]==0)
    if zero["differential_parallax_norm_m"]>1e-4:
        raise ValueError("zero-height rays do not meet at common sphere marker")
    # Conditional calculation only: camera sample/line nominal resolutions
    # and raw affine marker components are not independent map coordinates.
    m=radii["256"]["approx_before_camera_pixel_scale_m"]
    lo,hi=0.,20000.
    if sensitivity(before,after,hi)["differential_parallax_norm_m"]<m:
        inferred=None
    else:
        for _ in range(60):
            mid=(lo+hi)/2
            if sensitivity(before,after,mid)["differential_parallax_norm_m"]<m:
                lo=mid
            else:
                hi=mid
        inferred=(lo+hi)/2
    output={
        "schema":"gambart-published-marker-spherical-ray-height-stress-test-v1",
        "scientific_scope":"known positive, source-camera-only sensitivity diagnosis",
        "source":{k:{"product":v["product"],"run":v["run"],
                    "camera_json_sha256":v["source_camera_json_sha256"],
                    "reference_radius_km":v["reference_radius_km"],
                    "off_nadir_deg":v["off_nadir_deg"],
                    "sample_resolution_m":v["sample_resolution_m"],
                    "line_resolution_m":v["line_resolution_m"]}
                  for k,v in (("before",before),("after",after))},
        "local_audit_json_sha256":sha(args.local_audit),
        "observed_control_fit_discordance":radii,
        "height_only_exact_ray_sensitivity":samples,
        "conditional_equal_magnitude_height_m_at_radius256":inferred,
        "coordinate_basis":"local east/north at shared published sphere point",
        "strong_limitations":[
          "The inferred height is NOT an estimated real elevation or measured lunar topography.",
          "Models a common radial height changing both predeclared CSM rays; does not adjust camera pointing, kernels, focal-plane coordinate convention or shape model.",
          "Converting unprojected source affine pixels to ground metric through one epoch's nominal sample/line resolution is approximate.",
          "The local RANSAC fit establishes correspondence on the same source pair, not independent positional ground truth.",
          "No DEM or calibrated common map exists, and this cannot determine the actual cause of the source-marker disagreement.",
          "No positive published event has been recovered by the change detector and no new landslide has been found.",
        ],
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps({"output":str(args.out),"relative_parallax_1km_m":
      sensitivity(before,after,1000)["differential_parallax_norm_m"],
      "approx_observed_m":m,
      "conditional_equal_magnitude_height_m":inferred,
      "no_new_landslide":True},indent=2))


if __name__=="__main__":
    main()
