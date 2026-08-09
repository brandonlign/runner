from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

EXPECTED_GIT_BLOB = "493fcc7f2d2cc75ee35acf17e142e7ce7c1e03e8"


def _git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


_source = Path(__file__).resolve().parents[1] / "orbittrace_wavelet_catalogue_v3" / "wavelet_episode_comparator.py"
_raw = _source.read_bytes()
_digest = _git_blob_sha1(_raw)
if _digest != EXPECTED_GIT_BLOB:
    raise RuntimeError(f"unexpected Stage-A wavelet comparator identity: {_digest}")

_spec = importlib.util.spec_from_file_location("orbittrace_stage_a_exact_wavelet_episode_comparator", _source)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load exact Stage-A comparator {_source}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

for _name, _value in vars(_module).items():
    if _name not in {"__name__", "__loader__", "__package__", "__spec__"}:
        globals()[_name] = _value
