#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED = {
    2017: "ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc",
    2019: "301a711e4de43566ba434f2d4a94fc38a85714a33dcee45e26cb19340101ea43",
}

OLD_GATE_FIELD = '        "gates": parser_gates,\n'
NEW_GATE_FIELD = '''        "fixed4_parser_gates": parser_gates,\n        "fixed4_supported_native_code_gate_report_only": bool(parser_gates["at_least_30_supported_native_codes"]),\n        "gates": {name: passed for name, passed in parser_gates.items() if name != "at_least_30_supported_native_codes"},\n'''


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def adapt(year: int, source: Path, output: Path) -> str:
    raw = source.read_bytes()
    require(sha(raw) == EXPECTED[year], f"frozen SonotaCo {year} parser hash changed")
    text = raw.decode("utf-8")
    require(text.count(OLD_GATE_FIELD) == 1, f"{year} audit gate field anchor changed")
    old_if = '    if not all(parser_gates.values()):\n'
    require(text.count(old_if) == 1, f"{year} parser gate execution anchor changed")
    old_error = f'        raise RuntimeError(f"frozen {year} parser gate failed: {{parser_gates}}")\n'
    require(text.count(old_error) == 1, f"{year} parser gate error anchor changed")
    old_id = f'            "id": f"SNM{year}:{{row_index}}",\n'
    new_id = f'            "id": f"{year}:SNM{year}:{{row_index}}",\n'
    require(text.count(old_id) == 1, f"{year} deterministic event-ID anchor changed")

    patched = text.replace(OLD_GATE_FIELD, NEW_GATE_FIELD, 1)
    patched = patched.replace(old_if, '    if not all(audit_record["gates"].values()):\n', 1)
    patched = patched.replace(
        old_error,
        f'        raise RuntimeError(f"catalogue-v6 {year} transport gate failed: {{audit_record[\'gates\']}}")\n',
        1,
    )
    patched = patched.replace(old_id, new_id, 1)

    # Exact scientific row transform, quality cuts, mapping, target exclusion,
    # background definition and returned geometry remain inherited byte-for-byte.
    # Two preregistered transport-only adaptations are made before any execution:
    # (1) the obsolete fixed4-specific >=30 native codes with >=20 events/code gate
    # is report-only for catalogue v6; (2) event IDs receive a deterministic
    # leading four-digit year so the exact inherited v8 evaluator's immutable
    # year-from-ID convention remains valid on SonotaCo.
    require('if BLIND_SOLAR_MIN <= sol <= BLIND_SOLAR_MAX:' in patched, "blind gate missing")
    require('# Critical blindness boundary: no label token or feature is read before this exclusion.' in patched, "blind-order marker missing")
    require('ncam is not None and ncam >= 2.0' in patched, "quality cut changed")
    require('if base.is_esv(event):' in patched, "ESV background exclusion changed")
    require('"at_least_10000_sporadic_after_esv_exclusion"' in patched, "background gate changed")
    require('"at_least_30_distinct_labeled_showers"' in patched, "mapped-shower gate changed")
    require(patched.count('fixed4_supported_native_code_gate_report_only') == 1, "report-only record missing")
    require(patched.count('if name != "at_least_30_supported_native_codes"') == 1, "single excluded fixed4 gate not proven")
    require(patched.count(new_id) == 1 and old_id not in patched, "deterministic year-prefix ID adaptation failed")
    compile(patched, str(output), "exec")
    output.write_text(patched, encoding="utf-8")
    return sha(output.read_bytes())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--parser-2017", required=True, type=Path)
    p.add_argument("--parser-2019", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for year, source in ((2017, args.parser_2017), (2019, args.parser_2019)):
        out = args.output_dir / f"run_sonotaco_{year}_catalogue_v6_parser.py"
        results[year] = adapt(year, source, out)
        print(f"PASS_CATALOGUE_V6_PARSER_ADAPT year={year} sha256={results[year]}", flush=True)
    (args.output_dir / "catalogue_v6_parser_sha256.txt").write_text(
        "".join(f"{digest}  run_sonotaco_{year}_catalogue_v6_parser.py\n" for year, digest in sorted(results.items()))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
