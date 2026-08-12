#!/usr/bin/env python3
"""Engineering-only repair for v61 literature comparator budget metadata.

The first v61 run sealed its pretruth order before truth access, then failed before any
scientific panel was evaluated because run_transfer.py encoded the recovered-count field
as the comparator budget for Sugar and HDBSCAN 2013. This wrapper changes only those four
externally frozen comparator-budget constants. It does not alter candidate memberships,
predictive features, predictive order, v31 parent order, fusion, literature scores,
literature recovered counts, or the binding 4/4 gate.
"""
from __future__ import annotations

import run_transfer as v61

v61.EXPECTED_LITERATURE = {
    ('sugar', 2013): (0.20372657466522806, 13, 34),
    ('sugar', 2014): (0.25901527732153334, 15, 46),
    ('hdbscan', 2013): (0.16813025050497152, 10, 11),
    ('hdbscan', 2014): (0.15689595582646423, 9, 9),
}


if __name__ == '__main__':
    raise SystemExit(v61.main())
