#!/usr/bin/env python3
"""Implementation-only repairs for the frozen DTb68/ECO continuity audit.

No scientific setting changes. GMN uses q_au/i_deg/peri_deg/node_deg; the
frozen audit's descriptive output referred to short aliases. This wrapper adds
those aliases after the unchanged quality/data loading step.
"""
from __future__ import annotations

from orbittrace_new_discovery_screen import dtb68_eco_continuity as target

_original_load_year = target.load_year


def load_year_with_orbit_aliases(year: int):
    frame = _original_load_year(year)
    aliases = {
        "q": "q_au",
        "incl": "i_deg",
        "peri": "peri_deg",
        "node": "node_deg",
    }
    for alias, source in aliases.items():
        if alias not in frame.columns and source in frame.columns:
            frame[alias] = frame[source]
    return frame


target.load_year = load_year_with_orbit_aliases


if __name__ == "__main__":
    raise SystemExit(target.main())
