#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import runpy
import sys
from pathlib import Path

OLD = '''    successor_labels = eom_labels(tree, exposure_stability)\n    successor_nodes = selected_eom_nodes(tree, exposure_stability)\n'''
NEW = '''    successor_nodes = selected_eom_nodes(tree, dict(exposure_stability))\n    successor_labels = eom_labels(tree, dict(exposure_stability))\n'''


def main() -> int:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--frozen-runner", type=Path, required=True)
    ns, rest = p.parse_known_args()

    raw = ns.frozen_runner.read_text()
    count = raw.count(OLD)
    if count != 1:
        raise RuntimeError(f"authorized stability call sequence occurs {count} times, expected exactly once")
    repaired = raw.replace(OLD, NEW, 1)
    if repaired == raw or OLD in repaired:
        raise RuntimeError("stability-copy repair did not apply exactly")

    out = Path("/tmp/orbittrace_exposure_lr_v1_stability_copy_repaired.py")
    out.write_text(repaired)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"STABILITY_COPY_REPAIR_RUNTIME_SHA256={digest}", flush=True)

    sys.argv = [str(out), *rest]
    runpy.run_path(str(out), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
