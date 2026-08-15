#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import runpy
import sys
from pathlib import Path

STABILITY_OLD = '''    successor_labels = eom_labels(tree, exposure_stability)\n    successor_nodes = selected_eom_nodes(tree, exposure_stability)\n'''
STABILITY_NEW = '''    successor_nodes = selected_eom_nodes(tree, dict(exposure_stability))\n    successor_labels = eom_labels(tree, dict(exposure_stability))\n'''

MAP_OLD = '''    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)\n    req(positive == list(range(len(nodes))), "compact exposure-LR labels do not map to selected nodes")\n    out: list[dict[str, Any]] = []\n    for lab, node in enumerate(nodes):\n'''
MAP_NEW = '''    req(tuple(nodes) == tuple(sorted(nodes)), "EOM selected nodes are not in HDBSCAN cluster-map order")\n    positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)\n    req(all(0 <= lab < len(nodes) for lab in positive), "authoritative HDBSCAN label index is outside selected-node map")\n    out: list[dict[str, Any]] = []\n    for lab in positive:\n        node = nodes[lab]\n'''


def replace_exact(raw: str, old: str, new: str, name: str) -> str:
    count = raw.count(old)
    if count != 1:
        raise RuntimeError(f"authorized {name} fragment occurs {count} times, expected exactly once")
    out = raw.replace(old, new, 1)
    if out == raw or old in out:
        raise RuntimeError(f"authorized {name} repair did not apply exactly")
    return out


def main() -> int:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--frozen-runner", type=Path, required=True)
    ns, rest = p.parse_known_args()

    raw = ns.frozen_runner.read_text()
    repaired = replace_exact(raw, STABILITY_OLD, STABILITY_NEW, "stability-copy")
    repaired = replace_exact(repaired, MAP_OLD, MAP_NEW, "HDBSCAN label-map")

    out = Path("/tmp/orbittrace_exposure_lr_v1_label_map_repaired.py")
    out.write_text(repaired)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"LABEL_MAP_REPAIR_RUNTIME_SHA256={digest}", flush=True)

    sys.argv = [str(out), *rest]
    runpy.run_path(str(out), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
