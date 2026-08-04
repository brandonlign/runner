from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('source_args', nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = importlib.util.spec_from_file_location('frozen_mondrian_2018_confirmation', args.source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load exact frozen source: {args.source}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    if tuple(module.ALLOWED_YEARS) != (2021, 2024, 2025, 2026):
        raise RuntimeError(f'Unexpected exact-source year interface: {module.ALLOWED_YEARS}')
    if tuple(module.ALLOWED_CORPORA) != ('odd-archive', 'even-archive', 'fresh-2026h1-spent'):
        raise RuntimeError(f'Unexpected exact-source corpus interface: {module.ALLOWED_CORPORA}')

    # Interface-only extension. The hash-verified source bytes, statistic,
    # calibration, seeds, folds, comparators, and scientific gates are unchanged.
    module.ALLOWED_YEARS = tuple(module.ALLOWED_YEARS) + (2018,)
    module.ALLOWED_CORPORA = tuple(module.ALLOWED_CORPORA) + ('complete-year-2018-confirmation',)
    source_args = list(args.source_args)
    if source_args and source_args[0] == '--':
        source_args = source_args[1:]
    sys.argv = [str(args.source), *source_args]
    module.main()


if __name__ == '__main__':
    main()
