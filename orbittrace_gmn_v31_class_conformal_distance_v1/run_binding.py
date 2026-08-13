#!/usr/bin/env python3
"""Engineering-only binding entrypoint for the frozen class-conditional successor.

The scientific implementation was frozen before execution. Its parent feature-SHA
constant was populated from a non-authoritative copied value. This entrypoint
replaces only that provenance assertion with the SHA read from authoritative
parent run 31563202833 / artifact 9128529120 before the first candidate outcome.
No scientific method, score, input, parameter, gate, or firewall rule changes.
"""
from __future__ import annotations

import run_development as impl

AUTHORITATIVE_PARENT_FEATURE_SHA = "fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5"
impl.PARENT_FEATURE_SHA = AUTHORITATIVE_PARENT_FEATURE_SHA

if __name__ == "__main__":
    raise SystemExit(impl.main())
