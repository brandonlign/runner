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

# Repair B: select the raw header by the SAME textual marker rule used by the
# approved schema-only audit. Case is preserved for field extraction, q != Q.
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

# Repair C: restore the event-ID mapping omitted by the first replacement
# parser. The approved raw schema has `Unique trajectory` as field 0 after the
# leading comment marker is removed. No event-row value is inspected here.
id_anchor_hits = [
    i for i, line in enumerate(lines)
    if line.strip() == '"q": exact("q"),'
]
assert len(id_anchor_hits) == 1, id_anchor_hits
id_anchor_i = id_anchor_hits[0]
id_indent = lines[id_anchor_i][: len(lines[id_anchor_i]) - len(lines[id_anchor_i].lstrip())]
id_line = id_indent + '"id": exact("Unique trajectory"),\n'
assert all('"id": exact("Unique trajectory")' not in line for line in lines)
lines = lines[:id_anchor_i] + [id_line] + lines[id_anchor_i:]
patched = ''.join(lines)

# Repair D: schema-only preflight on the SAME month already used by the
# approved no-row schema audit. It also statically enumerates every literal
# `positions["..."]` key used by parse_target_excluded_orbits, guaranteeing the
# replacement parser supplies the complete interface before the expensive run.
needle = "PYTHONPATH=input/v3:orbittrace_wavelet_catalogue_v3:. \\\npython input/r1/run_development.py \\\n"
assert patched.count(needle) == 1, patched.count(needle)
preflight = r'''PYTHONPATH=input/v3:orbittrace_wavelet_catalogue_v3:. python - <<'PY'
import ast
import runpy
from pathlib import Path
from gmn_python_api import data_directory as dd

source_path = Path('input/r1/run_development.py')
ns = runpy.run_path(str(source_path), run_name='r1_schema_preflight')
text = dd.get_monthly_file_content_by_date('2022-01')
fields, positions = ns['raw_header_positions'](text)
assert fields[0] == 'Unique trajectory', fields[0]
assert positions['id'] == 0, positions
assert positions['q'] == 37, positions
assert fields[43] == 'Q', fields[43]
assert positions['q'] != 43

tree = ast.parse(source_path.read_text())
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'parse_target_excluded_orbits']
assert len(funcs) == 1
required = set()
for node in ast.walk(funcs[0]):
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == 'positions':
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            required.add(key.value)
missing = sorted(required - set(positions))
assert not missing, f'missing raw-header position keys: {missing}; required={sorted(required)}; supplied={sorted(positions)}'
print('R1_REQUIRED_POSITION_KEYS', sorted(required))
print('PASS_R1_SCHEMA_PARSER_PREFLIGHT')
PY

'''
patched = patched.replace(needle, preflight + needle, 1)
assert patched != text

# Everything above changes only execution plumbing around the SHA-pinned R1
# source. Scientific source bytes are restored later from the frozen payload;
# scientific thresholds, ranking, target exclusion, and promotion gates stay
# unchanged.
path.write_text(patched)
Path('output').mkdir(exist_ok=True)
record = {
    'repair_scope': 'execution-wrapper source boundary + audited header selection + event-ID interface + static schema preflight',
    'boundary_method': 'unique top-level def raw_header_positions line through next top-level def line',
    'header_selection_method': 'same textual marker rule as approved GMN schema-only audit',
    'event_id_field': 'Unique trajectory',
    'event_id_expected_index': 0,
    'preflight_month': '2022-01',
    'preflight_event_rows_parsed': False,
    'preflight_static_required_position_key_check': True,
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
