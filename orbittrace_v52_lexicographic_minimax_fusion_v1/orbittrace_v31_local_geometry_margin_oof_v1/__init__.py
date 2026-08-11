from __future__ import annotations

import sys
from pathlib import Path

# Execution-only import-path shim for v52. Running train_evaluate.py by file path
# places the v52 source directory, not the repository root, at sys.path[0].
# Redirect this package's submodule lookup to the already-pinned repo-root v31
# package without copying or modifying any v31 or v52 scientific source.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_REAL_PACKAGE = _REPO_ROOT / 'orbittrace_v31_local_geometry_margin_oof_v1'
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
__path__ = [str(_REAL_PACKAGE)]
