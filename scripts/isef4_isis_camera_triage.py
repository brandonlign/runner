#!/usr/bin/env python3
"""Public, source-pixel-free LUNARSHIFT Gambart C camera-stage triage.

The workflow downloads one *published* positive development observation,
tests official ISIS 8.3/ALE geolocation, and commits only small diagnostics.
It does not touch the private isef4 repository or provisional holdouts.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROLE = os.environ.get("ISEF4_PRODUCT_ROLE", "before").strip()
if ROLE not in ("before", "after"):
    raise ValueError("ISEF4_PRODUCT_ROLE must be before or after")
PRODUCT = {"before": "M1138987659LE", "after": "M1200206882LE"}[ROLE]
SOURCE_URL = (
    "https://pds.lroc.im-ldi.com/data/LRO-L-LROC-2-EDR-V1.0/"
    + {"before": "LROLRC_0017/DATA/ESM/2013317/NAC/",
       "after": "LROLRC_0025/DATA/ESM/2015296/NAC/"}[ROLE]
)
EXPECTED_IMG_BYTES = {"before": 77788104, "after": 140014536}[ROLE]
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
    "source_role": ROLE,
    "expected_edr_bytes": EXPECTED_IMG_BYTES,
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
    if SUFFIX.startswith("isis10"):
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
            if ext == "IMG" and n != EXPECTED_IMG_BYTES:
                raise ValueError(
                    f"source EDR length mismatch for {PRODUCT}: "
                    f"{n} != {EXPECTED_IMG_BYTES}"
                )
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


def normalize_lroc_nac_distortion(isd_data: dict) -> dict:
    """Repair a serialization-only shape defect using the same NAC-L NAIF IK.

    This modifies only a derived ALE ISD, NEVER a raw cube/PDS label.
    Refuse if the source calibration is missing or disagrees with the ISD.
    """
    if isd_data.get("name_model") != "USGS_ASTRO_LINE_SCANNER_SENSOR_MODEL":
        raise ValueError("not a supported line-scanner ISD")
    keywords = isd_data.get("naif_keywords")
    if not isinstance(keywords, dict):
        raise ValueError("NAIF source calibration missing")
    source = keywords.get("INS-85600_OD_K")
    if isinstance(source, list):
        if len(source) != 1:
            raise ValueError("NAC-L source OD_K does not have one element")
        source = source[0]
    if isinstance(source, bool) or not isinstance(source, (int, float)):
        raise ValueError("source OD_K is not numeric")
    source = float(source)
    if not math.isfinite(source):
        raise ValueError("source OD_K is not finite")

    distortion = isd_data.get("optical_distortion")
    if not isinstance(distortion, dict) or set(distortion) != {"lrolrocnac"}:
        raise ValueError("ISD is not the official LRO NAC distortion model")
    model = distortion["lrolrocnac"]
    if not isinstance(model, dict) or set(model) != {"coefficients"}:
        raise ValueError("unexpected NAC distortion structure")
    previous = model["coefficients"]
    if isinstance(previous, list):
        if len(previous) != 1:
            raise ValueError("NAC optical distortion must contain exactly one coefficient")
        candidate = previous[0]
    else:
        candidate = previous
    if candidate is None:
        candidate = source
    if isinstance(candidate, bool) or not isinstance(candidate, (int, float)):
        raise ValueError("derived NAC distortion is not numeric")
    candidate = float(candidate)
    if not math.isfinite(candidate):
        raise ValueError("derived NAC distortion is not finite")
    if not math.isclose(candidate, source, rel_tol=1e-10, abs_tol=1e-13):
        raise ValueError("derived NAC distortion disagrees with original NAIF IK")

    model["coefficients"] = [source]
    return {
        "instrument": "NAC-L (-85600)",
        "field": "optical_distortion.lrolrocnac.coefficients",
        "original_type": type(previous).__name__,
        "original_value": previous,
        "verified_source_key": "INS-85600_OD_K",
        "verified_source_value": source,
        "repaired_coefficients": [source],
        "status": "already_vector" if isinstance(previous, list) else "repaired_derived_isd_only",
    }


def csm_attempt(raw: Path) -> bool:
    """Use the working ALE 1.2+ LROC web ISD without local LRO CK databases.

    A failed CSM plugin/ground-point conversion remains separate from the
    success of ALE loading. Retain the original ISIS cube and ISD locally.
    """
    isd = OUTPUT / (ROLE + ".raw.cub.json")
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
    state = isd_data.get("instrument_position", {})
    state_times = state.get("ephemeris_times", [])
    state_velocities = state.get("velocities", [])
    RESULT["ale_j2000_state_audit"] = {
        "reference_frame": state.get("reference_frame"),
        "state_samples": len(state_times),
        "velocity_samples": len(state_velocities),
        "time_range": [state_times[0], state_times[-1]] if state_times else [],
        "first_velocity": state_velocities[0] if state_velocities else None,
        "center_et": isd_data.get("center_ephemeris_time"),
        "starting_et": isd_data.get("starting_ephemeris_time"),
        "note": "only geometry summaries; no source image pixels",
    }
    persist()
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
    # Preserve enough of the actual ALE spacecraft-state table to tell
    # whether the needed exposure epoch is bracketed by returned data.
    # This is technical camera telemetry, never the lunar source pixels.
    ip = isd_data.get("instrument_position") or {}
    ets = ip.get("ephemeris_times") or []
    velocities = ip.get("velocities") or []
    RESULT["ale_state_table_audit"] = {
        "reference_frame": ip.get("reference_frame"),
        "time_count": len(ets),
        "first_time": ets[0] if ets else None,
        "last_time": ets[-1] if ets else None,
        "velocity_count": len(velocities),
        "first_velocity": velocities[0] if velocities else None,
        "first_time_minus_start_s": (
            float(ets[0]) - float(isd_data["starting_ephemeris_time"])
            if ets else None
        ),
    }
    persist()
    # Probe the actual LROC driver property separately, without modifying
    # the scientific ISD or suppressing the CSM failure.
    # Compute the exact signed NAC line transformation with the official ALE
    # driver. If the remote SPK request needed *only for flight direction*
    # fails, reproduce its own calculation using the time-matched J2000
    # velocity returned in the successfully loaded ALE ISD and the driver's
    # official J2000->LRO_SC_BUS frame chain. Never infer sign from an
    # observation date, detector layout, or an arbitrary image flip.
    driver_code = "\n".join([
        "import json, numpy as np, pyspiceql, spiceypy as spice",
        "from ale.drivers import get_driver_from_label, pre_parse_label",
        "klass=get_driver_from_label(" + repr(str(raw)) +
        ',props={"web":True},verbose=False,only_isis_spice=False,'
        "only_naif_spice=True)",
        'print("DRIVER_CLASS",klass.__name__)',
        "d=klass(" + repr(str(raw)) +
        ',props={"web":True},parsed_label=pre_parse_label(' +
        repr(str(raw)) + "))",
        "with d as active:",
        ' print("IKID",repr(active.ikid))',
        " try:",
        "  direction=float(active.spacecraft_direction)",
        '  print("DIRECTION_PROVENANCE","remote_SpiceQL_state")',
        " except Exception as error:",
        '  print("REMOTE_DIRECTION_ERROR",repr(error))',
        '  if "SPKINSUFFDATA" not in str(error): raise',
        "  support=json.load(open(" + repr(str(isd)) + "))",
        '  ip=support["instrument_position"]',
        '  times=np.asarray(ip["ephemeris_times"],dtype=float)',
        '  velocities=np.asarray(ip["velocities"],dtype=float)',
        '  epoch=float(active.ephemeris_start_time)',
        '  if ip["reference_frame"] != 1: raise ValueError("ALE velocity is not J2000")',
        '  if times.ndim!=1 or velocities.shape!=(len(times),3) or len(times)<2: raise ValueError("bad ALE state array shape")',
        '  if not (np.isfinite(times).all() and np.isfinite(velocities).all() and np.all(np.diff(times)>0)): raise ValueError("invalid ALE state samples")',
        '  if not (times[0]<=epoch<=times[-1]): raise ValueError("ALE state does not cover NAC start")',
        '  hi=int(np.searchsorted(times,epoch,side="left"))',
        '  if hi==0: lo=hi=0',
        '  elif hi>=len(times): lo=hi=len(times)-1',
        '  else: lo=hi-1',
        '  if hi!=lo and times[hi]-times[lo]>30.0: raise ValueError("ALE state sampling gap too large for directional inference")',
        '  weight=0.0 if hi==lo else float((epoch-times[lo])/(times[hi]-times[lo]))',
        '  velocity=(1-weight)*velocities[lo]+weight*velocities[hi]',
        "  bus_id=pyspiceql.translateNameToCode(frame='LRO_SC_BUS',mission=active.spiceql_mission,searchKernels=active.search_kernels,useWeb=active.use_web)[0]",
        '  rotate=active.frame_chain.compute_rotation(1,bus_id)',
        '  if (rotate.source,rotate.dest)!=(1,bus_id): raise ValueError("ALE bus rotation frame mismatch")',
        '  if hasattr(rotate,"times") and not (rotate.times[0]<=epoch<=rotate.times[-1]): raise ValueError("ALE bus rotation does not cover NAC start")',
        '  bus_v=np.asarray(rotate.apply_at(velocity,epoch),dtype=float).reshape(-1,3)[0]',
        '  direction=float(bus_v[0])',
        '  if not np.isfinite(direction) or abs(direction)<0.01: raise ValueError("ambiguous LRO bus X velocity")',
        '  active._spacecraft_direction=direction',
        '  print("DIRECTION_PROVENANCE","ALE_ISD_J2000_velocity_rotated_using_official_ALE_frame_chain")',
        '  print("SUPPORT_EPOCH",epoch)',
        '  print("SUPPORT_STATE_BRACKET",json.dumps([float(times[lo]),float(times[hi])]))',
        '  print("SUPPORT_J2000_VELOCITY",json.dumps(velocity.tolist()))',
        '  print("BUS_X_VELOCITY",direction)',
        ' print("DIRECTION",direction)',
        ' print("FOCAL_LINES_JSON",json.dumps(np.asarray(active.focal2pixel_lines).tolist()))',
    ]) + "\n"
    compile(driver_code, "<ale_lroc_driver_probe>", "exec")
    direct_ok = command(
        "ale_direct_line_transform", [sys.executable, "-c", driver_code],
        timeout=130,
    )
    if isd_data.get("focal2pixel_lines") is None:
        # A CSM sensor model cannot be constructed from a null line
        # transformation. Repair *only* if the same official ALE LROC
        # driver independently returns the flight-direction-aware value;
        # independently compare its magnitude against the actual PDS
        # NAIF inverse pixel mapping. No guessed sign or replacement pixel.
        direct_log = (OUTPUT / "ale_direct_line_transform.log").read_text()
        observed = re.search(
            r"(?m)^FOCAL_LINES_JSON (\[[^\r\n]+\])\s*$", direct_log
        )
        coeff = nk.get("INS-85600_ITRANSL")
        factor = isd_data.get("detector_sample_summing")
        if (direct_ok and observed is not None
                and "LroLrocNac" in direct_log
                and re.search(r"(?m)^IKID -85600\s*$", direct_log)
                and isinstance(coeff, list) and len(coeff) == 3
                and isinstance(factor, (int, float)) and factor > 0
                and isd_data.get("name_model")
                    == "USGS_ASTRO_LINE_SCANNER_SENSOR_MODEL"):
            candidate = json.loads(observed.group(1))
            if (isinstance(candidate, list) and len(candidate) == 3
                    and all(isinstance(v, (float, int)) and
                            __import__("math").isfinite(v)
                            for v in candidate)
                    and all(abs(abs(float(v)) -
                                abs(float(n) / float(factor))) < 0.0001
                            for v, n in zip(candidate, coeff))):
                original = OUTPUT / (ROLE + ".original_ale_isd.json")
                shutil.copyfile(isd, original)
                isd_data["focal2pixel_lines"] = candidate
                isd.write_text(json.dumps(isd_data))
                RESULT["derived_isd_repair"] = {
                    "field": "focal2pixel_lines",
                    "original": None,
                    "direct_ale_driver": candidate,
                    "naif_itransl": coeff,
                    "detector_sample_summing": factor,
                    "sign_from_verified_ALE_spacecraft_state_not_guessed": True,
                    "direction_provenance": (
                        re.search(r"(?m)^DIRECTION_PROVENANCE (.+)$", direct_log)
                        .group(1)
                    ),
                    "original_isd_preserved_locally": str(original),
                }
                persist()
            else:
                RESULT["derived_isd_repair"] = {
                    "status": "rejected: driver's value does not match "
                              "physical NAIF inverse pixel transform"
                }
                persist()
        else:
            RESULT["derived_isd_repair"] = {
                "status": "not attempted: live-driver verified signed "
                          "transformation is unavailable; no inferred sign"
            }
            persist()
    # ALE may serialize the single official NAC optical distortion as a
    # scalar/null, while USGSCSM requires a vector<double>. Correct ONLY
    # the derived JSON, checking the exact NAC-L NAIF instrument keyword.
    # Deliberately require successful direction/line-transform recovery
    # before attempting this independent secondary camera-field repair.
    if (RESULT.get("derived_isd_repair", {}).get("field")
            == "focal2pixel_lines"):
        try:
            audit = normalize_lroc_nac_distortion(isd_data)
            RESULT["distortion_shape_audit"] = audit
            if audit["status"] == "repaired_derived_isd_only":
                isd.write_text(json.dumps(isd_data))
            persist()
        except ValueError as exc:
            RESULT["distortion_shape_audit"] = {
                "status": "rejected_without_fabrication",
                "reason": str(exc),
                "naif_od_k": nk.get("INS-85600_OD_K"),
                "raw_derived_optical_distortion": isd_data.get(
                    "optical_distortion"
                ),
            }
            persist()
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
    if SUFFIX.startswith("isis10"):
        if not fetch():
            return 1
        raw = OUTPUT / (ROLE + ".raw.cub")
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

    raw = OUTPUT / (ROLE + ".raw.cub")
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
