#!/usr/bin/env python3
from __future__ import annotations

from orbittrace_v31_source_density_suppression_diagnostic_v1 import diagnose

# Immutable #950 pretruth manifest cardinalities. The first workflow attempt
# stopped before truth/status because the original transcription used 54/156.
diagnose.EXPECTED_SOURCES = {'hard': 19, 'p19': 53, 'p20': 157}

if __name__ == '__main__':
    raise SystemExit(diagnose.main())
