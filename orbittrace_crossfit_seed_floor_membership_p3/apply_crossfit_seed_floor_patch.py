#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_INPUT_SHA256 = "f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb"

BEFORE_CONSTANTS = '''DSH_BATCH_SIZE = 512\n'''
AFTER_CONSTANTS = '''DSH_BATCH_SIZE = 512\nP3_FOLDS = 5\nP3_SEED_FLOOR_MIN = 0.5\nP3_NEGATIVE_TAIL_MAX = 0.10\n'''

BEFORE_DIRECTION = '''            directions.append({\n                "family_index": family_index,\n                "family_id": family_id,\n                "source_year": source_year,\n                "target_year": target_year,\n                "source_seed_ids": source_ids,\n                "target_seed_ids": target_ids,\n                "negative_event_ids": negative_ids,\n                "negative_features": x_neg,\n            })\n'''
AFTER_DIRECTION = '''            directions.append({\n                "family_index": family_index,\n                "family_id": family_id,\n                "source_year": source_year,\n                "target_year": target_year,\n                "source_seed_ids": source_ids,\n                "target_seed_ids": target_ids,\n                "positive_features": x_pos,\n                "negative_event_ids": negative_ids,\n                "negative_features": x_neg,\n            })\n'''

BEFORE_FINAL_FIT = '''    X = np.vstack(training_x).astype(np.float64, copy=False)\n'''
AFTER_FINAL_FIT = r'''    # P3 addition: deterministic family-level five-fold cross-fitting.  No known-\n    # shower truth is read here.  Each held-out family is scored only by a model\n    # whose training rows contain no direction from that family.\n    def p3_family_fold(family_id: str) -> int:\n        return int.from_bytes(hashlib.sha256(family_id.encode("utf-8")).digest()[:8], "big") % P3_FOLDS\n\n    family_fold = {str(f["family_id"]): p3_family_fold(str(f["family_id"])) for f in families}\n    require(len(family_fold) == EXPECTED_FAMILY_COUNT, "P3 fold family universe changed")\n    require(set(family_fold.values()) == set(range(P3_FOLDS)), "P3 deterministic folds not all populated")\n    reliability_by_direction: dict[tuple[str, int, int], dict[str, Any]] = {}\n    crossfit_models: list[dict[str, Any]] = []\n    heldout_score_hashes: list[dict[str, Any]] = []\n\n    for fold in range(P3_FOLDS):\n        train_dirs = [d for d in directions if family_fold[str(d["family_id"])] != fold]\n        heldout_dirs = [d for d in directions if family_fold[str(d["family_id"])] == fold]\n        require(train_dirs and heldout_dirs, f"P3 empty train/heldout fold {fold}")\n        require(\n            not ({str(d["family_id"]) for d in train_dirs} & {str(d["family_id"]) for d in heldout_dirs}),\n            f"P3 heldout family leaked into training fold {fold}",\n        )\n        cf_x_parts: list[np.ndarray] = []\n        cf_y_parts: list[np.ndarray] = []\n        cf_w_parts: list[np.ndarray] = []\n        for d in train_dirs:\n            xp = np.asarray(d["positive_features"], dtype=np.float64)\n            xn = np.asarray(d["negative_features"], dtype=np.float64)\n            require(len(xp) >= 4 and len(xn) >= MIN_DIRECTION_NEGATIVES, "P3 crossfit train direction became ineligible")\n            cf_x_parts.extend((xp, xn))\n            cf_y_parts.extend((np.ones(len(xp), dtype=np.int8), np.zeros(len(xn), dtype=np.int8)))\n            cf_w_parts.extend((\n                np.full(len(xp), 0.5 / len(xp), dtype=np.float64),\n                np.full(len(xn), 0.5 / len(xn), dtype=np.float64),\n            ))\n        cf_X = np.vstack(cf_x_parts).astype(np.float64, copy=False)\n        cf_y = np.concatenate(cf_y_parts).astype(np.int8, copy=False)\n        cf_w = np.concatenate(cf_w_parts).astype(np.float64, copy=False)\n        require(np.all(np.isfinite(cf_X)) and np.all(np.isfinite(cf_w)), f"P3 non-finite fold {fold} training data")\n        cf_scaler = StandardScaler()\n        cf_scaler.fit(cf_X, sample_weight=cf_w)\n        cf_classifier = LogisticRegression(\n            penalty="l2", C=LOGISTIC_C, solver="lbfgs", max_iter=LOGISTIC_MAX_ITER,\n            tol=LOGISTIC_TOL, fit_intercept=True, class_weight=None, random_state=None,\n        )\n        with warnings.catch_warnings(record=True) as caught:\n            warnings.simplefilter("always")\n            cf_classifier.fit(cf_scaler.transform(cf_X), cf_y, sample_weight=cf_w)\n        convergence = [w for w in caught if issubclass(w.category, ConvergenceWarning)]\n        require(not convergence, f"P3 crossfit convergence warning fold {fold}: {[str(w.message) for w in convergence]}")\n        require(int(np.max(cf_classifier.n_iter_)) < LOGISTIC_MAX_ITER, f"P3 crossfit fold {fold} hit max_iter")\n        train_families = sorted({str(d["family_id"]) for d in train_dirs})\n        heldout_families = sorted({str(d["family_id"]) for d in heldout_dirs})\n        crossfit_models.append({\n            "fold": fold,\n            "train_family_ids": train_families,\n            "heldout_family_ids": heldout_families,\n            "scaler_mean": np.asarray(cf_scaler.mean_, dtype=np.float64).tolist(),\n            "scaler_scale": np.asarray(cf_scaler.scale_, dtype=np.float64).tolist(),\n            "scaler_var": np.asarray(cf_scaler.var_, dtype=np.float64).tolist(),\n            "logistic_coef": np.asarray(cf_classifier.coef_, dtype=np.float64).tolist(),\n            "logistic_intercept": np.asarray(cf_classifier.intercept_, dtype=np.float64).tolist(),\n            "logistic_n_iter": np.asarray(cf_classifier.n_iter_, dtype=np.int64).tolist(),\n        })\n        for d in heldout_dirs:\n            xp = np.asarray(d["positive_features"], dtype=np.float64)\n            xn = np.asarray(d["negative_features"], dtype=np.float64)\n            pp = np.asarray(cf_classifier.predict_proba(cf_scaler.transform(xp))[:, 1], dtype=np.float64)\n            pn = np.asarray(cf_classifier.predict_proba(cf_scaler.transform(xn))[:, 1], dtype=np.float64)\n            require(np.all(np.isfinite(pp)) and np.all(np.isfinite(pn)), "P3 non-finite heldout score")\n            seed_floor = float(np.min(pp))\n            negative_tail = float(np.mean(pn >= seed_floor))\n            reliable = bool(\n                len(d["target_seed_ids"]) >= 4\n                and seed_floor > P3_SEED_FLOOR_MIN\n                and negative_tail <= P3_NEGATIVE_TAIL_MAX\n            )\n            key = (str(d["family_id"]), int(d["source_year"]), int(d["target_year"]))\n            require(key not in reliability_by_direction, f"P3 duplicate heldout direction {key}")\n            reliability_by_direction[key] = {\n                "fold": fold,\n                "family_id": key[0],\n                "source_year": key[1],\n                "target_year": key[2],\n                "positive_count": len(pp),\n                "negative_count": len(pn),\n                "seed_floor": seed_floor,\n                "negative_tail_fraction": negative_tail,\n                "reliable": reliable,\n            }\n            heldout_score_hashes.append({\n                **reliability_by_direction[key],\n                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),\n                "negative_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pn, dtype="<f8").tobytes()).hexdigest(),\n            })\n\n    require(len(reliability_by_direction) == len(directions), "P3 not every family-direction held out exactly once")\n    crossfit_payload = {\n        "fold_rule": "int.from_bytes(SHA256(family_id UTF-8)[:8], big) % 5",\n        "fold_count": P3_FOLDS,\n        "seed_floor_rule": "minimum held-out recurrent-seed probability",\n        "seed_floor_strict_min": P3_SEED_FLOOR_MIN,\n        "negative_tail_max": P3_NEGATIVE_TAIL_MAX,\n        "models": crossfit_models,\n        "heldout_direction_score_hashes": sorted(heldout_score_hashes, key=lambda r: (r["family_id"], r["source_year"], r["target_year"])),\n    }\n    crossfit_sha = canonical_sha(crossfit_payload)\n    (args.output / "p3_crossfit_pretruth.json").write_text(json.dumps(crossfit_payload, indent=2, sort_keys=True) + "\\n")\n    (args.output / "p3_crossfit_pretruth.sha256").write_text(crossfit_sha + "\\n")\n\n    X = np.vstack(training_x).astype(np.float64, copy=False)\n'''

BEFORE_SCORING = '''    for index, direction in enumerate(directions, start=1):\n        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)\n        ids = list(direction["negative_event_ids"])\n        probabilities = classifier.predict_proba(scaler.transform(features))[:, 1]\n        probabilities = np.clip(probabilities, eps, 1.0 - eps)\n        odds = probabilities / (1.0 - probabilities)\n        for event_id, probability, odd in zip(ids, probabilities.tolist(), odds.tolist()):\n            proposals_by_event[event_id].append({\n'''
AFTER_SCORING = '''    p3_unreliable_directions = 0\n    p3_seed_floor_rejections = 0\n    p3_surviving_proposals = 0\n    for index, direction in enumerate(directions, start=1):\n        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)\n        direction.pop("positive_features", None)\n        ids = list(direction["negative_event_ids"])\n        key = (str(direction["family_id"]), int(direction["source_year"]), int(direction["target_year"]))\n        rel = reliability_by_direction[key]\n        if not bool(rel["reliable"]):\n            p3_unreliable_directions += 1\n            continue\n        probabilities = classifier.predict_proba(scaler.transform(features))[:, 1]\n        probabilities = np.clip(probabilities, eps, 1.0 - eps)\n        odds = probabilities / (1.0 - probabilities)\n        seed_floor = float(rel["seed_floor"])\n        for event_id, probability, odd in zip(ids, probabilities.tolist(), odds.tolist()):\n            if float(probability) < seed_floor:\n                p3_seed_floor_rejections += 1\n                continue\n            p3_surviving_proposals += 1\n            proposals_by_event[event_id].append({\n'''

BEFORE_PREFIX = '''        "verdict": verdict,\n        "classification": "cross-year self-supervised two-view membership discriminator; immutable promoted-v8 cores and rank",\n'''
AFTER_PREFIX = '''        "verdict": verdict,\n        "classification": "cross-fitted seed-floor cross-year two-view membership; immutable promoted-v8 cores and rank",\n'''

BEFORE_GATES = '''        "membership_frozen_before_truth_evaluation": bool(membership_sha),\n        "classifier_converged": int(np.max(classifier.n_iter_)) < LOGISTIC_MAX_ITER,\n        "expansion_nonvacuous": len(assignments) > 0,\n'''
AFTER_GATES = '''        "membership_frozen_before_truth_evaluation": bool(membership_sha),\n        "classifier_converged": int(np.max(classifier.n_iter_)) < LOGISTIC_MAX_ITER,\n        "p3_exact_five_deterministic_family_folds": len(crossfit_models) == P3_FOLDS and set(family_fold.values()) == set(range(P3_FOLDS)),\n        "p3_every_direction_heldout_once": len(reliability_by_direction) == len(directions),\n        "p3_crossfit_payload_frozen_before_truth": bool(crossfit_sha),\n        "p3_no_unreliable_direction_proposal": all(\n            reliability_by_direction[(str(p["family_id"]), int(p["source_year"]), int(p["target_year"]))]["reliable"]\n            for proposals in proposals_by_event.values() for p in proposals\n        ),\n        "p3_every_surviving_proposal_meets_seed_floor": all(\n            float(p["probability"]) >= float(reliability_by_direction[(str(p["family_id"]), int(p["source_year"]), int(p["target_year"]))]["seed_floor"])\n            for proposals in proposals_by_event.values() for p in proposals\n        ),\n        "expansion_nonvacuous": len(assignments) > 0,\n'''

BEFORE_VERDICT = '''    verdict = (\n        "PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT"\n        if all(gates.values())\n        else "FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO"\n    )\n'''
AFTER_VERDICT = '''    verdict = (\n        "PASS_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT"\n        if all(gates.values())\n        else "FAIL_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_NO_GO"\n    )\n'''

BEFORE_DIAGNOSTICS = '''            "families_gaining_members": sum(bool(additions_by_family.get(index)) for index in range(len(families))),\n            "responsibility_median": float(np.median(max_responsibilities)) if max_responsibilities else None,\n'''
AFTER_DIAGNOSTICS = '''            "families_gaining_members": sum(bool(additions_by_family.get(index)) for index in range(len(families))),\n            "p3_crossfit_pretruth_sha256": crossfit_sha,\n            "p3_reliable_directions": sum(bool(r["reliable"]) for r in reliability_by_direction.values()),\n            "p3_unreliable_directions": p3_unreliable_directions,\n            "p3_seed_floor_rejections": p3_seed_floor_rejections,\n            "p3_surviving_preconflict_proposals": p3_surviving_proposals,\n            "responsibility_median": float(np.median(max_responsibilities)) if max_responsibilities else None,\n'''

BEFORE_OUTPUT = '''    (args.output / "crossyear_two_view_membership_p2_development.json").write_text(json.dumps(result, indent=2) + "\\n")\n    (args.output / "CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md").write_text(\n        "# OrbitTrace cross-year two-view membership P2 development\\n\\n"\n'''
AFTER_OUTPUT = '''    result["p3_crossfit_pretruth_sha256"] = crossfit_sha\n    (args.output / "crossfit_seed_floor_membership_p3_development.json").write_text(json.dumps(result, indent=2) + "\\n")\n    (args.output / "CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT.md").write_text(\n        "# OrbitTrace cross-fitted seed-floor membership P3 development\\n\\n"\n'''

BEFORE_PRINT = '''    print((args.output / "CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md").read_text(), flush=True)\n'''
AFTER_PRINT = '''    print((args.output / "CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT.md").read_text(), flush=True)\n'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P3 patch anchor {label} count={count}, expected 1")
    return text.replace(before, after, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_crossfit_seed_floor_patch.py CANONICAL_P2_V2.py OUTPUT.py")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_INPUT_SHA256:
        raise RuntimeError(f"unexpected canonical P2 input SHA256: {actual}")
    text = raw.decode("utf-8")
    transforms = (
        (BEFORE_CONSTANTS, AFTER_CONSTANTS, "constants"),
        (BEFORE_DIRECTION, AFTER_DIRECTION, "direction-features"),
        (BEFORE_FINAL_FIT, AFTER_FINAL_FIT, "crossfit-block"),
        (BEFORE_SCORING, AFTER_SCORING, "seed-floor-scoring"),
        (BEFORE_GATES, AFTER_GATES, "gates"),
        (BEFORE_VERDICT, AFTER_VERDICT, "verdict"),
        (BEFORE_PREFIX, AFTER_PREFIX, "classification"),
        (BEFORE_DIAGNOSTICS, AFTER_DIAGNOSTICS, "diagnostics"),
        (BEFORE_OUTPUT, AFTER_OUTPUT, "output"),
        (BEFORE_PRINT, AFTER_PRINT, "print"),
    )
    for before, after, label in transforms:
        text = replace_once(text, before, after, label)
    # No scientific target identifiers or known-shower labels may be introduced.
    if "OrbitTrace-April" in text or "target_id" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P3_CROSSFIT_PATCH_INPUT_SHA256={EXPECTED_INPUT_SHA256}")
    print(f"P3_CROSSFIT_PATCH_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P3_CROSSFIT_PATCH_SCOPE=five deterministic family folds + heldout seed floor only; P2 core/rank/features/final model/conflict/gates preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
