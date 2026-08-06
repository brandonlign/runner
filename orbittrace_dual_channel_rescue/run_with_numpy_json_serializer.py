#!/usr/bin/env python3
"""Execute an audited runner while converting only NumPy scalar JSON values."""
from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import numpy as np

_ORIGINAL_DUMPS = json.dumps


def numpy_scalar_default(value: Any) -> Any:
    """Convert a NumPy scalar to its native Python scalar for JSON encoding."""
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


def patched_dumps(obj: Any, *args: Any, **kwargs: Any) -> str:
    """Call the standard encoder with the NumPy-scalar default if none was supplied."""
    kwargs.setdefault("default", numpy_scalar_default)
    return _ORIGINAL_DUMPS(obj, *args, **kwargs)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: run_with_numpy_json_serializer.py RUNNER [RUNNER_ARGS ...]")
    runner = Path(sys.argv[1])
    if not runner.is_file():
        raise SystemExit(f"runner not found: {runner}")
    forwarded = sys.argv[2:]
    json.dumps = patched_dumps
    sys.argv = [str(runner), *forwarded]
    runpy.run_path(str(runner), run_name="__main__")


if __name__ == "__main__":
    main()
