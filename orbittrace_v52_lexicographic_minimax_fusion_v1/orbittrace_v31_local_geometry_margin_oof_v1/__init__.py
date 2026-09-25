from __future__ import annotations

import sys
from pathlib import Path

# Execution-only import-path shim for v52. Running train_evaluate.py by file path
# places the v52 source directory, not the repository root, at sys.path[0].
# Redirect this package's submodule lookup to the already-pinned repo-root v31
# package and prepend the same frozen v22 stub path used by valid v31/v51 runs.
# No v31/v52 scientific source or ranking rule is copied or modified here.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_REAL_PACKAGE = _REPO_ROOT / 'orbittrace_v31_local_geometry_margin_oof_v1'
_V22_STUBS = _REPO_ROOT / 'orbittrace_v22_sonotaco_grouped_oof_ranker_v1' / 'stubs'
for _path in (str(_REPO_ROOT), str(_V22_STUBS)):
    if _path not in sys.path:
        sys.path.insert(0, _path)
__path__ = [str(_REAL_PACKAGE)]
