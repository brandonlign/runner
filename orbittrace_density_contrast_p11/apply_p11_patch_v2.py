#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("p11_patch_v1", HERE / "apply_p11_patch.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load P11 v1 patch")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# v2 changes only the source anchor around the scoring-loop prologue.  P4/P5
# inserted inherited counters between proposals_by_event/eps and the loop, so
# v1's broader anchor cannot match exact P10.  The scientific replacement is
# unchanged: retain positive features and initialize P11 pretruth counters
# immediately before the exact inherited direction-scoring loop.
m.SCORING_START_ANCHOR = '''    for index, direction in enumerate(directions, start=1):
        direction.pop("positive_features", None)
        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)
'''
m.SCORING_START_REPL = '''    p11_density_audits: list[dict[str, Any]] = []
    p11_density_rejected_p10 = 0
    p11_density_candidate_zero_denominator = 0
    for index, direction in enumerate(directions, start=1):
        p11_positive_features = np.asarray(direction.pop("positive_features"), dtype=np.float64)
        features = np.asarray(direction.pop("negative_features"), dtype=np.float64)
'''


def main() -> int:
    old = sys.argv
    sys.argv = [str(HERE / "apply_p11_patch.py"), *old[1:]]
    try:
        return int(m.main())
    finally:
        sys.argv = old


if __name__ == "__main__":
    raise SystemExit(main())
