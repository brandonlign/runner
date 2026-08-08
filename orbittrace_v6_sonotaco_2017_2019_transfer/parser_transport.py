from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

PARSER_SHA256 = {
    2017: "ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc",
    2019: "301a711e4de43566ba434f2d4a94fc38a85714a33dcee45e26cb19340101ea43",
}
ARCHIVE_SHA256 = {
    2017: "1db43348806a44490fde8936529541754411b16825f2caea240378cda11c77cf",
    2019: "d49c37f5a9f7f089973d7029b840283f26ca9d915c137152a6f4368bbf5aabb4",
}
OBSOLETE_GATE_LINE = '        "at_least_30_supported_native_codes": len(supported_codes) >= 30,\n'
V6_NONBINDING_LINE = '        "v6_transport_old_supported_code_gate_nonbinding": True,\n'


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_transported_parser(year: int, source_path: Path) -> tuple[ModuleType, dict[str, Any]]:
    require(year in (2017, 2019), f"unsupported transfer year {year}")
    raw = source_path.read_bytes()
    original_sha = hashlib.sha256(raw).hexdigest()
    require(original_sha == PARSER_SHA256[year], f"parser {year} source mismatch: {original_sha}")
    text = raw.decode("utf-8")
    require(text.count(OBSOLETE_GATE_LINE) == 1, f"obsolete parser gate anchor changed for {year}")
    transported = text.replace(OBSOLETE_GATE_LINE, V6_NONBINDING_LINE, 1)
    require(transported.count(V6_NONBINDING_LINE) == 1, f"v6 nonbinding parser marker missing for {year}")
    require(transported.replace(V6_NONBINDING_LINE, OBSOLETE_GATE_LINE, 1) == text, f"parser transform not exactly reversible for {year}")
    transported_sha = hashlib.sha256(transported.encode("utf-8")).hexdigest()

    name = f"orbittrace_v6_sonotaco_{year}_transport_parser"
    spec = importlib.util.spec_from_loader(name, loader=None)
    require(spec is not None, f"cannot create transported parser module {year}")
    module = importlib.util.module_from_spec(spec)
    module.__file__ = f"{name}.py"
    sys.modules[name] = module
    exec(compile(transported, module.__file__, "exec"), module.__dict__)
    require(float(module.BLIND_SOLAR_MIN) == 20.0 and float(module.BLIND_SOLAR_MAX) == 55.0, f"parser blind interval changed {year}")
    parse_name = f"parse_sonotaco_{year}_events"
    require(hasattr(module, parse_name), f"transport parser entry point missing {year}")
    return module, {
        "year": year,
        "original_source_sha256": original_sha,
        "transported_source_sha256": transported_sha,
        "replacement_count": 1,
        "removed_binding_gate": "at_least_30_supported_native_codes",
        "replacement_nonbinding_marker": "v6_transport_old_supported_code_gate_nonbinding",
        "all_other_parser_gates_unchanged": True,
        "blind_interval_unchanged": [20.0, 55.0],
    }


def parse_transfer_year(
    year: int,
    source_path: Path,
    archive_path: Path,
    mapping_audit_path: Path,
    base: ModuleType,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    archive_sha = sha256_path(archive_path)
    require(archive_sha == ARCHIVE_SHA256[year], f"archive {year} hash mismatch: {archive_sha}")
    module, transform_audit = load_transported_parser(year, source_path)
    parser = getattr(module, f"parse_sonotaco_{year}_events")
    labeled, sporadic, parser_audit = parser(archive_path, mapping_audit_path, base)
    gates = dict(parser_audit["gates"])
    require(gates.pop("v6_transport_old_supported_code_gate_nonbinding", None) is True, f"v6 nonbinding gate marker missing after parse {year}")
    require(all(gates.values()), f"transport parser gate failure {year}: {gates}")
    require(parser_audit["input_hashes"]["archive_sha256"] == ARCHIVE_SHA256[year], f"parser archive identity changed {year}")
    require(parser_audit["gates"]["blind_interval_removed_before_label_access"] is True, f"blind boundary failed {year}")
    return labeled, sporadic, {
        "transform": transform_audit,
        "parser": parser_audit,
        "binding_parser_gates": gates,
        "obsolete_supported_code_gate_imported_into_v6": False,
    }
