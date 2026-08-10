#!/usr/bin/env python3
"""Pre-result strict-group scientific adapter for eventwise P12 calibration.

The initial committed lab source accidentally restricted supervised event rows to already-qualified
hard cores. Before any execution/result, this adapter changes that one scientific rule to include
every hard fragment with any eligible best-known shower, so nonqualified near-miss fragments of a
shower are grouped with that shower exactly as required by the post-#840 standard.

It also applies the transport-only P12 gzip/decompressed-hash compatibility already documented in
`run_artifact_hash_compatible.py`. No feature, model parameter, threshold, gate, candidate, ranking,
or dataset changes.
"""
from __future__ import annotations

import gzip
import hashlib
import types
from pathlib import Path

SOURCE = Path(__file__).with_name("run_lab.py")
text = SOURCE.read_text()
old_rule = '        if not truth["positive"] or truth["best_label"] is None:\n'
new_rule = '        if truth["best_label"] is None:\n'
old_comment = "    # Build supervised event examples only from already-qualified hard cores. The family/shower\n"
new_comment = "    # Build supervised event examples from every hard fragment with an eligible best-known shower. The family/shower\n"
old_description = '            "training_family_rule": "only hard cores qualified on GMN; no shower identity enters features",\n'
new_description = '            "training_family_rule": "all hard fragments with an eligible best-known GMN shower; no shower identity enters features",\n'

for old, new, label in (
    (old_rule, new_rule, "supervised-family rule"),
    (old_comment, new_comment, "supervised-family comment"),
    (old_description, new_description, "serialized training rule"),
):
    if text.count(old) != 1:
        raise RuntimeError(f"expected exactly one {label} replacement, found {text.count(old)}")
    text = text.replace(old, new)

module = types.ModuleType("orbittrace_urc_eventwise_p12_calibration_strict_group")
module.__file__ = str(SOURCE)
exec(compile(text, str(SOURCE), "exec"), module.__dict__)

_original_sha = module.sha


def _compatible_sha(path: Path) -> str:
    if path.name == "p12_decisions_pretruth.json.gz":
        return hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()
    return _original_sha(path)


module.sha = _compatible_sha

if __name__ == "__main__":
    raise SystemExit(module.main())
