from __future__ import annotations

import hashlib
import json
from pathlib import Path

path = Path('orbittrace_recurrent_core_expansion_r1/run_schemafixed_execution.sh')
raw = path.read_bytes()
text = raw.decode()
lines = text.splitlines(keepends=True)

# Repair A: remove regex dependence from locating the frozen source function.
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
old_boundary_block = ''.join(lines[start_i : end_i + 1])

boundary_replacement = [
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
new_boundary_block = ''.join(indent + line + '\n' for line in boundary_replacement)
lines = lines[:start_i] + [new_boundary_block] + lines[end_i + 1 :]

# Repair B: make the replacement parser select the raw header by the SAME
# textual marker rule used by the approved schema-only audit, rather than an
# exact line prefix. Case is preserved for field extraction, so q != Q.
selection_hits = [
    i for i, line in enumerate(lines)
    if 'schema_lines = [line for line in text.splitlines() if line.startswith("# Unique trajectory;")]' in line
]
assert len(selection_hits) == 1, selection_hits
selection_i = selection_hits[0]
selection_indent = lines[selection_i][: len(lines[selection_i]) - len(lines[selection_i].lstrip())]
old_selection_line = lines[selection_i]
selection_replacement = [
    'known_markers = ("unique trajectory identifier", "sol lon", "solar longitude", "lamgeo", "betgeo", "vgeo")',
    'orbit_terms = ("perihelion", "eccentric", "inclination", "argument", "ascending", "node", "semimajor", "semi-major", "q au", "omega")',
    'schema_lines = []',
    'for raw in text.splitlines():',
    '    low = raw.lower()',
    '    if sum(marker in low for marker in known_markers) >= 2 or (',
    '        any(marker in low for marker in known_markers)',
    '        and any(term in low for term in orbit_terms)',
    '    ):',
    '        candidate = " ".join(raw.strip().lstrip("\\ufeff").split())',
    '        if candidate:',
    '            schema_lines.append(candidate)',
    'schema_lines = sorted(set(schema_lines))',
]
new_selection_block = ''.join(selection_indent + line + '\n' for line in selection_replacement)
lines = lines[:selection_i] + [new_selection_block] + lines[selection_i + 1 :]
patched = ''.join(lines)

# Repair C: add a schema-only preflight on the SAME month already used by the
# approved no-row schema audit. This calls only raw_header_positions(); it does
# not parse an event row, label, target-region event, or scientific score.
needle = "PYTHONPATH=input/v3:orbittrace_wavelet_catalogue_v3:. \\\npython input/r1/run_development.py \\\n"
assert patched.count(needle) == 1, patched.count(needle)
preflight = r'''PYTHONPATH=input/v3:orbittrace_wavelet_catalogue_v3:. python - <<'PY'
import runpy
from gmn_python_api import data_directory as dd
ns = runpy.run_path('input/r1/run_development.py', run_name='r1_schema_preflight')
text = dd.get_monthly_file_content_by_date('2022-01')
fields, positions = ns['raw_header_positions'](text)
assert positions['q'] == 37, positions
assert fields[43] == 'Q', fields[43]
assert positions['q'] != 43
print('PASS_R1_SCHEMA_PARSER_PREFLIGHT')
PY

'''
patched = patched.replace(needle, preflight + needle, 1)
assert patched != text

# Everything above changes only execution plumbing around the SHA-pinned R1
# source. Scientific source bytes are restored later from the frozen payload;
# the only source edits remain the already-declared comparator-provenance fix
# and exact-case schema parser repair, both checked reversible there.
path.write_text(patched)
Path('output').mkdir(exist_ok=True)
record = {
    'repair_scope': 'execution-wrapper source boundary + audited schema-header selection + schema-only preflight',
    'boundary_method': 'unique top-level def raw_header_positions line through next top-level def line',
    'header_selection_method': 'same textual marker rule as approved GMN schema-only audit',
    'preflight_month': '2022-01',
    'preflight_event_rows_parsed': False,
    'original_wrapper_sha256': hashlib.sha256(raw).hexdigest(),
    'patched_wrapper_sha256': hashlib.sha256(patched.encode()).hexdigest(),
    'old_boundary_block_sha256': hashlib.sha256(old_boundary_block.encode()).hexdigest(),
    'new_boundary_block_sha256': hashlib.sha256(new_boundary_block.encode()).hexdigest(),
    'old_selection_line_sha256': hashlib.sha256(old_selection_line.encode()).hexdigest(),
    'new_selection_block_sha256': hashlib.sha256(new_selection_block.encode()).hexdigest(),
    'scientific_source_changed': False,
    'scientific_rule_changed': False,
    'promotion_gate_changed': False,
}
Path('output/r1_wrapper_regex_repair.json').write_text(
    json.dumps(record, indent=2, sort_keys=True) + '\n'
)
print(json.dumps(record, indent=2, sort_keys=True))
