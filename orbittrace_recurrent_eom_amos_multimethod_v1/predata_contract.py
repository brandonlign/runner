from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable, Mapping, Sequence


SUPPLEMENT_KEYS = (
    "event_id",
    "ra_sd_deg",
    "dec_sd_deg",
    "vg_sd_km_s",
    "convergence_angle_deg",
    "q_au",
    "e",
)
RECURRENT_KEYS = ("id", "year", "sol", "sun_lon", "ecl_lat", "vg")
FORBIDDEN_TRUTH_KEYS = {
    "shower",
    "shower_code",
    "shower_name",
    "iau",
    "iau_code",
    "sporadic",
    "background",
    "label",
    "cluster",
    "target",
    "target_id",
}


@dataclass(frozen=True)
class SupplementalRow:
    event_id: str
    ra_sd_deg: float | None
    dec_sd_deg: float | None
    vg_sd_km_s: float | None
    convergence_angle_deg: float | None
    q_au: float | None
    e: float | None


def _nullable_finite(value: Any) -> float | None:
    if value is None or value == "":
        return None
    x = float(value)
    if not math.isfinite(x):
        raise ValueError("supplemental numeric values must be finite or blank")
    return x


def _assert_no_truth_keys(row: Mapping[str, Any]) -> None:
    bad = sorted(k for k in row if k.lower() in FORBIDDEN_TRUTH_KEYS)
    if bad:
        raise ValueError(f"truth-bearing keys are forbidden pretruth: {bad}")


def parse_supplement(
    rows: Sequence[Mapping[str, Any]],
    retained_ids: Iterable[str],
) -> dict[str, SupplementalRow]:
    """Validate the exact retained-ID-only comparator supplement.

    Missing rows and blank comparator-only quantities are allowed. Unknown IDs,
    duplicate IDs, extra columns, truth-bearing keys, and non-finite supplied
    quantities fail closed.
    """
    allow = {str(x) for x in retained_ids}
    if not allow:
        raise ValueError("retained-ID allowlist must be non-empty")
    out: dict[str, SupplementalRow] = {}
    for raw in rows:
        _assert_no_truth_keys(raw)
        if tuple(raw.keys()) != SUPPLEMENT_KEYS:
            raise ValueError(f"supplement header/order must be exactly {SUPPLEMENT_KEYS}")
        eid = str(raw["event_id"])
        if not eid:
            raise ValueError("blank event_id")
        if eid not in allow:
            raise ValueError(f"non-retained/protected/unknown event_id in supplement: {eid}")
        if eid in out:
            raise ValueError(f"duplicate supplement event_id: {eid}")
        out[eid] = SupplementalRow(
            event_id=eid,
            ra_sd_deg=_nullable_finite(raw["ra_sd_deg"]),
            dec_sd_deg=_nullable_finite(raw["dec_sd_deg"]),
            vg_sd_km_s=_nullable_finite(raw["vg_sd_km_s"]),
            convergence_angle_deg=_nullable_finite(raw["convergence_angle_deg"]),
            q_au=_nullable_finite(raw["q_au"]),
            e=_nullable_finite(raw["e"]),
        )
    return out


def _finite_base_vg(base: Mapping[str, Any]) -> float:
    _assert_no_truth_keys(base)
    vg = float(base["vg"])
    if not math.isfinite(vg) or vg <= 0.0:
        raise ValueError("base recurrent geometry must contain finite positive vg")
    return vg


def sugar_eligible(base: Mapping[str, Any], sup: SupplementalRow | None) -> bool:
    vg = _finite_base_vg(base)
    if sup is None:
        return False
    vals = (sup.ra_sd_deg, sup.dec_sd_deg, sup.vg_sd_km_s, sup.convergence_angle_deg)
    if any(v is None for v in vals):
        return False
    assert sup.ra_sd_deg is not None and sup.dec_sd_deg is not None
    assert sup.vg_sd_km_s is not None and sup.convergence_angle_deg is not None
    return bool(
        sup.ra_sd_deg >= 0.0
        and sup.dec_sd_deg >= 0.0
        and sup.vg_sd_km_s >= 0.0
        and sup.convergence_angle_deg > 15.0
        and sup.vg_sd_km_s <= 0.10 * vg + 1.0
    )


def catalogue_hdbscan_eligible(base: Mapping[str, Any], sup: SupplementalRow | None) -> bool:
    vg = _finite_base_vg(base)
    if sup is None:
        return False
    vals = (sup.convergence_angle_deg, sup.vg_sd_km_s, sup.q_au, sup.e)
    if any(v is None for v in vals):
        return False
    assert sup.convergence_angle_deg is not None and sup.vg_sd_km_s is not None
    assert sup.q_au is not None and sup.e is not None
    return bool(
        sup.convergence_angle_deg >= 15.0
        and sup.vg_sd_km_s / vg <= 0.10
        and 0.0 <= sup.e <= 1.0
        and 0.0 < sup.q_au <= 1.0
    )


def recurrent_projection(base: Mapping[str, Any]) -> dict[str, Any]:
    """Return the only row shape recurrent-EOM is allowed to receive."""
    _assert_no_truth_keys(base)
    missing = [k for k in RECURRENT_KEYS if k not in base]
    if missing:
        raise ValueError(f"base canonical geometry missing recurrent keys: {missing}")
    projected = {k: base[k] for k in RECURRENT_KEYS}
    if tuple(projected.keys()) != RECURRENT_KEYS:
        raise RuntimeError("recurrent projection schema drift")
    forbidden = set(SUPPLEMENT_KEYS[1:]) & set(projected)
    if forbidden:
        raise RuntimeError(f"comparator-only values leaked into recurrent projection: {sorted(forbidden)}")
    return projected


def pairwise_universe(
    base_rows: Sequence[Mapping[str, Any]],
    supplement: Mapping[str, SupplementalRow],
    comparator: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Create a same-row recurrent-EOM universe for one frozen comparator.

    Returns only recurrent geometry rows plus the selected stable IDs. Comparator
    fields are consulted for eligibility and then discarded rather than carried
    into the recurrent method.
    """
    if comparator not in {"sugar", "catalogue_hdbscan"}:
        raise ValueError("unsupported frozen comparator")
    out: list[dict[str, Any]] = []
    ids: list[str] = []
    seen: set[str] = set()
    for base in base_rows:
        _assert_no_truth_keys(base)
        eid = str(base["id"])
        if eid in seen:
            raise ValueError(f"duplicate base event ID: {eid}")
        seen.add(eid)
        sup = supplement.get(eid)
        keep = sugar_eligible(base, sup) if comparator == "sugar" else catalogue_hdbscan_eligible(base, sup)
        if keep:
            projected = recurrent_projection(base)
            if str(projected["id"]) != eid:
                raise RuntimeError("projection changed event identity")
            out.append(projected)
            ids.append(eid)
    return out, ids
