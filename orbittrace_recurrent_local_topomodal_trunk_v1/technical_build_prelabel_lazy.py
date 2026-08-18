#!/usr/bin/env python3
from __future__ import annotations

# Technical-only execution wrapper. The frozen scientific runner remains
# byte-identical; only its local_trunk implementation is rebound to the
# exact lazy-neighbor storage equivalent before invoking the unchanged main().
import build_prelabel as frozen
from technical_lazy_local_trunk import local_trunk_lazy

frozen.local_trunk = local_trunk_lazy

if __name__ == "__main__":
    raise SystemExit(frozen.main())
