#!/usr/bin/env python3
"""Public, source-pixel-free LUNARSHIFT Gambart C camera-stage triage.

The workflow downloads one *published* positive development observation,
tests official ISIS 8.3/ALE geolocation, and commits only small diagnostics.
It does not touch the private isef4 repository or provisional holdouts.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PRODUCT = "M1138987659LE"
SOURCE_URL = (
    "https://pds.lroc.im-ldi.com/data/LRO-L-LROC-2-EDR-V1.0/"
    "LROLRC_0017/DATA/ESM/2013317/NAC/"
)
ROOT = Path.cwd()
SUFFIX = os.environ.get("ISEF4_DIAGNOSTIC_SUFFIX", "").strip()
if SUFFIX and not re.fullmatch(r"[a-z0-9_-]{1,20}", SUFFIX):
    raise ValueError("invalid diagnostic suffix")
OUTPUT = ROOT / "output" / ("triage_" + SUFFIX if SUFFIX else "triage")
STATUS = ROOT / "diagnostics" / (
    "isef4_gambart_camera_status" + ("_" + SUFFIX if SUFFIX else "") + ".json"
)
OUTPUT.mkdir(parents=True, exist_ok=True)
STATUS.parent.mkdir(parents=True, exist_ok=True)
RESULT = {
    "schema_version": "isef4-public-source-camera-triage-v1",
    "runtime_label": SUFFIX or "isis83",
    "event": "Xiao et al. 2025 Figure S5 Gambart C (published positive)",
    "product": PRODUCT,
    "target_latitude_deg_n": 3.218,
    "target_longitude_deg_e": 348.092,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "workflow": os.environ.get("GITHUB_WORKFLOW", ""),
    "run_id": os.environ.get("GITHUB_RUN_ID", ""),
    "commit_sha": os.environ.get("GITHUB_SHA", ""),
    "stages": {},
    "scientific_status": "camera-stage feasibility only; no recovered event",
}


def persist() -> None:
    tmp = STATUS.with_suffix(".json.part")
    tmp.write_text(json.dumps(RESULT, indent=2, sort_keys=True) + "\n")
    tmp.replace(STATUS)


def command(name: str, argv: list[str], timeout: int = 180) -> bool:
    p = OUTPUT / (name + ".log")
    try:
        process = subprocess.run(
            argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace", timeout=timeout, check=False,
        )
        logfile = process.stdout
        rc = process.returncode
    except Exception as exc:
        logfile = f"{type(exc).__name__}: {exc}"
        rc = -1
    p.write_text(logfile)
    # Retain *all relevant error lines* when a noisy USGSCSM plugin dumps
    # the entire large ISD repeatedly, which can bury the first cause beyond
    # the final log tail. Never include image bytes or full large ISDs.
    error_lines = [
        line[-1500:] for line in logfile.splitlines()
        if re.search(r"\berror\b|invalid|could not|exception|missing|\bwarn", line, re.I)
    ]
    RESULT["stages"][name] = {
        "returncode": rc,
        "log_tail": logfile[-6500:],
        "diagnostic_lines": error_lines[:12] + error_lines[-20:]
                            if len(error_lines) > 32 else error_lines,
        "full_log_bytes": len(logfile.encode("utf-8")),
    }
    persist()
    print(name, "RC", rc, logfile[-1000:], flush=True)
    return rc == 0


def configure() -> None:
    prefix = Path(os.environ["ISISROOT"])
    prefs = prefix / "IsisPreferences"
    text = prefs.read_text()
    group = 'Group = SpiceQL\n  UseSpiceQL = "true"\nEndGroup\n'
    if re.search(r"(?im)^\s*Group\s*=\s*SpiceQL\s*$", text):
        # Replace the whole group, not an unrelated UseSpiceQL keyword.
        text, count = re.subn(
            r"(?ims)^\s*Group\s*=\s*SpiceQL\s*\n.*?^\s*End[_ ]?Group\s*\n",
            group, text, count=1,
        )
        if count != 1:
            raise RuntimeError("SpiceQL group exists but could not be replaced")
    elif re.search(r"(?m)^End\s*$", text):
        text = re.sub(r"(?m)^End\s*$", lambda _: group + "End",
                      text, count=1)
    else:
        raise RuntimeError("IsisPreferences lacks final End")
    if SUFFIX == "isis10":
        # CSM CameraFactory discovers dynamic .so plugins only through the
        # Plugins/CSMDirectory paths. ALE success alone does not register CSM.
        csm_dir = prefix / "lib" / "csmplugins"
        files = sorted(csm_dir.glob("*.so"))
        RESULT["csm_plugin_directory"] = str(csm_dir)
        RESULT["csm_plugin_files"] = [p.name for p in files]
        plugin_group = (
            "Group = Plugins\n"
            '  CSMDirectory = ("' + str(csm_dir) + '/")\n'
            "EndGroup\n"
        )
        if re.search(r"(?im)^\s*Group\s*=\s*Plugins\s*$", text):
            text, n = re.subn(
                r"(?ims)^\s*Group\s*=\s*Plugins\s*\n.*?^\s*End[_ ]?Group\s*\n",
                lambda _: plugin_group, text, count=1,
            )
            if n != 1:
                raise RuntimeError("Plugins group exists but cannot be replaced")
        elif re.search(r"(?m)^End\s*$", text):
            text = re.sub(r"(?m)^End\s*$", lambda _: plugin_group + "End",
                          text, count=1)
        else:
            raise RuntimeError("IsisPreferences lacks final End for plugins")
    prefs.write_text(text)
    RESULT["spiceql_preference_enabled"] = bool(
        group.strip() in text
    )
    persist()


def fetch() -> bool:
    try:
        for ext in ("IMG", "xml"):
            destination = OUTPUT / (PRODUCT + "." + ext)
            h = hashlib.sha256()
            n = 0
            req = urllib.request.Request(
                SOURCE_URL + destination.name,
                headers={"User-Agent": "LUNARSHIFT-reproducible-public-probe/1.0"},
            )
            with urllib.request.urlopen(req, timeout=240) as src, destination.open("wb") as out:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    h.update(chunk)
                    n += len(chunk)
                    out.write(chunk)
            RESULT["stages"]["download_" + ext] = {
                "bytes": n, "sha256": h.hexdigest(),
                "source_url": SOURCE_URL + destination.name,
            }
            persist()
        return True
    except Exception as exc:
        RESULT["stages"]["download_error"] = {
            "error": type(exc).__name__ + ": " + str(exc)
        }
        persist()
        return False


def ale_probe(name: str, path: Path) -> None:
    probe = (
        "import ale; "
        "r=ale.load(" + repr(str(path)) +
        ',props={"web":True},formatter="ale",verbose=False,'
        "only_isis_spice=False,only_naif_spice=True); "
        'print("ALE_SUCCESS",type(r).__name__); '
        'print("ALE_TOP_KEYS",sorted(r) if isinstance(r,dict) else "")'
    )
    command("ale_" + name, [sys.executable, "-c", probe], timeout=90)


def csm_attempt(raw: Path) -> bool:
    """Use the working ALE 1.2+ LROC web ISD without local LRO CK databases.

    A failed CSM plugin/ground-point conversion remains separate from the
    success of ALE loading. Retain the original ISIS cube and ISD locally.
    """
    isd = OUTPUT / "before.raw.cub.json"
    ale_code = (
        "import ale,json; "
        "result=ale.load(" + repr(str(raw)) +
        ',props={"web":True},formatter="ale",verbose=False,'
        "only_isis_spice=False,only_naif_spice=True);"
        "json.dump(result,open(" + repr(str(isd)) + ',"w"),'
        'default=lambda o:o.tolist() if hasattr(o,"tolist") else str(o));'
        'print("ISD_KEYS", sorted(result));'
    )
    if not command("ale_isd", [sys.executable, "-c", ale_code], timeout=150):
        return False
    # Small exact-format evidence only: preserve input values/types needed
    # to understand the USGSCSM C++ parser (no kernels, no source pixels).
    isd_data = json.loads(isd.read_text(encoding="utf-8"))
    inspect = (
        "name_model", "image_lines", "image_samples",
        "focal2pixel_lines", "focal2pixel_samples",
        "line_scan_rate", "detector_center",
        "starting_ephemeris_time", "center_ephemeris_time",
        "detector_line_summing", "detector_sample_summing",
    )
    RESULT["ale_isd_interface"] = {
        k: {"type": type(isd_data.get(k)).__name__,
            "value": isd_data.get(k)[:4] if isinstance(isd_data.get(k), list)
                     else isd_data.get(k)}
        for k in inspect
    }
    # Compare *observed* NAIF distortion/mapping coefficients with ALE's
    # missing focal2pixel_lines. Never fabricate a camera parameter.
    nk = isd_data.get("naif_keywords", {})
    RESULT["ale_naif_transform_keys"] = {
        k: v for k, v in nk.items()
        if re.search(r"ITRANSL|ITRANSS|TRANSY|TRANSX|PIXEL_SIZE|SAMPLING_FACTOR", k)
    }
    persist()
    # Probe the actual LROC driver property separately, without modifying
    # the scientific ISD or suppressing the CSM failure.
    driver_code = (
        "from ale.drivers import get_driver_from_label,pre_parse_label; "
        "klass=get_driver_from_label(" + repr(str(raw)) +
        ',props={"web":True},verbose=False,'
        "only_isis_spice=False,only_naif_spice=True);"
        'print("DRIVER_CLASS",klass.__name__);'
        "d=klass(" + repr(str(raw)) +
        ',props={"web":True},parsed_label=pre_parse_label(' +
        repr(str(raw)) + '));'
        "\\nwith d as active:\\n"
        ' print("IKID",repr(active.ikid))\\n'
        ' print("DIRECTION",repr(active.spacecraft_direction))\\n'
        ' print("FOCAL_LINES",repr(active.focal2pixel_lines))\\n'
    )
    command("ale_direct_line_transform", [sys.executable, "-c", driver_code],
            timeout=130)
    # Force the documented NAC line-scan model, not all five USGSCSM
    # models. The generic search can flood the diagnostic with irrelevant
    # frame/push-frame errors that hide the line scanner's actual failure.
    if not command("csminit_linescan", [
        "csminit", f"from={raw}", f"isd={isd}", "targetname=Moon",
        "pluginname=UsgsAstroPluginCSM",
        "modelname=USGS_ASTRO_LINE_SCANNER_SENSOR_MODEL",
    ], timeout=120):
        return False
    center = OUTPUT / "csm_center_campt.pvl"
    center_ok = command("csm_campt_center", [
        "campt", f"from={raw}", "type=image",
        "sample=2532", "line=7680", f"to={center}",
    ], timeout=120)
    point = OUTPUT / "csm_event_campt.pvl"
    event_ok = command("csm_campt_event", [
        "campt", f"from={raw}", "type=ground",
        "latitude=3.218", "longitude=348.092",
        "allowoutside=false", f"to={point}",
    ], timeout=120)
    for tag, p in (("center", center), ("event", point)):
        if p.exists():
            RESULT["stages"]["csm_" + tag + "_pvl"] = {
                "pvl_tail": p.read_text(errors="replace")[-6000:]
            }
    if center_ok and event_ok:
        RESULT["scientific_status"] = (
            "ALE/CSM camera ground-coordinate query succeeded for the "
            "published BEFORE EDR; calibration, AFTER geometry, common "
            "projection, and geological event recovery remain untested"
        )
    else:
        RESULT["scientific_status"] = (
            "ALE/CSM initialized but camera image and/or published ground "
            "coordinate query failed; inspect CSM stage diagnostics"
        )
    persist()
    return center_ok and event_ok


def main() -> int:
    persist()
    RESULT["tool_versions"] = {}
    for name in ("lronac2isis", "spiceinit", "campt", "getkey"):
        RESULT["tool_versions"][name] = shutil.which(name)
    persist()
    try:
        configure()
    except Exception as exc:
        RESULT["stages"]["preference_error"] = {
            "error": type(exc).__name__ + ": " + str(exc)
        }
        persist()
        return 1
    # ALE's native web route is independently supported by ISIS 10 on this
    # published LROC EDR. Avoid downloading several GiB of irrelevant base
    # SPKs when testing CSM geometry; no provisional holdouts are accessed.
    if SUFFIX == "isis10":
        if not fetch():
            return 1
        raw = OUTPUT / "before.raw.cub"
        if not command("import", [
            "lronac2isis", f"from={OUTPUT / (PRODUCT + '.IMG')}", f"to={raw}"
        ], timeout=180):
            return 1
        if csm_attempt(raw):
            return 0
        for name, path in (
            ("cube", raw),
            ("pds3", OUTPUT / (PRODUCT + ".IMG")),
            ("pds4", OUTPUT / (PRODUCT + ".xml")),
        ):
            ale_probe(name, path)
        return 1

    # A conda ISIS install contains binaries but NOT the $ISISDATA/base
    # databases. In particular, WEB=false still needs the base LSK database
    # even when remote SPICE/SpiceQL supplies mission kernels.
    if not command("base_data", [
        "downloadIsisData", "base", os.environ["ISISDATA"],
        "--include={kernels/**,dems/*.db}",
    ], timeout=900):
        RESULT["scientific_status"] = (
            "ISISDATA base bootstrap failed, before any scientific geometry test"
        )
        persist()
        return 1
    required = Path(os.environ["ISISDATA"]) / "base" / "kernels" / "lsk"
    lsk = sorted(required.glob("kernels.????.db"))
    RESULT["base_lsk_databases"] = [str(p.relative_to(Path(os.environ["ISISDATA"]))) for p in lsk]
    persist()
    if not lsk:
        RESULT["scientific_status"] = "base download returned success without required LSK kernel database"
        persist()
        return 1
    if not fetch():
        return 1

    raw = OUTPUT / "before.raw.cub"
    if not command("import", [
        "lronac2isis", f"from={OUTPUT / (PRODUCT + '.IMG')}", f"to={raw}"
    ], timeout=180):
        return 1

    ok = command("spiceinit", [
        "spiceinit", f"from={raw}", "web=false"
    ], timeout=160)
    if not ok:
        for name, path in (
            ("cube", raw),
            ("pds3", OUTPUT / (PRODUCT + ".IMG")),
            ("pds4", OUTPUT / (PRODUCT + ".xml")),
        ):
            ale_probe(name, path)
        return 1

    # Independent camera-model positive control: an interior image-space
    # pixel must return geometry even if the rounded published event location
    # is incompatible with a particular DEM, overlap, or footprint.
    center = OUTPUT / "center_campt.pvl"
    center_ok = command("campt_center", [
        "campt", f"from={raw}", "type=image",
        "sample=2532", "line=7680", f"to={center}",
    ], timeout=90)
    point = OUTPUT / "event_campt.pvl"
    event_ok = command("campt", [
        "campt", f"from={raw}", "type=ground",
        "latitude=3.218", "longitude=348.092",
        "allowoutside=false", f"to={point}",
    ], timeout=90)
    if not center_ok or not event_ok:
        RESULT["scientific_status"] = (
            "camera initialized but one or both ground/image coordinate "
            "probes failed; consult separate stages; no event recovery"
        )
        persist()
        return 1

    if point.exists():
        RESULT["stages"]["event_campt"] = {
            "pvl_tail": point.read_text()[-6500:]
        }
        persist()
    RESULT["scientific_status"] = (
        "source camera event-coordinate query succeeded for BEFORE EDR; "
        "after EDR, calibration, mapping and event recovery remain untested"
    )
    persist()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
