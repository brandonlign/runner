#!/usr/bin/env python3
from __future__ import annotations

import build_prelabel as frozen
import technical_exact_full_row_transport as exact

# Technical transport only: the frozen main() is unchanged except that each
# parent calls the exact full-row lazy graph provider rather than materializing
# all Python neighbor rows simultaneously.
frozen.local_trunk = exact.local_trunk_exact_full_row

if __name__ == '__main__':
    raise SystemExit(frozen.main())
