from __future__ import annotations

import hashlib
import json
from pathlib import Path

path = Path('orbittrace_recurrent_core_expansion_r1/run_schemafixed_execution.sh')
raw = path.read_bytes()
text = raw.decode()
lines = text.splitlines(keepends=True)

header_hits = [
    i for i, line in enumerate(lines)
    if line.strip().startswith('m=re.search(') and 'raw_header_positions' in line
]
next_hits = [
    i for i, line in enumerate(lines)
    if line.strip().startswith('n=re.search(') and 'A-Za-z_' in line
]
assert len(header_hits) == 1, header_hits
assert len(next_hits) == 1, next_hits

old_header_line = lines[header_hits[0]].rstrip('\n')
old_next_line = lines[next_hits[0]].rstrip('\n')
correct_header_line = "m=re.search(r'(?m)^def raw_header_positions\\(text[^\\n]*\\):\\n',after_hash)"
correct_next_line = "n=re.search(r'(?m)^def [A-Za-z_][A-Za-z0-9_]*\\(',after_hash[m.end():])"

assert old_header_line != correct_header_line
assert old_next_line != correct_next_line
lines[header_hits[0]] = correct_header_line + '\n'
lines[next_hits[0]] = correct_next_line + '\n'
patched = ''.join(lines)
assert patched != text

# The repair is limited to the two wrapper lines above. The frozen R1 scientific
# source is restored later from its SHA-pinned payload and is not edited here.
path.write_text(patched)
Path('output').mkdir(exist_ok=True)
record = {
    'repair_scope': 'two execution-wrapper regex source lines only',
    'original_wrapper_sha256': hashlib.sha256(raw).hexdigest(),
    'patched_wrapper_sha256': hashlib.sha256(patched.encode()).hexdigest(),
    'old_header_line': old_header_line,
    'new_header_line': correct_header_line,
    'old_next_line': old_next_line,
    'new_next_line': correct_next_line,
    'scientific_source_changed': False,
    'scientific_rule_changed': False,
    'promotion_gate_changed': False,
}
Path('output/r1_wrapper_regex_repair.json').write_text(
    json.dumps(record, indent=2, sort_keys=True) + '\n'
)
print(json.dumps(record, indent=2, sort_keys=True))
