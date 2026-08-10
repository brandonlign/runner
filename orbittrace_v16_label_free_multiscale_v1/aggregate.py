#!/usr/bin/env python3
"""Apply the preregistered all-panel v16 decision rule."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--panel-2020-2021", type=Path, required=True)
    p.add_argument("--panel-2022-2023", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def main() -> int:
    a = parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    first = load(a.panel_2020_2021)
    second = load(a.panel_2022_2023)
    require(first["years"] == [2020, 2021], "first panel identity changed")
    require(second["years"] == [2022, 2023], "second panel identity changed")
    panel_pass = {
        "2020_2021": first["verdict"] == "PASS_V16_LABEL_FREE_MULTISCALE_PANEL",
        "2022_2023": second["verdict"] == "PASS_V16_LABEL_FREE_MULTISCALE_PANEL",
    }
    verdict = (
        "PASS_LABEL_FREE_MULTISCALE_CONSENSUS_V16_TARGET_EXCLUDED_DEVELOPMENT"
        if all(panel_pass.values())
        else "FAIL_LABEL_FREE_MULTISCALE_CONSENSUS_V16_TARGET_EXCLUDED_DEVELOPMENT"
    )
    result = {
        "verdict": verdict,
        "method": "label-free v6 recurrent-family construction + v15 multiscale-consensus multiplicity",
        "panel_pass": panel_pass,
        "panels": {"2020_2021": first, "2022_2023": second},
        "all_panels_required": True,
        "no_panel_selection": True,
        "sonotaco_access": False,
        "maarsy_access": False,
        "target_information_access": False,
        "claim_boundary": (
            "A pass freezes v16 as the first label-free survey-portable successor candidate. "
            "It does not constitute external validation, literature superiority, or target discovery."
        ),
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
