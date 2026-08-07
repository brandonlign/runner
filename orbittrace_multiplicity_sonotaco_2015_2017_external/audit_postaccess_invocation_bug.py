#!/usr/bin/env python3
"""Source-only audit of the post-archive-access SonotaCo parser invocation failure."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

RUNNER = Path('orbittrace_multiplicity_sonotaco_2015_2017_external/run_external_validation.py')
TRANSPORT = Path('input/parser_transport/sonotaco_2015_2017_parser_transport.json')
PARSERS = {
    2015: Path('input/parser_transport/run_sonotaco_2015_transport_parser.py'),
    2017: Path('input/parser_transport/run_sonotaco_2017_transport_parser.py'),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parser_signature(path: Path, name: str) -> list[str]:
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return [arg.arg for arg in node.args.args]
    raise RuntimeError(f'missing {name}')


def main() -> int:
    transport = json.loads(TRANSPORT.read_text())
    assert transport['verdict'] == 'PASS_SONOTACO_2015_2017_SOURCE_ONLY_PARSER_TRANSPORT'
    signatures = {}
    for year, path in PARSERS.items():
        assert sha(path) == transport['years'][str(year)]['source_sha256']
        signature = parser_signature(path, f'parse_sonotaco_{year}_events')
        assert signature == ['archive', 'audit_path', 'base'], (year, signature)
        signatures[str(year)] = signature

    runner_text = RUNNER.read_text()
    frozen_call = 'parsed = function(archive_path, base, mapping_audit)'
    corrected_call = 'parsed = function(archive_path, mapping_audit, base)'
    assert runner_text.count(frozen_call) == 1
    assert corrected_call not in runner_text

    result = {
        'verdict': 'PASS_POSTACCESS_INVOCATION_BUG_SOURCE_AUDIT',
        'catalogue_access': False,
        'archive_content_access': False,
        'target_information_access': False,
        'runner_sha256': sha(RUNNER),
        'transport_manifest_sha256': sha(TRANSPORT),
        'parser_signatures': signatures,
        'frozen_call': frozen_call,
        'corrected_call': corrected_call,
        'diagnosis': 'argument_order_mismatch',
        'mechanical_repair_lines': 1,
        'scientific_method_change': False,
    }
    Path('output').mkdir(exist_ok=True)
    Path('output/postaccess_invocation_bug_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
