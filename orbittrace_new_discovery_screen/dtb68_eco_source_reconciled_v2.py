#!/usr/bin/env python3
"""Implementation-only repair for the primary-source ECO representation.

Scientific settings remain those frozen in DTB68_ECO_SOURCE_RECONCILIATION.
This supplies the GMN orbit-column aliases expected by the descriptive audit.
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
target.ECO_REF_SOL = 307.1


if __name__ == "__main__":
    raise SystemExit(target.main())
