#!/usr/bin/env python3
from __future__ import annotations
import ast, base64, gzip, hashlib, json, re
from pathlib import Path

parts = sorted(Path('orbittrace_fixed4_support_wrapper_development/source_parts').glob('part*.b64'))
if len(parts) != 4:
    raise RuntimeError(f'expected 4 frozen source parts, got {len(parts)}')
encoded = ''.join(p.read_text().strip() for p in parts)
source = gzip.decompress(base64.b64decode(encoded)).decode('utf-8')
ast.parse(source)

terms = ('mag', 'magnitude', 'height', 'begin', 'end', 'peak', 'orbit', 'peri', 'node', 'incl', 'ecc', "['q']", '"q"')
lines = source.splitlines()
matches = []
for i, line in enumerate(lines, 1):
    low = line.lower()
    if any(t.lower() in low for t in terms):
        matches.append({'line': i, 'text': line.strip()[:500]})

# Extract string literal keys from subscripts/dicts for a schema-oriented audit without executing the module.
tree = ast.parse(source)
keys = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        v = node.value
        if len(v) <= 80:
            keys.add(v)
interesting = sorted(k for k in keys if any(t in k.lower() for t in ('mag','height','begin','end','peak','orbit','peri','node','incl','ecc','q','sol','vg')))

out = {
    'verdict': 'PASS_FROZEN_GMN_OBSERVABLE_SCHEMA_SOURCE_AUDIT_V1',
    'scientific_data_accessed': False,
    'source_parts': [p.name for p in parts],
    'decoded_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
    'decoded_source_lines': len(lines),
    'interesting_string_literals': interesting,
    'matching_source_lines': matches,
}
Path('output').mkdir(exist_ok=True)
Path('output/GMN_OBSERVABLE_SCHEMA_SOURCE_AUDIT_V1.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
print(json.dumps(out, indent=2, sort_keys=True))
