#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

EXPECTED_P2_SHA256 = "f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb"

CONST_ANCHOR = '''RESPONSIBILITY_THRESHOLD = 0.5
'''
CONST_REPL = '''RESPONSIBILITY_THRESHOLD = 0.5
P4_FOLD_COUNT = 5
P4_LOCAL_FDR_Q = 0.05
P4_PSEUDOCOUNT = 1.0
P4_MIN_SPLIT_SIZE = 64
'''

DIRECTION_ANCHOR = '''            directions.append({
                "family_index": family_index,
                "family_id": family_id,
                "source_year": source_year,
                "target_year": target_year,
                "source_seed_ids": source_ids,
                "target_seed_ids": target_ids,
                "negative_event_ids": negative_ids,
                "negative_features": x_neg,
            })
'''
DIRECTION_REPL = '''            directions.append({
                "family_index": family_index,
                "family_id": family_id,
                "source_year": source_year,
                "target_year": target_year,
                "source_seed_ids": source_ids,
                "target_seed_ids": target_ids,
                "positive_features": x_pos,
                "negative_event_ids": negative_ids,
                "negative_features": x_neg,
            })
'''

HELPER_ANCHOR = '''def main() -> int:
'''
HELPER_REPL = '''def p4_split_indices(family_id: str, source_year: int, target_year: int, event_ids: list[str]) -> tuple[list[int], list[int]]:
    keyed = []
    for index, event_id in enumerate(event_ids):
        payload = f"P4-SPLIT|{family_id}|{source_year}|{target_year}|{event_id}".encode("utf-8")
        keyed.append((hashlib.sha256(payload).digest(), str(event_id), index))
    keyed.sort(key=lambda row: (row[0], row[1]))
    split0 = [int(row[2]) for row in keyed[0::2]]
    split1 = [int(row[2]) for row in keyed[1::2]]
    require(len(split0) >= P4_MIN_SPLIT_SIZE and len(split1) >= P4_MIN_SPLIT_SIZE, "P4 reciprocal split below frozen minimum")
    require(len(split0) + len(split1) == len(event_ids) and not (set(split0) & set(split1)), "P4 reciprocal split integrity failure")
    return split0, split1


def p4_select_threshold(proposal_scores: np.ndarray, calibration_scores: np.ndarray, seed_median: float) -> dict[str, float | int] | None:
    proposal = np.asarray(proposal_scores, dtype=np.float64)
    calibration = np.asarray(calibration_scores, dtype=np.float64)
    require(len(proposal) >= P4_MIN_SPLIT_SIZE and len(calibration) >= P4_MIN_SPLIT_SIZE, "P4 reciprocal calibration support changed")
    require(np.all(np.isfinite(proposal)) and np.all(np.isfinite(calibration)) and math.isfinite(seed_median), "P4 non-finite calibration score")
    valid: list[dict[str, float | int]] = []
    for threshold in sorted(set(float(x) for x in proposal.tolist())):
        if threshold > float(seed_median):
            continue
        R = int(np.sum(proposal >= threshold))
        B = int(np.sum(calibration >= threshold))
        fdrhat = ((P4_PSEUDOCOUNT + B) / len(calibration)) * len(proposal) / max(1, R)
        if fdrhat <= P4_LOCAL_FDR_Q:
            valid.append({"threshold": float(threshold), "R": R, "B": B, "fdrhat": float(fdrhat)})
    if not valid:
        return None
    # Lowest observed proposal score satisfying the frozen local-background bound.
    return min(valid, key=lambda row: float(row["threshold"]))


def main() -> int:
'''

SCIENCE_START = '''    scaler = StandardScaler()
'''
SCIENCE_END = '''    expanded: list[dict[str, Any]] = []
'''
SCIENCE_REPL = '''    family_fold = {
        str(f["family_id"]): int.from_bytes(hashlib.sha256(str(f["family_id"]).encode("utf-8")).digest()[:8], "big") % P4_FOLD_COUNT
        for f in families
    }
    require(len(family_fold) == EXPECTED_FAMILY_COUNT, "P4 family-fold universe changed")
    require(set(family_fold.values()) == set(range(P4_FOLD_COUNT)), "P4 deterministic folds not all populated")

    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    fold_models: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    reliable_directions = 0
    unreliable_directions = 0
    total_surviving_proposals = 0

    for held_fold in range(P4_FOLD_COUNT):
        train_dirs = [d for d in directions if family_fold[str(d["family_id"])] != held_fold]
        held_dirs = [d for d in directions if family_fold[str(d["family_id"])] == held_fold]
        require(train_dirs and held_dirs, f"P4 fold {held_fold} empty train/holdout")
        train_family_ids = sorted({str(d["family_id"]) for d in train_dirs})
        heldout_family_ids = sorted({str(d["family_id"]) for d in held_dirs})
        require(not (set(train_family_ids) & set(heldout_family_ids)), f"P4 fold {held_fold} family leakage")

        x_parts: list[np.ndarray] = []
        y_parts: list[np.ndarray] = []
        w_parts: list[np.ndarray] = []
        for d in train_dirs:
            xp = np.asarray(d["positive_features"], dtype=np.float64)
            xn = np.asarray(d["negative_features"], dtype=np.float64)
            require(len(xp) >= 4 and len(xn) >= MIN_DIRECTION_NEGATIVES, "P4 cross-fit direction support changed")
            x_parts.extend((xp, xn))
            y_parts.extend((np.ones(len(xp), dtype=np.int8), np.zeros(len(xn), dtype=np.int8)))
            w_parts.extend((
                np.full(len(xp), 0.5 / len(xp), dtype=np.float64),
                np.full(len(xn), 0.5 / len(xn), dtype=np.float64),
            ))
        xcf = np.vstack(x_parts).astype(np.float64, copy=False)
        ycf = np.concatenate(y_parts).astype(np.int8, copy=False)
        wcf = np.concatenate(w_parts).astype(np.float64, copy=False)
        require(np.all(np.isfinite(xcf)) and np.all(np.isfinite(wcf)), f"P4 fold {held_fold} non-finite training data")
        require(abs(float(np.sum(wcf[ycf == 1])) - 0.5 * len(train_dirs)) <= 1e-8, f"P4 fold {held_fold} positive weighting changed")
        require(abs(float(np.sum(wcf[ycf == 0])) - 0.5 * len(train_dirs)) <= 1e-8, f"P4 fold {held_fold} negative weighting changed")

        scaler_cf = StandardScaler()
        scaler_cf.fit(xcf, sample_weight=wcf)
        classifier_cf = LogisticRegression(
            penalty="l2", C=LOGISTIC_C, solver="lbfgs", max_iter=LOGISTIC_MAX_ITER,
            tol=LOGISTIC_TOL, fit_intercept=True, class_weight=None, random_state=None,
        )
        with warnings.catch_warnings(record=True) as caught_cf:
            warnings.simplefilter("always")
            classifier_cf.fit(scaler_cf.transform(xcf), ycf, sample_weight=wcf)
        convergence_cf = [w for w in caught_cf if issubclass(w.category, ConvergenceWarning)]
        require(not convergence_cf, f"P4 cross-fit convergence warning fold {held_fold}: {[str(w.message) for w in convergence_cf]}")
        require(int(np.max(classifier_cf.n_iter_)) < LOGISTIC_MAX_ITER, f"P4 cross-fit solver hit max_iter fold {held_fold}")
        fold_models.append({
            "held_fold": held_fold,
            "training_family_ids": train_family_ids,
            "heldout_family_ids": heldout_family_ids,
            "scaler_mean": np.asarray(scaler_cf.mean_, dtype=np.float64).tolist(),
            "scaler_scale": np.asarray(scaler_cf.scale_, dtype=np.float64).tolist(),
            "scaler_var": np.asarray(scaler_cf.var_, dtype=np.float64).tolist(),
            "logistic_coef": np.asarray(classifier_cf.coef_, dtype=np.float64).tolist(),
            "logistic_intercept": np.asarray(classifier_cf.intercept_, dtype=np.float64).tolist(),
            "logistic_n_iter": np.asarray(classifier_cf.n_iter_, dtype=np.int64).tolist(),
        })

        for d in held_dirs:
            family_id = str(d["family_id"])
            source_year = int(d["source_year"])
            target_year = int(d["target_year"])
            xp = np.asarray(d["positive_features"], dtype=np.float64)
            xn = np.asarray(d["negative_features"], dtype=np.float64)
            ids = list(map(str, d["negative_event_ids"]))
            seed_scores = np.asarray(classifier_cf.predict_proba(scaler_cf.transform(xp))[:, 1], dtype=np.float64)
            nonseed_scores = np.asarray(classifier_cf.predict_proba(scaler_cf.transform(xn))[:, 1], dtype=np.float64)
            require(np.all(np.isfinite(seed_scores)) and np.all(np.isfinite(nonseed_scores)), "P4 non-finite heldout probability")
            split0, split1 = p4_split_indices(family_id, source_year, target_year, ids)
            seed_median = float(np.median(seed_scores))
            sides = []
            for side_name, proposal_idx, calibration_idx in (("0<-1", split0, split1), ("1<-0", split1, split0)):
                proposal_scores = nonseed_scores[np.asarray(proposal_idx, dtype=np.int64)]
                calibration_scores = nonseed_scores[np.asarray(calibration_idx, dtype=np.int64)]
                selected = p4_select_threshold(proposal_scores, calibration_scores, seed_median)
                sides.append((side_name, proposal_idx, calibration_idx, proposal_scores, calibration_scores, selected))
            direction_reliable = all(side[-1] is not None for side in sides)
            reliable_directions += int(direction_reliable)
            unreliable_directions += int(not direction_reliable)
            row = {
                "family_id": family_id,
                "source_year": source_year,
                "target_year": target_year,
                "fold": held_fold,
                "seed_count": len(seed_scores),
                "negative_count": len(nonseed_scores),
                "seed_median": seed_median,
                "seed_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(seed_scores, dtype="<f8").tobytes()).hexdigest(),
                "split0_event_ids": [ids[i] for i in split0],
                "split1_event_ids": [ids[i] for i in split1],
                "reliable": bool(direction_reliable),
                "sides": {},
            }
            for side_name, proposal_idx, calibration_idx, proposal_scores, calibration_scores, selected in sides:
                side_row = {
                    "proposal_count": len(proposal_idx),
                    "calibration_count": len(calibration_idx),
                    "proposal_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(proposal_scores, dtype="<f8").tobytes()).hexdigest(),
                    "calibration_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(calibration_scores, dtype="<f8").tobytes()).hexdigest(),
                    "selected": selected,
                }
                row["sides"][side_name] = side_row
                if not direction_reliable:
                    continue
                require(selected is not None and float(selected["fdrhat"]) <= P4_LOCAL_FDR_Q, "P4 reliable side violates frozen q")
                threshold = float(selected["threshold"])
                for local, score in zip(proposal_idx, proposal_scores.tolist()):
                    if float(score) < threshold:
                        continue
                    event_id = ids[int(local)]
                    proposals_by_event[event_id].append({
                        "family_index": int(d["family_index"]),
                        "family_id": family_id,
                        "source_year": source_year,
                        "target_year": target_year,
                        "fold": held_fold,
                        "split_side": side_name,
                        "probability": float(score),
                        "threshold": threshold,
                        "fdrhat": float(selected["fdrhat"]),
                        "R": int(selected["R"]),
                        "B": int(selected["B"]),
                    })
                    total_surviving_proposals += 1
            calibration_rows.append(row)
        print(f"P4 crossfit/calibration fold {held_fold + 1}/{P4_FOLD_COUNT}", flush=True)

    require(len(calibration_rows) == len(directions), "P4 every direction must be held out exactly once")
    model_payload = {
        "feature_order": ["d_obs", "d_orb"],
        "fold_count": P4_FOLD_COUNT,
        "fold_rule": "first 8 bytes SHA256(family_id UTF-8) mod 5",
        "models": fold_models,
        "no_final_all_family_model": True,
        "settings": {
            "penalty": "l2", "C": LOGISTIC_C, "solver": "lbfgs", "max_iter": LOGISTIC_MAX_ITER,
            "tol": LOGISTIC_TOL, "fit_intercept": True, "class_weight": None,
            "family_direction_positive_total_weight": 0.5, "family_direction_negative_total_weight": 0.5,
            "window_half_width_deg": WINDOW_HALF_WIDTH_DEG,
        },
    }
    model_sha = canonical_sha(model_payload)
    calibration_payload = {
        "local_fdr_q": P4_LOCAL_FDR_Q,
        "pseudocount": P4_PSEUDOCOUNT,
        "minimum_split_size": P4_MIN_SPLIT_SIZE,
        "split_rule": "sort by SHA256(P4-SPLIT|family_id|source_year|target_year|event_id), event_id; alternate 0/1",
        "threshold_rule": "lowest observed proposal score with FDRhat<=0.05 and threshold<=heldout seed median; both reciprocal sides required",
        "family_fold": family_fold,
        "directions": sorted(calibration_rows, key=lambda r: (r["family_id"], r["source_year"], r["target_year"])),
    }
    calibration_sha = canonical_sha(calibration_payload)
    (args.output / "p4_crossfit_models_pretruth.json").write_text(json.dumps(model_payload, indent=2, sort_keys=True) + "\\n")
    (args.output / "p4_crossfit_models_pretruth.sha256").write_text(model_sha + "\\n")
    (args.output / "p4_local_fdr_pretruth.json").write_text(json.dumps(calibration_payload, indent=2, sort_keys=True) + "\\n")
    (args.output / "p4_local_fdr_pretruth.sha256").write_text(calibration_sha + "\\n")

    assignments: dict[str, dict[str, Any]] = {}
    conflicted = 0
    for event_id, proposals in proposals_by_event.items():
        require(event_id not in global_seed_ids, "seed entered P4 competition")
        family_ids = {str(p["family_id"]) for p in proposals}
        if len(family_ids) != 1:
            conflicted += 1
            continue
        require(len(proposals) == 1, f"P4 unexpected duplicate same-family proposal for {event_id}")
        assignments[event_id] = dict(proposals[0])

    decision_payload = {
        "proposals_by_event": {eid: proposals_by_event[eid] for eid in sorted(proposals_by_event)},
        "assignments": {eid: assignments[eid] for eid in sorted(assignments)},
        "conflict_rule": "assign iff exactly one family survives; multi-family survivors abstain",
    }
    decision_sha = canonical_sha(decision_payload)
    (args.output / "p4_decisions_pretruth.json.gz").write_bytes(gzip.compress(json.dumps(decision_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")))
    (args.output / "p4_decisions_pretruth.sha256").write_text(decision_sha + "\\n")

    additions_by_family: dict[int, list[str]] = defaultdict(list)
    for event_id, rec in assignments.items():
        additions_by_family[int(rec["family_index"])].append(event_id)

'''

ADD_KEY_ANCHOR = '''        out["p2_added_event_ids"] = additions
        out["p2_added_event_count"] = len(additions)
'''
ADD_KEY_REPL = '''        out["p4_added_event_ids"] = additions
        out["p4_added_event_count"] = len(additions)
'''

FREEZE_ANCHOR = '''    (args.output / "p2_membership_pretruth.sha256").write_text(membership_sha + "\\n")
    (args.output / "p2_expanded_families.json.gz").write_bytes(gzip.compress(frozen_payload))
'''
FREEZE_REPL = '''    (args.output / "p4_membership_pretruth.sha256").write_text(membership_sha + "\\n")
    (args.output / "p4_expanded_families.json.gz").write_bytes(gzip.compress(frozen_payload))
'''

P2_EVAL_ANCHOR = '''    p2_full = v8.mult.evaluate_order(hidden_labels, expanded, v8_order)
'''
P2_EVAL_REPL = '''    p4_full = v8.mult.evaluate_order(hidden_labels, expanded, v8_order)
'''
P2_LARGE_ANCHOR = '''    p2_large = large_summary(p2_full, totals, baseline_large_labels)
'''
P2_LARGE_REPL = '''    p4_large = large_summary(p4_full, totals, baseline_large_labels)
'''

GATES_START = '''    gates = {
'''
GATES_END = '''    result = {
'''
GATES_REPL = '''    gates = {
        "exact_v8_226_family_order": len(expanded) == EXPECTED_FAMILY_COUNT and [str(f["family_id"]) for f in expanded] == [str(f["family_id"]) for f in families],
        "exact_v8_seed_members_preserved": all(set(map(str, family["event_ids"])).issubset(set(map(str, out["event_ids"]))) for family, out in zip(families, expanded)),
        "v8_baseline_reproduced": bool(baseline_reproduced),
        "exact_dsh_source_identity": sha256_file(args.dsh_comparator) == DSH_COMPARATOR_SHA256,
        "p4_exact_five_family_folds": P4_FOLD_COUNT == 5 and set(family_fold.values()) == set(range(P4_FOLD_COUNT)),
        "p4_no_heldout_family_in_own_fold_training": all(not (set(m["training_family_ids"]) & set(m["heldout_family_ids"])) for m in fold_models),
        "p4_no_final_all_family_model": bool(model_payload["no_final_all_family_model"]),
        "p4_every_direction_heldout_once": len(calibration_rows) == len(directions),
        "p4_every_reciprocal_split_at_least_64": all(len(r["split0_event_ids"]) >= P4_MIN_SPLIT_SIZE and len(r["split1_event_ids"]) >= P4_MIN_SPLIT_SIZE for r in calibration_rows),
        "p4_q_and_pseudocount_exact": P4_LOCAL_FDR_Q == 0.05 and P4_PSEUDOCOUNT == 1.0,
        "p4_both_reciprocal_sides_required": all(bool(r["reliable"]) == all(r["sides"][side]["selected"] is not None for side in ("0<-1", "1<-0")) for r in calibration_rows),
        "p4_every_selected_side_respects_q_and_seed_median": all(
            side["selected"] is None or (float(side["selected"]["fdrhat"]) <= P4_LOCAL_FDR_Q and float(side["selected"]["threshold"]) <= float(r["seed_median"]))
            for r in calibration_rows for side in r["sides"].values()
        ),
        "p4_every_surviving_proposal_meets_threshold_and_q": all(float(p["probability"]) >= float(p["threshold"]) and float(p["fdrhat"]) <= P4_LOCAL_FDR_Q for ps in proposals_by_event.values() for p in ps),
        "p4_multi_family_survivors_abstain": all(len({str(p["family_id"]) for p in proposals_by_event[eid]}) == 1 for eid in assignments),
        "model_frozen_before_truth_evaluation": bool(model_sha),
        "p4_calibration_frozen_before_truth_evaluation": bool(calibration_sha),
        "p4_decisions_frozen_before_truth_evaluation": bool(decision_sha),
        "membership_frozen_before_truth_evaluation": bool(membership_sha),
        "classifier_converged": all(int(max(m["logistic_n_iter"])) < LOGISTIC_MAX_ITER for m in fold_models),
        "expansion_nonvacuous": len(assignments) > 0,
        "qualified_matches_no_regression": int(p4_full["qualified_matches"]) >= EXPECTED_BASELINE_QUALIFIED,
        "recovery_at_100_no_regression": int(p4_full["recovered_at_100"]) >= EXPECTED_BASELINE_RECOVERY100,
        "top100_dominant_precision_at_least_065": float(p4_full["top100_dominant_precision"]) >= TOP100_PRECISION_FLOOR,
        "macro_f1_gain_at_least_008": float(p4_full["macro_f1"]) >= EXPECTED_BASELINE_MACRO_F1 + MACRO_F1_GAIN_GATE,
        "large_shower_mean_recall_at_least_15x_v8": float(p4_large["mean_recall"]) >= LARGE_RECALL_MULTIPLIER * float(baseline_large["mean_recall"]),
        "large_shower_mean_precision_at_least_085": float(p4_large["mean_precision"]) >= LARGE_PRECISION_FLOOR,
    }
    verdict = "PASS_CROSSFIT_LOCAL_FDR_MEMBERSHIP_P4_DEVELOPMENT" if all(gates.values()) else "FAIL_CROSSFIT_LOCAL_FDR_MEMBERSHIP_P4_NO_GO"

    result = {
'''

RESULT_START = '''    result = {
'''
RESULT_END = '''    return 0
'''
RESULT_BODY = '''    result = {
        "verdict": verdict,
        "classification": "family-excluded cross-fit two-view membership with reciprocal deterministic local-background FDR calibration and conflict abstention",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [float(support.BLIND_LOW), float(support.BLIND_HIGH)],
            "v8_source_commit": V8_SOURCE_COMMIT,
            "family_count": EXPECTED_FAMILY_COUNT,
            "features": ["cross-year source-seed OAS Mahalanobis observation distance", "minimum exact D_SH to source-year immutable seed"],
            "window_half_width_deg": WINDOW_HALF_WIDTH_DEG,
            "negative_minimum_per_direction": MIN_DIRECTION_NEGATIVES,
            "fold_count": P4_FOLD_COUNT,
            "fold_rule": "first 8 bytes SHA256(family_id UTF-8) mod 5",
            "reciprocal_split_rule": "SHA256(P4-SPLIT|family|source|target|event), then alternating IDs",
            "local_fdr_q": P4_LOCAL_FDR_Q,
            "local_fdr_pseudocount": P4_PSEUDOCOUNT,
            "seed_reference": "heldout recurrent-seed median probability from same family-excluded fold model",
            "threshold_rule": "lowest observed proposal score with FDRhat<=0.05 and threshold<=seed median; both reciprocal sides required",
            "final_all_family_model": False,
            "conflict_rule": "assign only if exactly one family survives; otherwise abstain",
            "new_members_can_seed_growth": False,
            "ranking_after_membership": "unchanged exact promoted-v8 multiplicity order",
            "parameter_search": False,
        },
        "sources": sources,
        "model_pretruth_sha256": model_sha,
        "calibration_pretruth_sha256": calibration_sha,
        "decisions_pretruth_sha256": decision_sha,
        "membership_pretruth_sha256": membership_sha,
        "baseline_v8": {k: v for k, v in baseline_full.items() if k != "per_label"},
        "p4": {k: v for k, v in p4_full.items() if k != "per_label"},
        "baseline_large_shower": baseline_large,
        "p4_large_shower": p4_large,
        "gates": gates,
        "diagnostics": {
            "training_rows_reference_only": int(len(X)),
            "positive_training_rows_reference_only": int(np.sum(y == 1)),
            "negative_training_rows_reference_only": int(np.sum(y == 0)),
            "family_directions": len(directions),
            "valid_orbit_events": len(orbit_by_id),
            "reliable_directions": reliable_directions,
            "unreliable_directions": unreliable_directions,
            "surviving_direction_proposals": total_surviving_proposals,
            "proposal_events": len(proposals_by_event),
            "conflicted_proposal_events_abstained": conflicted,
            "assigned_nonseed_events": len(assignments),
            "families_gaining_members": sum(bool(additions_by_family.get(index)) for index in range(len(families))),
            "v8_scoring_summary": v8_scoring_summary,
        },
        "direction_audits": direction_audits,
        "orbit_audits": orbit_audits,
        "claim_boundary": "Target-excluded development only. P4's empirical local-background FDR estimate is a conservative calibration heuristic, not a universal exact-FDR theorem. Promotion still requires frozen literature and external validation before target access.",
    }
    (args.output / "crossfit_local_fdr_membership_p4_development.json").write_text(json.dumps(result, indent=2) + "\\n")
    (args.output / "CROSSFIT_LOCAL_FDR_MEMBERSHIP_P4_DEVELOPMENT.md").write_text(
        "# OrbitTrace cross-fitted reciprocal local-FDR membership P4 development\\n\\n"
        f"Verdict: **`{verdict}`**\\n\\n"
        f"- v8 -> P4 macro F1: **{baseline_full['macro_f1']:.6f} -> {p4_full['macro_f1']:.6f}**\\n"
        f"- v8 -> P4 qualified: **{baseline_full['qualified_matches']} -> {p4_full['qualified_matches']}**\\n"
        f"- v8 -> P4 recovery@100: **{baseline_full['recovered_at_100']} -> {p4_full['recovered_at_100']}**\\n"
        f"- v8 -> P4 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p4_full['top100_dominant_precision']:.6f}**\\n"
        f"- large-shower recall: **{baseline_large['mean_recall']:.6f} -> {p4_large['mean_recall']:.6f}**\\n"
        f"- large-shower precision: **{baseline_large['mean_precision']:.6f} -> {p4_large['mean_precision']:.6f}**\\n"
        f"- reliable/unreliable directions: **{reliable_directions}/{unreliable_directions}**\\n"
        f"- assigned nonseed events: **{len(assignments):,}**; conflicted events abstained: **{conflicted:,}**\\n"
        f"- crossfit model SHA-256: `{model_sha}`\\n"
        f"- local-FDR calibration SHA-256: `{calibration_sha}`\\n"
        f"- decisions SHA-256: `{decision_sha}`\\n"
        f"- membership SHA-256: `{membership_sha}`\\n\\n"
        "No OrbitTrace target information or target-region event was used.\\n"
    )
    print((args.output / "CROSSFIT_LOCAL_FDR_MEMBERSHIP_P4_DEVELOPMENT.md").read_text(), flush=True)
    return 0
'''


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P4 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p4_patch.py CANONICAL_P2 OUTPUT")
    source, output = Path(sys.argv[1]), Path(sys.argv[2])
    raw = source.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_P2_SHA256:
        raise RuntimeError(f"canonical P2 SHA changed: {actual}")
    text = raw.decode("utf-8")
    text = replace_once(text, CONST_ANCHOR, CONST_REPL, "constants")
    text = replace_once(text, DIRECTION_ANCHOR, DIRECTION_REPL, "direction positive features")
    text = replace_once(text, HELPER_ANCHOR, HELPER_REPL, "P4 helper insertion")
    start = text.index(SCIENCE_START)
    end = text.index(SCIENCE_END, start)
    text = text[:start] + SCIENCE_REPL + text[end:]
    text = replace_once(text, ADD_KEY_ANCHOR, ADD_KEY_REPL, "P4 addition keys")
    text = replace_once(text, FREEZE_ANCHOR, FREEZE_REPL, "P4 membership freeze")
    text = replace_once(text, P2_EVAL_ANCHOR, P2_EVAL_REPL, "P4 evaluation name")
    text = replace_once(text, P2_LARGE_ANCHOR, P2_LARGE_REPL, "P4 large-shower name")
    gates_start = text.index(GATES_START)
    result_start = text.index(GATES_END, gates_start)
    text = text[:gates_start] + GATES_REPL + text[result_start + len(GATES_END):]
    result_start = text.index(RESULT_START)
    return_start = text.index(RESULT_END, result_start)
    text = text[:result_start] + RESULT_BODY + text[return_start + len(RESULT_END):]
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target token introduced")
    output.write_text(text, encoding="utf-8")
    compile(text, str(output), "exec")
    print(f"P4_INPUT_P2_SHA256={EXPECTED_P2_SHA256}")
    print(f"P4_OUTPUT_SHA256={hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    print("P4_PATCH_SCOPE=family-excluded reciprocal local-background FDR calibration plus conflict abstention; v8 cores/rank and P2 features/logistic settings preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
