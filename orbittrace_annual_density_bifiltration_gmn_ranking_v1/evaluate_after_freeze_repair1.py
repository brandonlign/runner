#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

ORIGINAL_BLOB = "31cce36ba7b43f09451f1a556ef46f52277cab16"
MARKER = '            bif_all = list(s["bifiltration_candidates"])\n'
PATCH = '''            bif_all = list(s["bifiltration_candidates"])
            _adapted_bif_all = []
            for _row in bif_all:
                req("family_hash" in _row and "event_ids" in _row, "bif adapter source fields missing")
                req("family_id" not in _row, "bif candidate unexpectedly already has family_id")
                _adapted = dict(_row)
                _adapted["family_id"] = "BIF/" + str(_row["family_hash"])
                req(_adapted["event_ids"] == _row["event_ids"], "bif adapter changed membership")
                _adapted_bif_all.append(_adapted)
            bif_all = _adapted_bif_all
'''


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def main() -> int:
    original = Path(__file__).with_name("evaluate_after_freeze.py")
    if not original.exists():
        raise RuntimeError(f"missing frozen evaluator: {original}")
    if git_blob(original) != ORIGINAL_BLOB:
        raise RuntimeError("frozen evaluator blob changed")
    source = original.read_text()
    if source.count(MARKER) != 1:
        raise RuntimeError("identity-adapter patch marker is not unique")
    patched = source.replace(MARKER, PATCH, 1)
    if hashlib.sha256(source.encode()).hexdigest() == hashlib.sha256(patched.encode()).hexdigest():
        raise RuntimeError("identity-adapter patch did not modify runtime source")
    ns = {"__name__": "__main__", "__file__": str(original)}
    exec(compile(patched, str(original), "exec"), ns, ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
