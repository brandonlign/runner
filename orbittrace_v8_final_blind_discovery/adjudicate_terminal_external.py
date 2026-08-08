#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FREEZE_COMMIT = "961f9e5c602679e1620fa20206cda794ca28660a"
V8_PARENT = "c9d6c44704013ba0c9430100e98a29a56b453304"
FREEZE_MANIFEST_SHA256 = "d6410ffea978f0fe88ac9a53795df63aabff99abf64484565b69e6d18204becb"
TERMINAL_JSON_SHA256 = "df21baba3713b7be5a99986ec15580d40c859c7ee75c82ad99be726b126d3bcf"
TERMINAL_VERDICT = "INCONCLUSIVE_V8_EXTERNAL_VALIDATION_NO_POWERED_PRISTINE_PANEL"
AMOR_VERDICT = "INCONCLUSIVE_V8_AMOR_EXTERNAL_POWER"
BLOCK = "BLOCK_STAGE_A_EXTERNAL_VALIDATION_INCONCLUSIVE"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    obj = json.loads(path.read_text())
    require(isinstance(obj, dict), f"not a JSON object: {path}")
    return obj


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--freeze-manifest", required=True, type=Path)
    p.add_argument("--freeze-audit", required=True, type=Path)
    p.add_argument("--terminal-result", required=True, type=Path)
    p.add_argument("--amor-result", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(sha256(a.freeze_manifest) == FREEZE_MANIFEST_SHA256, "freeze manifest SHA-256 mismatch")
    manifest = load(a.freeze_manifest)
    audit = load(a.freeze_audit)
    terminal = load(a.terminal_result)
    amor = load(a.amor_result)

    require(manifest.get("schema") == "orbittrace-v8-final-blind-freeze-v1", "freeze schema changed")
    require(manifest.get("freeze_commit") == FREEZE_COMMIT, "freeze commit changed")
    require(manifest.get("v8_parent_commit") == V8_PARENT, "v8 parent changed")
    require(manifest.get("catalogue_access") is False, "freeze audit accessed catalogue")
    require(manifest.get("target_region_data_access") is False, "freeze audit accessed target region")
    require(manifest.get("withheld_reference_access") is False, "freeze audit accessed withheld reference")
    require(manifest.get("stage_a_execution_request_present") is False, "Stage A request already present in freeze")
    require(manifest.get("stage_b_execution_request_present") is False, "Stage B request already present in freeze")
    require(audit.get("verdict") == "PASS_V8_FINAL_BLIND_SOURCE_AUDIT", "freeze source audit no longer passes")

    require(sha256(a.terminal_result) == TERMINAL_JSON_SHA256, "terminal result SHA-256 mismatch")
    require(terminal.get("verdict") == TERMINAL_VERDICT, "terminal verdict changed")
    require(terminal.get("powered_external_verdict_obtained") is False, "powered external verdict unexpectedly obtained")
    require(terminal.get("powered_external_pass_obtained") is False, "powered external pass unexpectedly obtained")
    require(terminal.get("powered_external_scientific_fail_obtained") is False, "powered external scientific failure unexpectedly obtained")
    require(terminal.get("direct_v8_external_test_powered") is False, "direct v8 external test unexpectedly powered")
    require(terminal.get("data_availability_or_pristine_panel_limitation_reached") is True, "terminal limitation flag changed")
    require(terminal.get("v8_method_changed_from_external_results") is False, "v8 changed from external outcomes")
    require(terminal.get("external_power_floors_lowered") is False, "external power floors were lowered")
    require(terminal.get("new_detector_developed_from_external_results") is False, "new detector developed from external outcomes")
    require(terminal.get("successor_detector_authorized") is False, "successor unexpectedly authorized")
    require(terminal.get("target_reveal_authorized") is False, "target reveal unexpectedly authorized")
    require(terminal.get("orbittrace_target_information_access") is False, "terminal synthesis accessed OrbitTrace target")
    require(terminal.get("catalogue_or_web_access_this_synthesis") is False, "terminal synthesis accessed catalogue/web")
    require(terminal.get("scientific_value_access_this_synthesis") is False, "terminal synthesis accessed new scientific values")
    amor_record = terminal.get("external_record", {}).get("amor_1996_1998", {})
    require(amor_record.get("N") == 19 and amor_record.get("Q") == 0, "terminal AMOR N/Q changed")

    require(amor.get("verdict") == AMOR_VERDICT, "direct AMOR verdict changed")
    require(amor.get("family_count") == 19, "direct AMOR family count changed")
    require(amor.get("orbital_summary", {}).get("orbitally_corroborated_families") == 0, "direct AMOR Q changed")
    claim = str(amor.get("claim_boundary", ""))
    claim_lower = claim.lower()
    require("no source label or orbittrace target information entered" in claim_lower, "AMOR target-free claim changed")
    require("a powered pass authorizes a separately frozen target-free gmn discovery scan" in claim_lower, "pre-existing powered-pass authorization rule changed")

    stage_a_authorized = bool(terminal.get("powered_external_pass_obtained"))
    require(stage_a_authorized is False, "this adjudication is only valid for a non-pass terminal result")

    result = {
        "schema": "orbittrace-v8-terminal-external-stage-a-adjudication-v1",
        "verdict": BLOCK,
        "freeze_commit": FREEZE_COMMIT,
        "freeze_manifest_sha256": FREEZE_MANIFEST_SHA256,
        "terminal_external_verdict": TERMINAL_VERDICT,
        "terminal_result_sha256": TERMINAL_JSON_SHA256,
        "powered_external_pass_obtained": False,
        "powered_external_scientific_fail_obtained": False,
        "stage_a_scientifically_authorized": False,
        "stage_a_execution_request_may_be_created": False,
        "external_validation_authorization_may_be_issued": False,
        "stage_b_scientifically_authorized": False,
        "target_reveal_authorized": False,
        "successor_detector_authorized": False,
        "v8_method_changed": False,
        "external_power_floors_lowered": False,
        "catalogue_access_this_adjudication": False,
        "target_region_data_access_this_adjudication": False,
        "withheld_reference_access_this_adjudication": False,
        "mechanical_authorizer_nonempty_verdict_is_not_scientific_authorization": True,
        "continuation_rule": "Only a genuinely new independent dataset opportunity established outside the exhausted panel-selection sequence may start a new preregistered external-validation route before scientific access.",
    }
    (a.output / "terminal_external_stage_a_adjudication.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (a.output / "TERMINAL_EXTERNAL_STAGE_A_ADJUDICATION.md").write_text(
        "# OrbitTrace v8 terminal external-validation adjudication\n\n"
        f"**Verdict:** `{BLOCK}`\n\n"
        "The corrected terminal external synthesis obtained neither a powered pass nor a powered scientific failure. "
        "The pre-existing rule requires a powered pass before the separately frozen GMN blind discovery scan is authorized. "
        "Therefore Stage A remains blocked, Stage B remains blocked, v8 remains unchanged, and OrbitTrace remains blinded.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
