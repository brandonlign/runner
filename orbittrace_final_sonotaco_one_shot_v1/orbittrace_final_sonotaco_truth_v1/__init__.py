"""Transport-only import bridge for the frozen SonotaCo truth package.

The one-shot scripts are executed by file path, so their directory replaces the
repository root at sys.path[0]. This bridge exposes the already-frozen top-level
truth package without copying or changing its scientific implementation.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_TRUTH = _ROOT / "orbittrace_final_sonotaco_truth_v1" / "truth_boundary.py"
_NORMALIZER = _ROOT / "orbittrace_final_sonotaco_normalizer_v1" / "normalizer.py"
_EXPECTED_GIT_BLOBS = {
    _TRUTH: "e61447c6589107bf2dc942e170582343239109a4",
    _NORMALIZER: "0264546418d0b50fa53514a6ba170f7c3e33d4d3",
}


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


for _path, _expected in _EXPECTED_GIT_BLOBS.items():
    if not _path.is_file() or _git_blob_sha(_path) != _expected:
        raise ImportError(f"frozen SonotaCo dependency identity mismatch: {_path}")

_root_text = str(_ROOT)
if _root_text not in sys.path:
    sys.path.insert(0, _root_text)

# Make the frozen top-level package directory part of this package's search path.
__path__.append(str(_ROOT / "orbittrace_final_sonotaco_truth_v1"))
