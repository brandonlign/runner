from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one occurrence, found {count}: {old!r}")
    return source.replace(old, new)


def load_original(path: Path):
    spec = importlib.util.spec_from_file_location("original_local_contrast_derivation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load original derivation: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive(base_source: str, original_derivation: Path) -> str:
    module = load_original(original_derivation)
    source = module.derive(base_source)
    source = replace_once(
        source,
        '"ideal_null_fwer_at_most_0_15": bool(ideal_summary["local_contrast"]["probability_any_detection"] <= 0.15 + tol),',
        '"ideal_null_fwer_at_most_0_20": bool(ideal_summary["local_contrast"]["probability_any_detection"] <= 0.20 + tol),',
    )
    source = replace_once(
        source,
        '"shared_structure_null_fwer_at_most_0_15": bool(shared_structure_summary["local_contrast"]["probability_any_detection"] <= 0.15 + tol),',
        '"shared_structure_null_fwer_at_most_0_20": bool(shared_structure_summary["local_contrast"]["probability_any_detection"] <= 0.20 + tol),',
    )
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_source", type=Path)
    parser.add_argument("original_derivation", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(
        derive(args.base_source.read_text(encoding="utf-8"), args.original_derivation),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
