#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P2_SHA256 = "f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


CONST_ANCHOR = '''RESPONSIBILITY_THRESHOLD = 0.5
'''
CONST_REPL = '''RESPONSIBILITY_THRESHOLD = 0.5
P3_FOLD_COUNT = 5
P3_NEGATIVE_TAIL_MAX = 0.10
P3_SEED_FLOOR_MIN = 0.5
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

FINAL_FIT_ANCHOR = '''    scaler = StandardScaler()
    scaler.fit(X, sample_weight=sample_weight)
'''
FINAL_FIT_REPL = '''    # P3 pretruth cross-fitting. Family folds are deterministic and no row from
    # a held-out family enters the classifier used to set that family's gate.
    family_fold = {
        str(f["family_id"]): int.from_bytes(hashlib.sha256(str(f["family_id"]).encode("utf-8")).digest()[:8], "big") % P3_FOLD_COUNT
        for f in families
    }
    require(len(family_fold) == len(families), "P3 family-fold universe changed")
    require(set(family_fold.values()) == set(range(P3_FOLD_COUNT)), "P3 deterministic folds not all populated")
    crossfit_models: list[dict[str, Any]] = []
    reliability: dict[str, dict[str, Any]] = {}
    for held_fold in range(P3_FOLD_COUNT):
        train_dirs = [d for d in directions if family_fold[str(d["family_id"])] != held_fold]
        held_dirs = [d for d in directions if family_fold[str(d["family_id"])] == held_fold]
        require(train_dirs and held_dirs, f"P3 fold {held_fold} empty train/holdout")
        train_family_ids = sorted({str(d["family_id"]) for d in train_dirs})
        heldout_family_ids = sorted({str(d["family_id"]) for d in held_dirs})
        require(not (set(train_family_ids) & set(heldout_family_ids)), f"P3 fold {held_fold} family leakage")
        x_parts: list[np.ndarray] = []
        y_parts: list[np.ndarray] = []
        w_parts: list[np.ndarray] = []
        for d in train_dirs:
            xp = np.asarray(d["positive_features"], dtype=np.float64)
            xn = np.asarray(d["negative_features"], dtype=np.float64)
            require(len(xp) >= 4 and len(xn) >= MIN_DIRECTION_NEGATIVES, "P3 cross-fit direction support changed")
            x_parts.extend((xp, xn))
            y_parts.extend((np.ones(len(xp), dtype=np.int8), np.zeros(len(xn), dtype=np.int8)))
            w_parts.extend((
                np.full(len(xp), 0.5 / len(xp), dtype=np.float64),
                np.full(len(xn), 0.5 / len(xn), dtype=np.float64),
            ))
        xcf = np.vstack(x_parts).astype(np.float64, copy=False)
        ycf = np.concatenate(y_parts).astype(np.int8, copy=False)
        wcf = np.concatenate(w_parts).astype(np.float64, copy=False)
        require(np.all(np.isfinite(xcf)) and np.all(np.isfinite(wcf)), f"P3 fold {held_fold} non-finite training data")
        require(abs(float(np.sum(wcf[ycf == 1])) - 0.5 * len(train_dirs)) <= 1e-8, f"P3 fold {held_fold} positive weighting changed")
        require(abs(float(np.sum(wcf[ycf == 0])) - 0.5 * len(train_dirs)) <= 1e-8, f"P3 fold {held_fold} negative weighting changed")
        scf = StandardScaler()
        scf.fit(xcf, sample_weight=wcf)
        clf = LogisticRegression(
            penalty="l2", C=LOGISTIC_C, solver="lbfgs", max_iter=LOGISTIC_MAX_ITER,
            tol=LOGISTIC_TOL, fit_intercept=True, class_weight=None, random_state=None,
        )
        with warnings.catch_warnings(record=True) as caught_cf:
            warnings.simplefilter("always")
            clf.fit(scf.transform(xcf), ycf, sample_weight=wcf)
        conv_cf = [w for w in caught_cf if issubclass(w.category, ConvergenceWarning)]
        require(not conv_cf, f"P3 cross-fit convergence warning fold {held_fold}: {[str(w.message) for w in conv_cf]}")
        require(int(np.max(clf.n_iter_)) < LOGISTIC_MAX_ITER, f"P3 cross-fit solver hit max_iter fold {held_fold}")
        crossfit_models.append({
            "held_fold": held_fold,
            "training_family_ids": train_family_ids,
            "heldout_family_ids": heldout_family_ids,
            "scaler_mean": np.asarray(scf.mean_, dtype=np.float64).tolist(),
            "scaler_scale": np.asarray(scf.scale_, dtype=np.float64).tolist(),
            "scaler_var": np.asarray(scf.var_, dtype=np.float64).tolist(),
            "logistic_coef": np.asarray(clf.coef_, dtype=np.float64).tolist(),
            "logistic_intercept": np.asarray(clf.intercept_, dtype=np.float64).tolist(),
            "logistic_n_iter": np.asarray(clf.n_iter_, dtype=np.int64).tolist(),
        })
        for d in held_dirs:
            xp = np.asarray(d["positive_features"], dtype=np.float64)
            xn = np.asarray(d["negative_features"], dtype=np.float64)
            pp = np.asarray(clf.predict_proba(scf.transform(xp))[:, 1], dtype=np.float64)
            pn = np.asarray(clf.predict_proba(scf.transform(xn))[:, 1], dtype=np.float64)
            require(np.all(np.isfinite(pp)) and np.all(np.isfinite(pn)), "P3 non-finite cross-fit probability")
            seed_floor = float(np.min(pp))
            negative_tail = float(np.mean(pn >= seed_floor))
            key = f"{d['family_id']}|{d['source_year']}|{d['target_year']}"
            require(key not in reliability, f"P3 duplicate reliability key {key}")
            reliability[key] = {
                "family_id": str(d["family_id"]),
                "source_year": int(d["source_year"]),
                "target_year": int(d["target_year"]),
                "fold": held_fold,
                "seed_count": int(len(xp)),
                "negative_count": int(len(xn)),
                "seed_floor": seed_floor,
                "negative_tail": negative_tail,
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
                "negative_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pn, dtype="<f8").tobytes()).hexdigest(),
                "reliable": bool(len(xp) >= 4 and seed_floor > P3_SEED_FLOOR_MIN and negative_tail <= P3_NEGATIVE_TAIL_MAX),
            }
    require(len(reliability) == len(directions), "P3 reliability direction universe changed")
    require(all(sum(1 for d in directions if str(d["family_id"]) == fid) == 2 for fid in family_fold), "P3 family direction count changed")
    crossfit_payload = {
        "fold_count": P3_FOLD_COUNT,
        "fold_rule": "int.from_bytes(SHA256(family_id UTF-8)[:8], big) % 5",
        "family_fold": family_fold,
        "models": crossfit_models,
        "reliability": reliability,
        "seed_floor_rule": "minimum held-out recurrent-seed probability",
        "seed_floor_min_strict": P3_SEED_FLOOR_MIN,
        "negative_tail_max": P3_NEGATIVE_TAIL_MAX,
        "no_known_shower_truth_used": True,
    }
    crossfit_sha = canonical_sha(crossfit_payload)
    (args.output / "p3_crossfit_pretruth.json").write_text(json.dumps(crossfit_payload, indent=2, sort_keys=True) + "\\n")
    (args.output / "p3_crossfit_pretruth.sha256").write_text(crossfit_sha + "\\n")

    # The final all-family model is exactly canonical P2 and is fit only after
    # the cross-fit gates are immutable.
    scaler = StandardScaler()
    scaler.fit(X, sample_weight=sample_weight)
'''

SCORING_ANCHOR = '''    for index, direction in enumerate(directions, start=1):
        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)
        ids = list(direction["negative_event_ids"])
        probabilities = classifier.predict_proba(scaler.transform(features))[:, 1]
        probabilities = np.clip(probabilities, eps, 1.0 - eps)
        odds = probabilities / (1.0 - probabilities)
        for event_id, probability, odd in zip(ids, probabilities.tolist(), odds.tolist()):
            proposals_by_event[event_id].append({
                "family_index": int(direction["family_index"]),
                "family_id": str(direction["family_id"]),
                "source_year": int(direction["source_year"]),
                "target_year": int(direction["target_year"]),
                "probability": float(probability),
                "odds": float(odd),
            })
'''
SCORING_REPL = '''    for index, direction in enumerate(directions, start=1):
        direction.pop("positive_features", None)
        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)
        ids = list(direction["negative_event_ids"])
        probabilities = classifier.predict_proba(scaler.transform(features))[:, 1]
        probabilities = np.clip(probabilities, eps, 1.0 - eps)
        key = f"{direction['family_id']}|{direction['source_year']}|{direction['target_year']}"
        gate = reliability[key]
        if not bool(gate["reliable"]):
            if index % 50 == 0 or index == len(directions):
                print(f"P3 scoring direction {index}/{len(directions)}", flush=True)
            continue
        allowed = probabilities >= float(gate["seed_floor"])
        odds = probabilities / (1.0 - probabilities)
        for event_id, probability, odd, keep in zip(ids, probabilities.tolist(), odds.tolist(), allowed.tolist()):
            if not bool(keep):
                continue
            proposals_by_event[event_id].append({
                "family_index": int(direction["family_index"]),
                "family_id": str(direction["family_id"]),
                "source_year": int(direction["source_year"]),
                "target_year": int(direction["target_year"]),
                "probability": float(probability),
                "odds": float(odd),
                "seed_floor": float(gate["seed_floor"]),
            })
'''

PRINT_ANCHOR = '''            print(f"P2 scoring direction {index}/{len(directions)}", flush=True)
'''
PRINT_REPL = '''            print(f"P3 scoring direction {index}/{len(directions)}", flush=True)
'''

MEMBERSHIP_FREEZE_ANCHOR = '''    (args.output / "p2_membership_pretruth.sha256").write_text(membership_sha + "\\n")
    (args.output / "p2_expanded_families.json.gz").write_bytes(gzip.compress(frozen_payload))

    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
'''
MEMBERSHIP_FREEZE_REPL = '''    (args.output / "p3_membership_pretruth.sha256").write_text(membership_sha + "\\n")
    (args.output / "p3_expanded_families.json.gz").write_bytes(gzip.compress(frozen_payload))
    decision_payload = {
        "proposals_by_event": {eid: proposals_by_event[eid] for eid in sorted(proposals_by_event)},
        "assignments": {eid: assignments[eid] for eid in sorted(assignments)},
    }
    decision_raw = json.dumps(decision_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    decision_sha = hashlib.sha256(decision_raw).hexdigest()
    (args.output / "p3_decisions_pretruth.sha256").write_text(decision_sha + "\\n")
    (args.output / "p3_decisions_pretruth.json.gz").write_bytes(gzip.compress(decision_raw))

    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
'''

GATES_ANCHOR = '''        "model_frozen_before_truth_evaluation": bool(model_sha),
        "membership_frozen_before_truth_evaluation": bool(membership_sha),
        "classifier_converged": int(np.max(classifier.n_iter_)) < LOGISTIC_MAX_ITER,
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATES_REPL = '''        "model_frozen_before_truth_evaluation": bool(model_sha),
        "membership_frozen_before_truth_evaluation": bool(membership_sha),
        "classifier_converged": int(np.max(classifier.n_iter_)) < LOGISTIC_MAX_ITER,
        "p3_exact_five_crossfit_folds": P3_FOLD_COUNT == 5 and set(family_fold.values()) == set(range(5)),
        "p3_crossfit_frozen_before_truth": len(crossfit_sha) == 64,
        "p3_decisions_frozen_before_truth": len(decision_sha) == 64,
        "p3_every_family_in_exactly_one_fold": len(family_fold) == EXPECTED_FAMILY_COUNT,
        "p3_no_heldout_family_in_own_fold_training": all(not (set(m["training_family_ids"]) & set(m["heldout_family_ids"])) for m in crossfit_models),
        "p3_every_direction_has_one_heldout_gate": len(reliability) == len(directions),
        "p3_exact_seed_floor_and_tail_rule": all(bool(r["reliable"]) == bool(r["seed_count"] >= 4 and r["seed_floor"] > P3_SEED_FLOOR_MIN and r["negative_tail"] <= P3_NEGATIVE_TAIL_MAX) for r in reliability.values()),
        "p3_no_unreliable_direction_can_propose": all(
            bool(reliability[f"{d['family_id']}|{d['source_year']}|{d['target_year']}"]["reliable"])
            or not any(
                str(p.get("family_id")) == str(d["family_id"])
                and int(p.get("source_year")) == int(d["source_year"])
                and int(p.get("target_year")) == int(d["target_year"])
                for ps in proposals_by_event.values() for p in ps
            )
            for d in directions
        ),
        "p3_every_surviving_proposal_meets_seed_floor": all(
            float(p["probability"]) >= float(p["seed_floor"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "cross-year self-supervised two-view membership discriminator; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "cross-fitted held-out seed-floor two-view membership discriminator; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "parameter_search": False,
        },
'''
CONFIG_REPL = '''            "parameter_search": False,
            "p3_fold_count": P3_FOLD_COUNT,
            "p3_fold_assignment": "first 8 bytes of SHA256(family_id UTF-8) mod 5",
            "p3_seed_floor": "minimum held-out recurrent-seed probability under family-excluded fold model; strict >0.5",
            "p3_negative_tail_max": P3_NEGATIVE_TAIL_MAX,
            "p3_final_probability_gate": "probability >= immutable family-direction seed_floor",
        },
'''

RESULT_HASH_ANCHOR = '''        "model_pretruth_sha256": model_sha,
        "membership_pretruth_sha256": membership_sha,
'''
RESULT_HASH_REPL = '''        "crossfit_pretruth_sha256": crossfit_sha,
        "model_pretruth_sha256": model_sha,
        "membership_pretruth_sha256": membership_sha,
        "decisions_pretruth_sha256": decision_sha,
'''

RESULT_METHOD_ANCHOR = '''        "p2": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
RESULT_METHOD_REPL = '''        "p3": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
RESULT_LARGE_ANCHOR = '''        "p2_large_shower": p2_large,
'''
RESULT_LARGE_REPL = '''        "p3_large_shower": p2_large,
'''

DIAG_BUG_ANCHOR = '''            "valid_nonseed_events_by_year": {str(year): len(valid_nonseed_by_year[year]) for year in YEARS},
'''
DIAG_BUG_REPL = '''            "nonseed_events_by_year": {str(year): len(nonseed_by_year[year]) for year in YEARS},
            "p3_reliable_directions": sum(bool(r["reliable"]) for r in reliability.values()),
            "p3_unreliable_directions": sum(not bool(r["reliable"]) for r in reliability.values()),
            "p3_crossfit_pretruth_sha256": crossfit_sha,
            "p3_decisions_pretruth_sha256": decision_sha,
'''

JSON_FILE_ANCHOR = '''    (args.output / "crossyear_two_view_membership_p2_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_FILE_REPL = '''    (args.output / "crossfit_seed_floor_membership_p3_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_FILE_ANCHOR = '''    (args.output / "CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md").write_text(
'''
MD_FILE_REPL = '''    (args.output / "CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace cross-year two-view membership P2 development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace cross-fitted seed-floor two-view membership P3 development\\n\\n"
'''
SUMMARY_P2_ANCHOR = '''f"- v8 -> P2 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_P2_REPL = '''f"- v8 -> P3 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
PRINT_ANCHOR_2 = '''    print((args.output / "CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL_2 = '''    print((args.output / "CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT.md").read_text(), flush=True)
'''


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P3 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p3_patch.py CANONICAL_P2 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P2_SHA256:
        raise RuntimeError(f"canonical P2 SHA changed: {actual}")
    text = raw.decode("utf-8")
    replacements = (
        (CONST_ANCHOR, CONST_REPL, "constants"),
        (DIRECTION_ANCHOR, DIRECTION_REPL, "direction feature retention"),
        (FINAL_FIT_ANCHOR, FINAL_FIT_REPL, "crossfit insertion"),
        (SCORING_ANCHOR, SCORING_REPL, "seed-floor proposal gating"),
        (PRINT_ANCHOR, PRINT_REPL, "progress label"),
        (MEMBERSHIP_FREEZE_ANCHOR, MEMBERSHIP_FREEZE_REPL, "pretruth decision freeze"),
        (GATES_ANCHOR, GATES_REPL, "crossfit integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "configuration"),
        (RESULT_HASH_ANCHOR, RESULT_HASH_REPL, "pretruth hashes"),
        (RESULT_METHOD_ANCHOR, RESULT_METHOD_REPL, "result method key"),
        (RESULT_LARGE_ANCHOR, RESULT_LARGE_REPL, "large-shower key"),
        (DIAG_BUG_ANCHOR, DIAG_BUG_REPL, "diagnostic variable plus P3 diagnostics"),
        (JSON_FILE_ANCHOR, JSON_FILE_REPL, "json filename"),
        (MD_FILE_ANCHOR, MD_FILE_REPL, "markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "markdown title"),
        (SUMMARY_P2_ANCHOR, SUMMARY_P2_REPL, "summary method label"),
        (PRINT_ANCHOR_2, PRINT_REPL_2, "print filename"),
    )
    patched = text
    for before, after, label in replacements:
        patched = replace_once(patched, before, after, label)
    if "OrbitTrace-April" in patched or "target_coordinate" in patched:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(patched, encoding="utf-8")
    print(f"P3_INPUT_P2_SHA256={EXPECTED_P2_SHA256}")
    print(f"P3_OUTPUT_SHA256={digest(patched.encode('utf-8'))}")
    print("P3_PATCH_SCOPE=five-fold held-out seed-floor reliability gate only; P2 seeds/features/final model/responsibility/scientific gates unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
