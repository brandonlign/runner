from __future__ import annotations

import hashlib
import json
from pathlib import Path

path = Path("orbittrace_recurrent_core_expansion_r1/run_schemafixed_execution.sh")
raw = path.read_bytes()
text = raw.decode()
needle = "PYTHONPATH=input/v3:orbittrace_wavelet_catalogue_v3:. \\\npython input/r1/run_development.py \\\n"
assert text.count(needle) == 1, text.count(needle)
insert = '''python orbittrace_recurrent_core_expansion_r1/optimize_exact_expansion.py input/r1/run_development.py
export R1_EQUIVALENCE_SAMPLE_FAMILIES="${R1_EQUIVALENCE_SAMPLE_FAMILIES:-8}"
export R1_EQUIVALENCE_ONLY="${R1_EQUIVALENCE_ONLY:-0}"
echo "R1_PERFORMANCE_PATCH_APPLIED equivalence_sample_families=$R1_EQUIVALENCE_SAMPLE_FAMILIES equivalence_only=$R1_EQUIVALENCE_ONLY"

'''
patched = text.replace(needle, insert + needle, 1)
assert patched != text
for token in (
    "D_SH(candidate, partner medoid) <= 0.05",
    "unchanged exact v8 multiplicity order",
    "no_threshold_search",
    "no_radius_search",
    "no_weight_search",
    "no_variant_search",
):
    assert token in patched, token
path.write_text(patched)

Path("output").mkdir(exist_ok=True)
record = {
    "wrapper_before_sha256": hashlib.sha256(raw).hexdigest(),
    "wrapper_after_sha256": hashlib.sha256(patched.encode()).hexdigest(),
    "insertion": "apply exact expansion optimizer immediately before frozen run_development execution",
    "scientific_rule_changed": False,
    "threshold_changed": False,
    "ranking_changed": False,
    "promotion_gate_changed": False,
}
Path("output/r1_performance_wrapper_patch.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps(record, indent=2, sort_keys=True))
