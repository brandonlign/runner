#!/usr/bin/env python3
"""Real-PUNCH-background synthetic injection gate for the PUNCH KH project.

STRICT TARGET BLIND:
- Uses ONLY the preregistered non-target control date 2025-09-21.
- Does NOT download/open any C/2025 R3 frame.
- Injects synthetic growing traveling tails of known truth into fixed Level-2 CTM
  patches at approximately the R3 solar-elongation radius.

This validates image -> centerline recovery on real PUNCH mosaic/starfield texture.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import requests
from astropy.io import fits
from scipy.ndimage import shift, median_filter
from scipy.optimize import least_squares

OUT = Path("results/punch_kh_real_background_controls")
OUT.mkdir(parents=True, exist_ok=True)
ROOT = "https://umbra.nascom.nasa.gov/punch/2/CTM/2025/09/21/"
LISTING = ROOT

# Fixed before reading control pixels: three time-of-day strata and four cardinal
# patches at radius 850 pixels = 19.125 deg for 0.0225 deg/pixel CTM sampling.
TARGET_HOURS = [0, 8, 16]
PATCH_RADIUS_PX = 850
PATCH_CENTERS = {
    "E": (2048 + PATCH_RADIUS_PX, 2048),
    "W": (2048 - PATCH_RADIUS_PX, 2048),
    "N": (2048, 2048 + PATCH_RADIUS_PX),
    "S": (2048, 2048 - PATCH_RADIUS_PX),
}
PATCH_NX = 192
PATCH_NY = 81
N_TIME = 48
DT_HR = 8.0 / 60.0
WAVELENGTH_PX = 24.0
PHASE_SPEED_PX_HR = 8.0
GROWTH_RATE_HR = 0.35
INITIAL_AMPLITUDE_PX = 1.5
TAIL_SIGMA_PX = 3.0
BACKGROUND_DRIFT_PX_FRAME = 2.3

# Frozen synthetic peak contrast in local robust-background sigma units. These are
# image-domain controls, not claims about target surface brightness.
TAIL_PEAK_SIGMA = [3.0, 5.0, 8.0]

LOCAL_WIDTH_COLUMNS = 5
OUTLIER_THRESHOLD_PX = 3.0
MAX_INTERPOLATED_RUN_COLUMNS = 2
MAX_FLAGGED_FRACTION_PER_FRAME = 0.05

FILE_RE = re.compile(r'href=["\'](PUNCH_L2_CTM_(20250921\d{6})_v(0l)\.fits)["\']', re.I)


def choose_files():
    r = requests.get(LISTING, timeout=(10, 30))
    r.raise_for_status()
    rows = []
    for name, stamp, ver in FILE_RE.findall(r.text):
        hh = int(stamp[8:10]); mm = int(stamp[10:12]); ss = int(stamp[12:14])
        sec = hh * 3600 + mm * 60 + ss
        rows.append((sec, name))
    if not rows:
        raise RuntimeError("No v0l L2 CTM files found on frozen control date")
    selected = []
    for hour in TARGET_HOURS:
        target = hour * 3600
        sec, name = min(rows, key=lambda x: abs(x[0] - target))
        selected.append((sec, name))
    # Must be three distinct epochs.
    if len({x[1] for x in selected}) != 3:
        raise RuntimeError(f"Control selection collapsed to duplicate files: {selected}")
    return selected


def download_file(name: str) -> Path:
    p = OUT / name
    if not p.exists():
        with requests.get(ROOT + name, stream=True, timeout=(10, 120)) as r:
            r.raise_for_status()
            with p.open("wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
    return p


def robust_standardize(patch: np.ndarray):
    p = np.asarray(patch, float)
    finite = np.isfinite(p)
    if finite.mean() < 0.95:
        return None, {"finite_fraction": float(finite.mean())}
    med = float(np.nanmedian(p))
    mad = float(np.nanmedian(np.abs(p - med)))
    sigma = max(1.4826 * mad, float(np.nanstd(p)) * 0.1, 1e-30)
    z = (p - med) / sigma
    # Preserve real outliers/stars. Fill only truly missing pixels with local zero
    # after normalization so masks do not create NaN failures in image shifts.
    z[~finite] = 0.0
    return z, {"finite_fraction": float(finite.mean()), "median": med, "robust_sigma": sigma}


def extract_patch(data: np.ndarray, cx: int, cy: int):
    x0 = int(cx - PATCH_NX // 2); x1 = x0 + PATCH_NX
    y0 = int(cy - PATCH_NY // 2); y1 = y0 + PATCH_NY
    if x0 < 0 or y0 < 0 or x1 > data.shape[1] or y1 > data.shape[0]:
        raise RuntimeError("fixed control patch falls outside CTM array")
    return np.asarray(data[y0:y1, x0:x1], float)


def make_injected_movie(background: np.ndarray, peak_sigma: float):
    ny, nx = background.shape
    y = np.arange(ny, dtype=float) - (ny - 1) / 2.0
    x = np.arange(nx, dtype=float)
    t = np.arange(N_TIME, dtype=float) * DT_HR
    frames = []
    truth = []
    for i, ti in enumerate(t):
        # Shift real sky texture through the synthetic comet-centered coordinate
        # system; wrap is forbidden, newly exposed edge is filled by local median 0.
        bg = shift(background, shift=(0.0, -BACKGROUND_DRIFT_PX_FRAME * i),
                   order=1, mode="constant", cval=0.0, prefilter=False)
        amp = INITIAL_AMPLITUDE_PX * math.exp(GROWTH_RATE_HR * ti)
        center = amp * np.sin(2*np.pi*(x - PHASE_SPEED_PX_HR*ti)/WAVELENGTH_PX + 0.3)
        truth.append(center)
        img = bg.copy()
        # Mild downstream brightness taper; peak is expressed in robust background sigma.
        brightness = peak_sigma * (1.0 - 0.30 * x / nx)
        for j, c in enumerate(center):
            img[:, j] += brightness[j] * np.exp(-0.5 * ((y-c)/TAIL_SIGMA_PX)**2)
        frames.append(img)
    return y, t, np.asarray(frames), np.asarray(truth)


def fit_column(y: np.ndarray, flux: np.ndarray, halfwidth_px: float = 15.0):
    keep = np.abs(y) <= halfwidth_px
    yy = y[keep]
    ff = np.asarray(flux[keep], float)
    good = np.isfinite(yy) & np.isfinite(ff)
    yy, ff = yy[good], ff[good]
    if len(yy) < 12:
        return np.nan
    edge = np.r_[ff[:4], ff[-4:]]
    b0 = float(np.median(edge))
    amp0 = max(float(np.nanmax(ff)-b0), 0.05)
    # Real standardized backgrounds can contain large stellar outliers; widen only
    # amplitude/background numerical bounds, not the scientific center/width range.
    scale = max(float(np.nanstd(ff)), 1.0)
    p0 = np.array([b0, 0.0, amp0, 0.0, 3.0])
    lo = np.array([b0-20*scale, -5*scale, 0.0, -halfwidth_px, 1.0])
    hi = np.array([b0+20*scale,  5*scale, max(100*scale, amp0*2), halfwidth_px, 8.0])
    def model(p):
        b, slope, amp, center, sigma = p
        return b + slope*yy + amp*np.exp(-0.5*((yy-center)/sigma)**2)
    try:
        fit = least_squares(lambda p: ff-model(p), p0, bounds=(lo, hi),
                            loss="soft_l1", f_scale=0.5, max_nfev=500)
        return float(fit.x[3]) if fit.success else np.nan
    except Exception:
        return np.nan


def extract_centerline(frames: np.ndarray, y: np.ndarray):
    centers = np.full((frames.shape[0], frames.shape[2]), np.nan)
    for i, img in enumerate(frames):
        for j in range(img.shape[1]):
            centers[i, j] = fit_column(y, img[:, j])
    return centers


def runs(mask):
    padded = np.r_[False, np.asarray(mask, bool), False]
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    return list(zip(edges[0::2], edges[1::2]))


def apply_mask(raw: np.ndarray):
    reference = raw.copy()
    xx = np.arange(raw.shape[1])
    for row in reference:
        finite = np.isfinite(row)
        if finite.sum() >= 2:
            row[~finite] = np.interp(xx[~finite], xx[finite], row[finite])
    local = median_filter(reference, size=(1, LOCAL_WIDTH_COLUMNS), mode="nearest")
    flagged = np.isfinite(raw) & np.isfinite(local) & (np.abs(raw-local) > OUTLIER_THRESHOLD_PX)
    cleaned = raw.copy(); cleaned[flagged] = np.nan
    eligible = np.ones(raw.shape[0], dtype=bool)
    for i in range(raw.shape[0]):
        denom = max(1, int(np.isfinite(raw[i]).sum()))
        eligible[i] = flagged[i].sum()/denom <= MAX_FLAGGED_FRACTION_PER_FRAME
        for a,b in runs(flagged[i]):
            if b-a > MAX_INTERPOLATED_RUN_COLUMNS:
                continue
            left, right = a-1, b
            if left >= 0 and right < raw.shape[1] and np.isfinite(cleaned[i,left]) and np.isfinite(cleaned[i,right]):
                cleaned[i,a:b] = np.interp(np.arange(a,b), [left,right], [cleaned[i,left],cleaned[i,right]])
    return cleaned, flagged, eligible


def score(est, truth, flagged, eligible):
    good = np.isfinite(est) & np.isfinite(truth)
    err = np.abs(est[good]-truth[good])
    return {
        "median_abs_error_px": float(np.median(err)),
        "p90_abs_error_px": float(np.quantile(err, .90)),
        "p99_abs_error_px": float(np.quantile(err, .99)),
        "max_abs_error_px": float(np.max(err)),
        "valid_fraction": float(np.mean(good)),
        "flagged_fraction": float(np.mean(flagged)),
        "eligible_frame_fraction": float(np.mean(eligible)),
    }


def main():
    selected = choose_files()
    report = {
        "information_barrier": "2025-09-21 PUNCH L2 controls only; no C/2025 R3 files accessed",
        "selection_rule": {"target_hours_utc": TARGET_HOURS, "patch_radius_px": PATCH_RADIUS_PX,
                           "patch_centers": PATCH_CENTERS, "version": "0l"},
        "selected_files": [name for _,name in selected],
        "trials": [],
    }

    for _, name in selected:
        path = download_file(name)
        with fits.open(path, memmap=True) as hdul:
            data = np.asarray(hdul[1].data, float)
            # Do not use the packed uncertainty numerically yet; simply verify paired shape.
            unc_shape = tuple(hdul[2].data.shape)
            data_shape = tuple(data.shape)
            if data_shape != unc_shape:
                raise RuntimeError(f"science/uncertainty shape mismatch {data_shape} vs {unc_shape}")
            for label, (cx,cy) in PATCH_CENTERS.items():
                raw_patch = extract_patch(data, cx, cy)
                bg, bgstats = robust_standardize(raw_patch)
                if bg is None:
                    report["trials"].append({"file":name,"patch":label,"status":"PATCH_INVALID",**bgstats})
                    continue
                for peak in TAIL_PEAK_SIGMA:
                    y,t,frames,truth = make_injected_movie(bg, peak)
                    raw_center = extract_centerline(frames,y)
                    cleaned, flagged, eligible = apply_mask(raw_center)
                    metrics = score(cleaned,truth,flagged,eligible)
                    report["trials"].append({"file":name,"patch":label,"peak_sigma":peak,
                                             "status":"OK",**bgstats,**metrics})
        # Release memory and delete local control FITS after metrics are derived.
        try: path.unlink()
        except OSError: pass

    good = [r for r in report["trials"] if r.get("status") == "OK"]
    report["summary"] = {
        "n_trials": len(good),
        "n_invalid_patches": sum(r.get("status") != "OK" for r in report["trials"]),
        "p90_of_trial_p90_error_px": float(np.quantile([r["p90_abs_error_px"] for r in good], .90)) if good else None,
        "worst_trial_p90_error_px": float(max(r["p90_abs_error_px"] for r in good)) if good else None,
        "minimum_valid_fraction": float(min(r["valid_fraction"] for r in good)) if good else None,
        "maximum_flagged_fraction": float(max(r["flagged_fraction"] for r in good)) if good else None,
        "minimum_eligible_frame_fraction": float(min(r["eligible_frame_fraction"] for r in good)) if good else None,
        "by_peak_sigma": {},
    }
    for peak in TAIL_PEAK_SIGMA:
        sub=[r for r in good if r["peak_sigma"]==peak]
        report["summary"]["by_peak_sigma"][str(peak)] = {
            "n":len(sub),
            "median_p90_error_px":float(np.median([r["p90_abs_error_px"] for r in sub])) if sub else None,
            "p90_trial_p90_error_px":float(np.quantile([r["p90_abs_error_px"] for r in sub],.90)) if sub else None,
            "min_valid_fraction":float(min(r["valid_fraction"] for r in sub)) if sub else None,
        }

    # Frozen preliminary real-background centerline gate. This does not yet include
    # downstream wave-parameter inference; it decides whether that next step is warranted.
    s=report["summary"]
    gate = bool(good) and s["p90_of_trial_p90_error_px"] <= 1.5 and s["minimum_valid_fraction"] >= 0.98 and s["minimum_eligible_frame_fraction"] >= 0.90
    report["centerline_real_background_gate"] = "PASS" if gate else "FAIL"

    (OUT/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report["summary"],indent=2,sort_keys=True))
    print("GATE", report["centerline_real_background_gate"])
    return 0 if gate else 3


if __name__ == "__main__":
    raise SystemExit(main())
