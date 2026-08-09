from __future__ import annotations

import re
from typing import Any

SUPPORT_INELIGIBLE_RE = re.compile(r"^family ([A-Za-z0-9_.:-]+) year ([0-9]{4}) has only ([0-9]+) events in local window$")
EPISODE_SIZE = 128


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def score_and_complete_rank(
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
    runtime: Any,
    base: Any,
    multiplicity_module: Any,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    """Delegate every defined family score to immutable v8 and fail-closed-complete its order.

    The only caught exception is immutable v8's insufficient-local-window condition.
    No score is synthesized for such a family; it is appended after all scored
    families by stable family_id.
    """
    require(int(multiplicity_module.EPISODE_SIZE) == EPISODE_SIZE, "P14 episode size changed")
    family_ids = [str(f["family_id"]) for f in families]
    require(len(family_ids) == len(set(family_ids)), "P14 duplicate family ID")

    scored_rows: list[dict[str, Any]] = []
    unscorable: list[dict[str, Any]] = []
    for family in families:
        fid = str(family["family_id"])
        try:
            rows, summary = multiplicity_module.score_families([family], scan_by_year, runtime, base)
        except RuntimeError as exc:
            match = SUPPORT_INELIGIBLE_RE.fullmatch(str(exc))
            if match is None:
                raise
            require(match.group(1) == fid, "P14 insufficient-support exception family mismatch")
            available = int(match.group(3))
            require(available < EPISODE_SIZE, "P14 caught non-insufficient support exception")
            unscorable.append({
                "family_id": fid,
                "year": int(match.group(2)),
                "available_local_events": available,
                "required_episode_events": EPISODE_SIZE,
                "exact_exception": str(exc),
            })
            continue
        require(len(rows) == 1, f"P14 exact v8 scorer returned {len(rows)} rows for {fid}")
        require(int(summary["families_requested"]) == 1 and int(summary["families_scored"]) == 1, "P14 exact scorer accounting changed")
        require(summary["episode_sizes"] == [EPISODE_SIZE], "P14 exact scorer episode size changed")
        scored_rows.append(rows[0])

    scored_order = list(map(str, multiplicity_module.rank_scored(scored_rows, "multiplicity")))
    scored_ids = {str(row["family_id"]) for row in scored_rows}
    unscorable_ids = sorted(str(row["family_id"]) for row in unscorable)
    require(set(scored_order) == scored_ids and len(scored_order) == len(scored_ids), "P14 scored ranking universe changed")
    require(not (scored_ids & set(unscorable_ids)), "P14 family both scored and unscorable")
    full_order = scored_order + unscorable_ids
    require(set(full_order) == set(family_ids) and len(full_order) == len(family_ids), "P14 completed ranking universe mismatch")
    if unscorable_ids:
        boundary = len(scored_order)
        require(all(fid in scored_ids for fid in full_order[:boundary]), "P14 unscorable family outranked scored family")
        require(full_order[boundary:] == unscorable_ids, "P14 unscorable tie order changed")

    return scored_rows, full_order, {
        "families_requested": len(families),
        "families_scored": len(scored_rows),
        "families_unscorable": len(unscorable),
        "episode_size": EPISODE_SIZE,
        "scored_family_ids": scored_order,
        "unscorable_families": unscorable,
        "unscorable_order_rule": "after all scored families; lexicographic stable family_id",
        "fabricated_scores": False,
        "episode_size_relaxed": False,
    }
