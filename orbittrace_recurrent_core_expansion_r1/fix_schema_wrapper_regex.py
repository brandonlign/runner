from __future__ import annotations

import hashlib
import json
from pathlib import Path

path = Path('orbittrace_recurrent_core_expansion_r1/run_schemafixed_execution.sh')
raw = path.read_bytes()
text = raw.decode()

old_header = "r'(?m)^def raw_header_positions\\\\(text[^\\\\n]*\\\\):\\\\n'"
new_header = "r'(?m)^def raw_header_positions\\(text[^\\n]*\\):\\n'"
old_next = "r'(?m)^def [A-Za-z_][A-Za-z0-9_]*\\\\('"
new_next = "r'(?m)^def [A-Za-z_][A-Za-z0-9_]*\\('"

assert text.count(old_header) == 1, text.count(old_header)
assert text.count(old_next) == 1, text.count(old_next)
patched = text.replace(old_header, new_header, 1).replace(old_next, new_next, 1)
assert patched != text

path.write_text(patched)
Path('output').mkdir(exist_ok=True)
record = {
    'repair_scope': 'two execution-wrapper regex literals only',
    'original_wrapper_sha256': hashlib.sha256(raw).hexdigest(),
    'patched_wrapper_sha256': hashlib.sha256(patched.encode()).hexdigest(),
    'scientific_source_changed': False,
    'scientific_rule_changed': False,
    'promotion_gate_changed': False,
}
Path('output/r1_wrapper_regex_repair.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps(record, indent=2, sort_keys=True))
