#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import runpy
import sys
from pathlib import Path

FROZEN_RUNNER_GIT_BLOB = "bc03d41a6b6442c589bbb6f219ee7b7c8feb2bd7"
REPLACEMENTS = (
    ('e["sun_lon"]', 'e["lon"]'),
    ('e["ecl_lat"]', 'e["lat"]'),
)


def main() -> int:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--frozen-runner", type=Path, required=True)
    ns, rest = p.parse_known_args()

    raw = ns.frozen_runner.read_text()
    repaired = raw
    for old, new in REPLACEMENTS:
        count = repaired.count(old)
        if count != 1:
            raise RuntimeError(f"authorized alias literal {old!r} occurs {count} times, expected exactly once")
        repaired = repaired.replace(old, new, 1)

    if repaired == raw:
        raise RuntimeError("field-alias repair made no change")
    for old, _new in REPLACEMENTS:
        if old in repaired:
            raise RuntimeError(f"authorized old alias survived repair: {old}")

    out = Path("/tmp/orbittrace_shared_drift_bic_v1_field_alias_repaired.py")
    out.write_text(repaired)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"FIELD_ALIAS_REPAIR_RUNTIME_SHA256={digest}", flush=True)

    sys.argv = [str(out), *rest]
    runpy.run_path(str(out), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
