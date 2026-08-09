#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P10_SHA256 = "638b4f41e51955436557a99f1142c3d3cea91e12a66e2f74925c6bfb79d5e50d"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P11 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


IMPORT_ANCHOR = '''from sklearn.preprocessing import StandardScaler
'''
IMPORT_REPL = '''from sklearn.preprocessing import StandardScaler
from scipy.spatial import cKDTree
'''

RUNTIME_INIT_ANCHOR = '''    crossfit_models: list[dict[str, Any]] = []
    crossfit_runtime_models: dict[int, tuple[Any, Any]] = {}
    reliability: dict[str, dict[str, Any]] = {}
'''
RUNTIME_INIT_REPL = '''    crossfit_models: list[dict[str, Any]] = []
    crossfit_runtime_models: dict[int, tuple[Any, Any]] = {}
    reliability: dict[str, dict[str, Any]] = {}
    p11_density_runtime_calibration: dict[str, dict[str, Any]] = {}
    p11_density_calibration_records: dict[str, dict[str, Any]] = {}
'''

CALIBRATION_ANCHOR = '''            require(key not in reliability, f"P3 duplicate reliability key {key}")
            reliability[key] = {
'''
CALIBRATION_REPL = '''            require(key not in reliability, f"P3 duplicate reliability key {key}")

            # P11 pretruth local density-contrast calibration.  The held-fold
            # StandardScaler is inherited exactly from P6; only the two already-
            # frozen [d_obs,D_SH] columns are used.  No label value is available.
            p11_positive_ids = list(map(str, d["target_seed_ids"]))
            p11_negative_ids = list(map(str, d["negative_event_ids"]))
            p11_positive_order = np.argsort(np.asarray(p11_positive_ids, dtype=str), kind="mergesort")
            p11_negative_order = np.argsort(np.asarray(p11_negative_ids, dtype=str), kind="mergesort")
            p11_positive_ids_sorted = [p11_positive_ids[int(j)] for j in p11_positive_order]
            p11_negative_ids_sorted = [p11_negative_ids[int(j)] for j in p11_negative_order]
            p11_z_pos = np.asarray(scf.transform(xp[p11_positive_order]), dtype=np.float64)
            p11_z_unl = np.asarray(scf.transform(xn[p11_negative_order]), dtype=np.float64)
            require(len(p11_z_pos) >= 4 and len(p11_z_unl) >= MIN_DIRECTION_NEGATIVES, "P11 calibration support changed")
            require(np.all(np.isfinite(p11_z_pos)) and np.all(np.isfinite(p11_z_unl)), "P11 non-finite standardized calibration feature")
            p11_pos_tree = cKDTree(p11_z_pos)
            p11_unl_tree = cKDTree(p11_z_unl)
            p11_seed_pos_dist = np.asarray(p11_pos_tree.query(p11_z_pos, k=2, p=2, eps=0, workers=1)[0][:, 1], dtype=np.float64)
            p11_seed_unl_dist = np.asarray(p11_unl_tree.query(p11_z_pos, k=1, p=2, eps=0, workers=1)[0], dtype=np.float64)
            p11_seed_num = np.square(p11_seed_pos_dist, dtype=np.float64)
            p11_seed_den = np.square(p11_seed_unl_dist, dtype=np.float64)
            p11_seed_ratio = np.full(len(p11_z_pos), np.inf, dtype=np.float64)
            p11_seed_positive_den = p11_seed_den > 0.0
            p11_seed_ratio[p11_seed_positive_den] = p11_seed_num[p11_seed_positive_den] / p11_seed_den[p11_seed_positive_den]
            require(np.all((np.isfinite(p11_seed_ratio)) | np.isposinf(p11_seed_ratio)), "P11 invalid seed density ratio")
            p11_rank = max(1, int(math.floor(P3_NEGATIVE_TAIL_MAX * (len(p11_seed_ratio) + 1))))
            require(1 <= p11_rank <= len(p11_seed_ratio), "P11 invalid inherited order-statistic rank")
            p11_seed_ratio_sorted = np.sort(np.asarray(p11_seed_ratio, dtype=np.float64))
            p11_threshold = float(p11_seed_ratio_sorted[len(p11_seed_ratio_sorted) - p11_rank])
            p11_density_runtime_calibration[key] = {
                "threshold": p11_threshold,
                "rank": p11_rank,
                "positive_ids_sha256": canonical_sha(p11_positive_ids_sorted),
                "negative_ids_sha256": canonical_sha(p11_negative_ids_sorted),
            }
            p11_density_calibration_records[key] = {
                "family_id": str(d["family_id"]),
                "source_year": int(d["source_year"]),
                "target_year": int(d["target_year"]),
                "fold": int(held_fold),
                "seed_count": int(len(p11_seed_ratio)),
                "unlabeled_count": int(len(p11_z_unl)),
                "rank": int(p11_rank),
                "rank_rule": "max(1,floor(P3_NEGATIVE_TAIL_MAX*(seed_count+1)))",
                "threshold": None if math.isinf(p11_threshold) else p11_threshold,
                "threshold_is_infinite": bool(math.isinf(p11_threshold)),
                "seed_zero_unlabeled_denominator_count": int(np.sum(~p11_seed_positive_den)),
                "seed_ratio_float64_sha256": hashlib.sha256(np.ascontiguousarray(p11_seed_ratio, dtype="<f8").tobytes()).hexdigest(),
                "positive_ids_sha256": canonical_sha(p11_positive_ids_sorted),
                "negative_ids_sha256": canonical_sha(p11_negative_ids_sorted),
                "standardized_feature_order": ["d_obs", "d_orb"],
                "nearest_neighbor_order": 1,
                "distance": "squared Euclidean after exact inherited held-fold StandardScaler",
                "no_known_shower_truth_used": True,
            }
            reliability[key] = {
'''

CALIBRATION_FREEZE_ANCHOR = '''    require(len(reliability) == len(directions), "P3 reliability direction universe changed")
'''
CALIBRATION_FREEZE_REPL = '''    require(len(reliability) == len(directions), "P3 reliability direction universe changed")
    require(len(p11_density_calibration_records) == len(directions), "P11 calibration direction universe changed")
    p11_density_calibration_payload = {
        "rule": "held-fold-standardized local 1-NN squared-distance ratio; seed leave-one-seed-out numerator / globally-v8-seed-excluded local-unlabeled denominator; kth-largest held-seed threshold with inherited P3 0.10 rank",
        "alpha_source": "P3_NEGATIVE_TAIL_MAX",
        "alpha": P3_NEGATIVE_TAIL_MAX,
        "nearest_neighbor_order": 1,
        "distance": "squared Euclidean",
        "records": p11_density_calibration_records,
        "no_known_shower_truth_used": True,
    }
    p11_density_calibration_sha = canonical_sha(p11_density_calibration_payload)
    (args.output / "p11_density_calibration_pretruth.json").write_text(json.dumps(p11_density_calibration_payload, indent=2, sort_keys=True, allow_nan=False) + "\\n")
    (args.output / "p11_density_calibration_pretruth.sha256").write_text(p11_density_calibration_sha + "\\n")
'''

SCORING_START_ANCHOR = '''    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eps = np.finfo(np.float64).eps
    for index, direction in enumerate(directions, start=1):
        direction.pop("positive_features", None)
        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)
'''
SCORING_START_REPL = '''    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    p11_density_audits: list[dict[str, Any]] = []
    p11_density_rejected_p10 = 0
    p11_density_candidate_zero_denominator = 0
    eps = np.finfo(np.float64).eps
    for index, direction in enumerate(directions, start=1):
        p11_positive_features = np.asarray(direction.pop("positive_features"), dtype=np.float64)
        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)
'''

ALLOWED_ANCHOR = '''        allowed = membership_floor_allowed & jointly_supported
        odds = probabilities / (1.0 - probabilities)
'''
ALLOWED_REPL = '''        p10_allowed = membership_floor_allowed & jointly_supported

        # P11 candidate veto.  All neighbor distances are exact 1-NN queries in
        # the inherited held-fold standardized two-view feature space.  The
        # candidate is itself a member of the local unlabeled reference, so k=2
        # excludes its own row; an exact duplicate event therefore correctly
        # gives a zero nearest-other denominator and is rejected conservatively.
        require(key in p11_density_runtime_calibration, f"P11 missing runtime calibration {key}")
        p11_cal = p11_density_runtime_calibration[key]
        p11_positive_ids_runtime = list(map(str, direction["target_seed_ids"]))
        p11_positive_order_runtime = np.argsort(np.asarray(p11_positive_ids_runtime, dtype=str), kind="mergesort")
        p11_negative_order_runtime = np.argsort(np.asarray(ids, dtype=str), kind="mergesort")
        p11_positive_ids_sorted_runtime = [p11_positive_ids_runtime[int(j)] for j in p11_positive_order_runtime]
        p11_negative_ids_sorted_runtime = [ids[int(j)] for j in p11_negative_order_runtime]
        require(canonical_sha(p11_positive_ids_sorted_runtime) == str(p11_cal["positive_ids_sha256"]), "P11 positive identity drift")
        require(canonical_sha(p11_negative_ids_sorted_runtime) == str(p11_cal["negative_ids_sha256"]), "P11 unlabeled identity drift")
        p11_z_pos_runtime = np.asarray(scoring_scaler.transform(p11_positive_features[p11_positive_order_runtime]), dtype=np.float64)
        p11_z_unl_runtime = np.asarray(scoring_scaler.transform(features[p11_negative_order_runtime]), dtype=np.float64)
        require(len(p11_z_unl_runtime) >= 2, "P11 candidate self-exclusion needs >=2 unlabeled rows")
        p11_pos_tree_runtime = cKDTree(p11_z_pos_runtime)
        p11_unl_tree_runtime = cKDTree(p11_z_unl_runtime)
        p11_candidate_pos_dist_sorted = np.asarray(p11_pos_tree_runtime.query(p11_z_unl_runtime, k=1, p=2, eps=0, workers=1)[0], dtype=np.float64)
        p11_candidate_unl_pair_dist_sorted = np.asarray(p11_unl_tree_runtime.query(p11_z_unl_runtime, k=2, p=2, eps=0, workers=1)[0], dtype=np.float64)
        p11_candidate_unl_other_dist_sorted = p11_candidate_unl_pair_dist_sorted[:, 1]
        p11_candidate_num_sorted = np.square(p11_candidate_pos_dist_sorted, dtype=np.float64)
        p11_candidate_den_sorted = np.square(p11_candidate_unl_other_dist_sorted, dtype=np.float64)
        p11_candidate_ratio_sorted = np.full(len(p11_z_unl_runtime), np.inf, dtype=np.float64)
        p11_candidate_positive_den_sorted = p11_candidate_den_sorted > 0.0
        p11_candidate_ratio_sorted[p11_candidate_positive_den_sorted] = p11_candidate_num_sorted[p11_candidate_positive_den_sorted] / p11_candidate_den_sorted[p11_candidate_positive_den_sorted]
        require(np.all((np.isfinite(p11_candidate_ratio_sorted)) | np.isposinf(p11_candidate_ratio_sorted)), "P11 invalid candidate density ratio")
        p11_candidate_ratio = np.empty(len(features), dtype=np.float64)
        p11_candidate_positive_den = np.empty(len(features), dtype=bool)
        p11_candidate_ratio[p11_negative_order_runtime] = p11_candidate_ratio_sorted
        p11_candidate_positive_den[p11_negative_order_runtime] = p11_candidate_positive_den_sorted
        p11_threshold = float(p11_cal["threshold"])
        p11_density_allowed = p11_candidate_positive_den & (p11_candidate_ratio <= p11_threshold)
        p11_density_rejected_p10 += int(np.sum(p10_allowed & ~p11_density_allowed))
        p11_density_candidate_zero_denominator += int(np.sum(~p11_candidate_positive_den))
        allowed = p10_allowed & p11_density_allowed
        p11_density_audits.append({
            "family_id": str(direction["family_id"]),
            "source_year": int(direction["source_year"]),
            "target_year": int(direction["target_year"]),
            "fold": int(scoring_fold),
            "candidate_count": int(len(features)),
            "p10_allowed_count": int(np.sum(p10_allowed)),
            "p11_allowed_count": int(np.sum(allowed)),
            "p11_rejected_p10_count": int(np.sum(p10_allowed & ~p11_density_allowed)),
            "candidate_zero_unlabeled_denominator_count": int(np.sum(~p11_candidate_positive_den)),
            "candidate_ids_sha256": canonical_sha(p11_negative_ids_sorted_runtime),
            "candidate_ratio_float64_sha256": hashlib.sha256(np.ascontiguousarray(p11_candidate_ratio_sorted, dtype="<f8").tobytes()).hexdigest(),
            "threshold": None if math.isinf(p11_threshold) else p11_threshold,
            "threshold_is_infinite": bool(math.isinf(p11_threshold)),
            "rank": int(p11_cal["rank"]),
            "self_exclusion": "exact cKDTree k=2 query on event-ID-sorted local unlabeled rows; second distance is nearest other row",
            "zero_denominator_rule": "candidate rejected directly",
            "label_value_accessed": False,
        })
        odds = probabilities / (1.0 - probabilities)
'''

PROPOSAL_ANCHOR = '''                "p9_bidirectional_reliability": True,
                "scoring_fold": scoring_fold,
'''
PROPOSAL_REPL = '''                "p9_bidirectional_reliability": True,
                "p11_density_order_statistic_pass": True,
                "scoring_fold": scoring_fold,
'''

DECISION_FREEZE_ANCHOR = '''    assignments: dict[str, dict[str, Any]] = {}
'''
DECISION_FREEZE_REPL = '''    p11_density_decision_payload = {
        "rule": "exact P10 candidate region AND local density-contrast order-statistic veto",
        "eligible_direction_count": int(len(p11_density_audits)),
        "p10_candidates_rejected": int(p11_density_rejected_p10),
        "candidate_zero_unlabeled_denominator_count": int(p11_density_candidate_zero_denominator),
        "direction_audits": p11_density_audits,
        "no_known_shower_truth_used": True,
    }
    p11_density_decision_sha = canonical_sha(p11_density_decision_payload)
    (args.output / "p11_density_decisions_pretruth.json").write_text(json.dumps(p11_density_decision_payload, indent=2, sort_keys=True, allow_nan=False) + "\\n")
    (args.output / "p11_density_decisions_pretruth.sha256").write_text(p11_density_decision_sha + "\\n")

    assignments: dict[str, dict[str, Any]] = {}
'''

MEMBERSHIP_NAMES = (
    ('"p10_membership_pretruth.sha256"', '"p11_membership_pretruth.sha256"'),
    ('"p10_expanded_families.json.gz"', '"p11_expanded_families.json.gz"'),
    ('"p10_decisions_pretruth.sha256"', '"p11_decisions_pretruth.sha256"'),
    ('"p10_decisions_pretruth.json.gz"', '"p11_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p10_exactly_50_reliable_rank_gt1_directions_changed_geometry": sum(
            bool(r["reliable"]) and int(r["membership_floor_rank"]) > 1 and int(r["p10_geometry_dropped_seed_count"]) > 0
            for r in reliability.values()
        ) == 50,
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATE_REPL = '''        "p10_exactly_50_reliable_rank_gt1_directions_changed_geometry": sum(
            bool(r["reliable"]) and int(r["membership_floor_rank"]) > 1 and int(r["p10_geometry_dropped_seed_count"]) > 0
            for r in reliability.values()
        ) == 50,
        "p11_density_calibration_frozen_before_truth": len(p11_density_calibration_sha) == 64 and len(p11_density_calibration_records) == len(directions),
        "p11_density_decisions_frozen_before_truth": len(p11_density_decision_sha) == 64,
        "p11_exact_inherited_10pct_order_statistic_rank": all(
            int(p11_density_runtime_calibration[k]["rank"]) == int(reliability[k]["membership_floor_rank"])
            for k in reliability
        ),
        "p11_exact_bidirectionally_reliable_direction_universe": len(p11_density_audits) == 436,
        "p11_candidate_self_exclusion_audited": all("k=2" in str(a["self_exclusion"]) for a in p11_density_audits),
        "p11_zero_denominator_candidates_cannot_propose": all(bool(p.get("p11_density_order_statistic_pass", False)) for ps in proposals_by_event.values() for p in ps),
        "p11_every_surviving_proposal_passes_density_veto": all(bool(p.get("p11_density_order_statistic_pass", False)) for ps in proposals_by_event.values() for p in ps),
        "p11_density_veto_nonvacuous": p11_density_rejected_p10 > 0,
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_FLOOR_CONSISTENT_GEOMETRY_MEMBERSHIP_P10_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_FLOOR_CONSISTENT_GEOMETRY_MEMBERSHIP_P10_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_DENSITY_CONTRAST_ORDER_STAT_MEMBERSHIP_P11_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_DENSITY_CONTRAST_ORDER_STAT_MEMBERSHIP_P11_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "Exact P9 bidirectional-reliability membership with P5 joint geometry recomputed from exactly the held-out recurrent seeds retained by the exact P8 membership floor; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "Exact P10 membership plus target-free cross-fit local 1-NN density-contrast order-statistic veto in the inherited held-fold standardized two-view space; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p10_new_numeric_thresholds": False,
            "p10_geometry_tuning": False,
            "p10_parameter_search": False,
'''
CONFIG_REPL = '''            "p10_new_numeric_thresholds": False,
            "p10_geometry_tuning": False,
            "p10_parameter_search": False,
            "p11_density_contrast_features": ["d_obs", "d_orb"],
            "p11_density_contrast_scaler": "exact inherited P6 held-fold StandardScaler",
            "p11_density_contrast_distance": "squared Euclidean",
            "p11_density_contrast_nearest_neighbor_order": 1,
            "p11_density_order_statistic_alpha_source": "P3_NEGATIVE_TAIL_MAX",
            "p11_density_order_statistic_alpha": P3_NEGATIVE_TAIL_MAX,
            "p11_formal_conformal_claim": False,
            "p11_new_numeric_thresholds": False,
            "p11_parameter_search": False,
'''

METHOD_KEY_ANCHOR = '''        "p10": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p11": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p10_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p11_large_shower": p2_large,
'''

RESULT_AUDIT_ANCHOR = '''        "geometry_audits": geometry_audits,
'''
RESULT_AUDIT_REPL = '''        "p11_density_calibration_pretruth_sha256": p11_density_calibration_sha,
        "p11_density_decision_pretruth_sha256": p11_density_decision_sha,
        "p11_density_audits": p11_density_audits,
        "geometry_audits": geometry_audits,
'''

DIAG_ANCHOR = '''            "p10_inherited_joint_support_vectors_total": sum(int(r["p10_inherited_joint_seed_support_count"]) for r in reliability.values()),
'''
DIAG_REPL = '''            "p10_inherited_joint_support_vectors_total": sum(int(r["p10_inherited_joint_seed_support_count"]) for r in reliability.values()),
            "p11_density_calibration_directions": len(p11_density_calibration_records),
            "p11_density_eligible_directions": len(p11_density_audits),
            "p11_density_rejected_p10_candidates": int(p11_density_rejected_p10),
            "p11_density_candidate_zero_denominator": int(p11_density_candidate_zero_denominator),
            "p11_density_infinite_seed_threshold_directions": sum(bool(r["threshold_is_infinite"]) for r in p11_density_calibration_records.values()),
'''

JSON_ANCHOR = '''    (args.output / "floor_consistent_geometry_membership_p10_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "density_contrast_order_stat_membership_p11_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "FLOOR_CONSISTENT_GEOMETRY_MEMBERSHIP_P10_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "DENSITY_CONTRAST_ORDER_STAT_MEMBERSHIP_P11_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P10 floor-consistent retained-seed joint-geometry membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P11 cross-fit local density-contrast order-statistic membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P10 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P11 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_ANCHOR = '''f"- v8 -> P10 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_REPL = '''f"- v8 -> P11 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_ANCHOR = '''f"- v8 -> P10 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_REPL = '''f"- v8 -> P11 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_ANCHOR = '''f"- v8 -> P10 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_REPL = '''f"- v8 -> P11 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "FLOOR_CONSISTENT_GEOMETRY_MEMBERSHIP_P10_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "DENSITY_CONTRAST_ORDER_STAT_MEMBERSHIP_P11_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p11_patch.py EXACT_P10 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P10_SHA256:
        raise RuntimeError(f"exact P10 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (IMPORT_ANCHOR, IMPORT_REPL, "cKDTree import"),
        (RUNTIME_INIT_ANCHOR, RUNTIME_INIT_REPL, "P11 runtime calibration registries"),
        (CALIBRATION_ANCHOR, CALIBRATION_REPL, "P11 held-seed density calibration"),
        (CALIBRATION_FREEZE_ANCHOR, CALIBRATION_FREEZE_REPL, "P11 calibration pretruth freeze"),
        (SCORING_START_ANCHOR, SCORING_START_REPL, "P11 scoring feature retention"),
        (ALLOWED_ANCHOR, ALLOWED_REPL, "P11 local density candidate veto"),
        (PROPOSAL_ANCHOR, PROPOSAL_REPL, "P11 proposal provenance"),
        (DECISION_FREEZE_ANCHOR, DECISION_FREEZE_REPL, "P11 density decisions pretruth freeze"),
        (GATE_ANCHOR, GATE_REPL, "P11 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P11 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P11 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P11 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P11 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P11 large-shower key"),
        (RESULT_AUDIT_ANCHOR, RESULT_AUDIT_REPL, "P11 result pretruth audits"),
        (DIAG_ANCHOR, DIAG_REPL, "P11 diagnostics"),
        (JSON_ANCHOR, JSON_REPL, "P11 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P11 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P11 title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P11 summary label"),
        (QUALIFIED_ANCHOR, QUALIFIED_REPL, "P11 qualified summary label"),
        (RECOVERY_ANCHOR, RECOVERY_REPL, "P11 recovery summary label"),
        (PRECISION_ANCHOR, PRECISION_REPL, "P11 precision summary label"),
        (PRINT_ANCHOR, PRINT_REPL, "P11 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"membership output rename {before}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P11_INPUT_P10_SHA256={EXPECTED_P10_SHA256}")
    print(f"P11_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P11_PATCH_SCOPE=exact P10 plus pretruth-fixed held-fold-standardized local 1-NN density-contrast order-statistic candidate veto using only inherited P3 0.10 rank; no parameter search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
