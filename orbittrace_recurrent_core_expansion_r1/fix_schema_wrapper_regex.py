from __future__ import annotations

import hashlib
import json
from pathlib import Path

path = Path('orbittrace_recurrent_core_expansion_r1/run_schemafixed_execution.sh')
raw = path.read_bytes()
text = raw.decode()
lines = text.splitlines(keepends=True)

start_hits = [
    i for i, line in enumerate(lines)
    if line.strip().startswith('m=re.search(') and 'raw_header_positions' in line
]
end_hits = [
    i for i, line in enumerate(lines)
    if line.strip() == 'old_parser=after_hash[start:end]'
]
assert len(start_hits) == 1, start_hits
assert len(end_hits) == 1, end_hits
start_i = start_hits[0]
end_i = end_hits[0]
assert start_i < end_i
indent = lines[start_i][: len(lines[start_i]) - len(lines[start_i].lstrip())]
old_block = ''.join(lines[start_i : end_i + 1])

replacement = [
    "source_lines=after_hash.splitlines(keepends=True)",
    "function_hits=[i for i,line in enumerate(source_lines) if line.startswith('def raw_header_positions(')]",
    "assert len(function_hits)==1, f'raw_header_positions definitions: {function_hits}'",
    "function_i=function_hits[0]",
    "next_hits=[i for i in range(function_i+1,len(source_lines)) if source_lines[i].startswith('def ')]",
    "assert next_hits, 'next top-level function after raw_header_positions() not found'",
    "next_i=next_hits[0]",
    "start=sum(len(line) for line in source_lines[:function_i])",
    "end=sum(len(line) for line in source_lines[:next_i])",
    "old_parser=after_hash[start:end]",
]
new_block = ''.join(indent + line + '\n' for line in replacement)
assert old_block != new_block
patched_lines = lines[:start_i] + [new_block] + lines[end_i + 1 :]
patched = ''.join(patched_lines)
assert patched != text

# This edits only the execution helper's way of locating a function in the
# SHA-pinned scientific source. It does not edit the frozen scientific source,
# scientific rule, thresholds, ranking, target exclusion, or promotion gates.
path.write_text(patched)
Path('output').mkdir(exist_ok=True)
record = {
    'repair_scope': 'execution-wrapper source-function boundary detection only',
    'boundary_method': 'unique top-level def raw_header_positions line through next top-level def line',
    'original_wrapper_sha256': hashlib.sha256(raw).hexdigest(),
    'patched_wrapper_sha256': hashlib.sha256(patched.encode()).hexdigest(),
    'old_boundary_block_sha256': hashlib.sha256(old_block.encode()).hexdigest(),
    'new_boundary_block_sha256': hashlib.sha256(new_block.encode()).hexdigest(),
    'scientific_source_changed': False,
    'scientific_rule_changed': False,
    'promotion_gate_changed': False,
}
Path('output/r1_wrapper_regex_repair.json').write_text(
    json.dumps(record, indent=2, sort_keys=True) + '\n'
)
print(json.dumps(record, indent=2, sort_keys=True))
