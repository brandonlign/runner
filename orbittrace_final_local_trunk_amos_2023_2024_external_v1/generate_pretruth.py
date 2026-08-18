#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

YEARS = (2023, 2024)
BLIND = (20.0, 55.0)
SCIENTIFIC_ROLE = "PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY"
SELECTED_FINAL_METHOD = "recurrent_local_topomodal_trunk_v1_over_density_sync_parent"

# Exact pre-data source identities. The parent AMOS generator is the fully
# audited density-synchronous endpoint from PR #1268. The local-trunk sources
# are the exact GMN scientific constructor plus the validated no-edge-pruning
# transport used by the active binding experiment.
PARENT_AMOS_GENERATOR_BLOB = "b76d7c53ab238cd45f12027947f2098a770ba7b6"
LOCAL_TRUNK_PROTOCOL_BLOB = "de8d040a1f9d3b0825ce56532efd5950acefc689"
LOCAL_TRUNK_CONSTRUCTOR_BLOB = "cd3fb15263fd4b2e38e4b413ece9b347b64816d5"
LOCAL_TRUNK_LAZY_TRANSPORT_BLOB = "79cc2e51929fd60f8e17faec4c1b04c19e43010e"
LOCAL_TRUNK_EXACT_ROW_TRANSPORT_BLOB = "81e4833ac24bb90fe810b0444da534906b10e798"
LOCAL_TRUNK_SOURCE_COMMIT = "3afb4bd1de98d9c765dcaff79b9e98a0cc1234a4"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def membership_sha(ids: list[str] | tuple[str, ...]) -> str:
    return hashlib.sha256("|".join(sorted(str(x) for x in ids)).encode()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    payload = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(payload.encode()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_local_trunk(local_dir: Path) -> tuple[Any, Any]:
    protocol = local_dir / "PROTOCOL.md"
    constructor = local_dir / "build_prelabel.py"
    lazy = local_dir / "technical_lazy_local_trunk.py"
    exact = local_dir / "technical_exact_full_row_transport.py"

    req(git_blob_sha(protocol) == LOCAL_TRUNK_PROTOCOL_BLOB, "local-trunk protocol source changed")
    req(git_blob_sha(constructor) == LOCAL_TRUNK_CONSTRUCTOR_BLOB, "local-trunk constructor source changed")
    req(git_blob_sha(lazy) == LOCAL_TRUNK_LAZY_TRANSPORT_BLOB, "local-trunk lazy transport source changed")
    req(git_blob_sha(exact) == LOCAL_TRUNK_EXACT_ROW_TRANSPORT_BLOB, "local-trunk exact-row transport source changed")

    # The frozen modules use these historical import names. Load the exact
    # pinned files explicitly so no ambient PYTHONPATH module can substitute.
    frozen = load_module(constructor, "build_prelabel")
    sys.modules["build_prelabel"] = frozen
    lazy_mod = load_module(lazy, "technical_lazy_local_trunk")
    sys.modules["technical_lazy_local_trunk"] = lazy_mod
    exact_mod = load_module(exact, "technical_exact_full_row_transport")

    # The only survey transfer in the local rule is the two annual identities.
    # Every physical/topological constant and selection rule remains byte-pinned.
    frozen.YEARS = YEARS
    return frozen, exact_mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical-2023", type=Path, required=True)
    ap.add_argument("--canonical-2024", type=Path, required=True)
    ap.add_argument("--parent-generator", type=Path, required=True)
    ap.add_argument("--local-trunk-source-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(git_blob_sha(a.parent_generator) == PARENT_AMOS_GENERATOR_BLOB, "audited parent AMOS generator changed")

    # First generate the exact already-audited density-synchronous AMOS pretruth.
    # This subprocess receives geometry-only canonical inputs; it has no label path.
    parent_out = a.output / "density_sync_parent"
    parent_out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(a.parent_generator),
            "--canonical-2023",
            str(a.canonical_2023),
            "--canonical-2024",
            str(a.canonical_2024),
            "--output",
            str(parent_out),
        ],
        check=True,
    )
    parent_path = parent_out / "FINAL_DENSITY_SYNC_AMOS_2023_2024_PRETRUTH.json"
    req(parent_path.exists(), "parent AMOS pretruth missing")
    parent = json.loads(parent_path.read_text(encoding="utf-8"))

    req(parent["scientific_role"] == SCIENTIFIC_ROLE, "parent AMOS scientific role changed")
    req(parent["phase"] == "PRETRUTH_FROZEN", "parent AMOS phase changed")
    req(parent["years"] == list(YEARS), "parent AMOS years changed")
    req(parent["blind_exclusion"] == list(BLIND), "parent AMOS blind exclusion changed")
    req(parent["selected_final_method"] == "density_synchronous_recurrent_eom_hdbscan_v1_pr1263", "wrong parent method")
    req(parent["labels_accessed"] is False and parent["amos_shower_associations_accessed"] is False, "parent AMOS pretruth reports label access")
    for key in (
        "target_information_access",
        "target_region_events_accessed",
        "orbittrace_target_access",
        "sonotaco_access",
        "asfn_access",
        "efn_access",
        "maarsy_scientific_access",
        "dms_scientific_access",
        "amos_post_result_parameter_search",
    ):
        req(parent[key] is False, f"parent firewall failed: {key}")

    # Reuse the exact parent canonical loader to obtain the same geometry rows
    # that entered the parent hierarchy, then apply the exact local-trunk rule.
    parent_mod = load_module(a.parent_generator, "pinned_density_sync_amos_generator")
    by_year = {
        2023: parent_mod.load_canonical(a.canonical_2023, 2023),
        2024: parent_mod.load_canonical(a.canonical_2024, 2024),
    }
    events = by_year[2023] + by_year[2024]
    event_by_id = {str(row["id"]): row for row in events}
    req(len(event_by_id) == len(events), "duplicate canonical event ID")
    req(len(events) == int(parent["events_total"]), "canonical event count diverged from parent pretruth")
    req({str(y): len(by_year[y]) for y in YEARS} == parent["events_by_year"], "canonical annual counts diverged")
    req(all(not (BLIND[0] <= float(row["sol"]) <= BLIND[1]) for row in events), "protected row reached local trunk")

    frozen, exact = load_local_trunk(a.local_trunk_source_dir)
    req(tuple(frozen.YEARS) == YEARS, "local-trunk annual transfer failed")
    req(float(frozen.RADIUS) == 1.0, "local-trunk radius changed")
    req(int(frozen.MIN_ANNUAL_SUPPORT) == 4, "local-trunk annual support changed")

    parents = list(parent["density_sync_candidates"])
    req(len(parents) > 0, "density-sync parent catalogue empty")

    successor: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    final_seen: set[str] = set()
    changed = 0
    for rank, parent_row in enumerate(parents, 1):
        parent_ids = [str(x) for x in parent_row["event_ids"]]
        req(parent_ids == sorted(parent_ids), f"parent membership not sorted at rank {rank}")
        req(set(parent_ids).issubset(event_by_id), f"parent event outside retained geometry at rank {rank}")
        final_ids, topo = exact.local_trunk_exact_full_row(parent_ids, event_by_id)
        req(final_ids == sorted(final_ids), f"local-trunk output not sorted at rank {rank}")
        req(set(final_ids).issubset(parent_ids), f"local-trunk escaped same-rank parent at rank {rank}")
        req(final_seen.isdisjoint(final_ids), f"local-trunk final slots overlap at rank {rank}")
        final_seen.update(final_ids)
        changed_here = final_ids != parent_ids
        changed += int(changed_here)

        successor.append(
            {
                "rank": rank,
                "parent_family_id": str(parent_row["family_id"]),
                "family_id": str(parent_row["family_id"]),
                "parent_node_id": int(parent_row["node_id"]),
                "event_ids": final_ids,
                "member_count": len(final_ids),
                "representation_changed": changed_here,
            }
        )
        diagnostics.append(
            {
                "rank": rank,
                "parent_family_id": str(parent_row["family_id"]),
                "parent_node_id": int(parent_row["node_id"]),
                "parent_membership_sha256": membership_sha(parent_ids),
                "parent_member_count": len(parent_ids),
                "topology": topo,
                "final_membership_sha256": membership_sha(final_ids),
                "final_member_count": len(final_ids),
                "representation_changed": changed_here,
            }
        )

    req(len(successor) == len(parents), "final catalogue slot count changed")
    req([int(row["rank"]) for row in successor] == list(range(1, len(parents) + 1)), "final slot order changed")
    req([str(row["family_id"]) for row in successor] == [str(row["family_id"]) for row in parents], "final family/rank identity changed")

    payload = dict(parent)
    payload.update(
        {
            "schema": "ORBITTRACE_FINAL_LOCAL_TRUNK_AMOS_2023_2024_PRETRUTH",
            "scientific_role": SCIENTIFIC_ROLE,
            "phase": "PRETRUTH_FROZEN",
            "selected_final_method": SELECTED_FINAL_METHOD,
            "density_sync_parent_pretruth_sha256": file_sha(parent_path),
            "density_sync_parent_candidates": parents,
            "local_trunk_candidates": successor,
            "local_trunk_diagnostics": diagnostics,
            "local_trunk_changed_slot_count": changed,
            "local_trunk_mechanism_active": bool(changed > 0),
            "local_trunk_parent_ordered_membership_sha256": ordered_membership_sha(parents),
            "local_trunk_final_ordered_membership_sha256": ordered_membership_sha(successor),
            "local_trunk_source_commit": LOCAL_TRUNK_SOURCE_COMMIT,
            "local_trunk_source_pins": {
                "protocol_git_blob": LOCAL_TRUNK_PROTOCOL_BLOB,
                "constructor_git_blob": LOCAL_TRUNK_CONSTRUCTOR_BLOB,
                "lazy_transport_git_blob": LOCAL_TRUNK_LAZY_TRANSPORT_BLOB,
                "exact_full_row_transport_git_blob": LOCAL_TRUNK_EXACT_ROW_TRANSPORT_BLOB,
            },
            "local_trunk_transfer": {
                "years": list(YEARS),
                "radius": float(frozen.RADIUS),
                "min_annual_support": int(frozen.MIN_ANNUAL_SUPPORT),
                "h_sol": float(frozen.H_SOL),
                "h_rad": float(frozen.H_RAD),
                "h_logv": float(frozen.H_LOGV),
                "rank_order_preserved_from_density_sync_parent": True,
                "same_rank_parent_subset_only": True,
                "post_result_parameter_search": False,
            },
            "labels_accessed": False,
            "amos_shower_associations_accessed": False,
            "amos_orbit_elements_accessed": False,
            "target_information_access": False,
            "target_region_events_accessed": False,
            "orbittrace_target_access": False,
            "sonotaco_access": False,
            "asfn_access": False,
            "efn_access": False,
            "maarsy_scientific_access": False,
            "dms_scientific_access": False,
            "amos_post_result_parameter_search": False,
            "new_external_survey_hunt": False,
        }
    )

    out = a.output / "FINAL_LOCAL_TRUNK_AMOS_2023_2024_PRETRUTH.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    digest = file_sha(out)
    (a.output / "PRETRUTH_SHA256.txt").write_text(digest + "\n", encoding="ascii")
    print(
        json.dumps(
            {
                "verdict": "PASS_FINAL_LOCAL_TRUNK_AMOS_PRETRUTH_FREEZE",
                "pretruth_sha256": digest,
                "events": payload["events_by_year"],
                "ordinary_candidates": len(payload["ordinary_candidates"]),
                "recurrent_candidates": len(payload["recurrent_candidates"]),
                "density_sync_candidates": len(parents),
                "local_trunk_candidates": len(successor),
                "local_trunk_changed_slots": changed,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
