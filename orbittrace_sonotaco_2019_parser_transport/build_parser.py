#!/usr/bin/env python3
"""Source-only transport of the frozen SonotaCo 2017 parser to 2019."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

SOURCE = Path('input/source/run_sonotaco_2017_transport_parser.py')
OUT = Path('output')
EXPECTED_SOURCE_SHA = 'ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc'


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    OUT.mkdir(exist_ok=True)
    source_bytes = SOURCE.read_bytes()
    assert sha(source_bytes) == EXPECTED_SOURCE_SHA
    source = source_bytes.decode('utf-8')

    # Mechanical year transport only: four-digit year and SNMv3 two-digit member prefix.
    transported = source.replace('2017', '2019').replace('017a', '019a')
    before = source.splitlines()
    after = transported.splitlines()
    assert len(before) == len(after)
    changed = [(i + 1, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed
    for _, a, b in changed:
        expected = a.replace('2017', '2019').replace('017a', '019a')
        assert expected == b
        assert ('2017' in a) or ('017a' in a)
        assert ('2019' in b) or ('019a' in b)

    out_parser = OUT / 'run_sonotaco_2019_transport_parser.py'
    out_parser.write_text(transported)
    compile(transported, str(out_parser), 'exec')

    tree = ast.parse(transported)
    year = None
    member = None
    function_args = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == 'YEAR' and isinstance(node.value, ast.Constant):
                    year = node.value.value
                if isinstance(t, ast.Name) and t.id == 'MEMBER' and isinstance(node.value, ast.Constant):
                    member = node.value.value
        if isinstance(node, ast.FunctionDef) and node.name == 'parse_sonotaco_2019_events':
            function_args = [a.arg for a in node.args.args]
    assert year == 2019
    assert member == '019a/_U2_20190101_S.csv'
    assert function_args == ['archive', 'audit_path', 'base']

    # Static blindness-order guard inherited exactly from source.
    blind_marker = '# Critical blindness boundary: no label token or feature is read before this exclusion.'
    blind_idx = transported.index(blind_marker)
    label_idx = transported.index('token = row[index["shower"]]', blind_idx)
    sol_idx = transported.index('if BLIND_SOLAR_MIN <= sol <= BLIND_SOLAR_MAX:', blind_idx)
    assert blind_idx < sol_idx < label_idx

    result = {
        'verdict': 'PASS_SONOTACO_2019_SOURCE_ONLY_PARSER_TRANSPORT',
        'catalogue_access': False,
        'shower_label_access': False,
        'scientific_score_access': False,
        'target_information_access': False,
        'ancestor_year': 2017,
        'ancestor_sha256': EXPECTED_SOURCE_SHA,
        'year': 2019,
        'member': member,
        'source_sha256': sha(out_parser.read_bytes()),
        'changed_line_count': len(changed),
        'year_identifier_only_line_changes': True,
        'function_args': function_args,
        'blind_interval_removed_before_label_access': True,
        'parser_integrity_gates_unchanged': True,
    }
    (OUT / 'sonotaco_2019_parser_transport.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
