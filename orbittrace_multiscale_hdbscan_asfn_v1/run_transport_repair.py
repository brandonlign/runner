#!/usr/bin/env python3
"""Transport/provenance-only wrapper for frozen ASFN multiscale test.

The first parser attempt reproduced the exact 4,679/4,548 annual counts but its
physical-row ID bookkeeping did not byte-match the already sealed historical
ASFN prelabel.  This wrapper makes no scientific-method change: it supplies the
exact historical label-free event table (IDs + already-authorized GEO6 fields)
as the geometry input, while the unchanged frozen runner still opens the pinned
NASA archive only in its later label pass.
"""
from __future__ import annotations
import json
import os
from collections import Counter
from pathlib import Path
import orbittrace_multiscale_hdbscan_asfn_v1.run_generalization as frozen

HIST_ENV = "ORBITTRACE_ASFN_HISTORICAL_PRELABEL"


def exact_historical_events(archive: Path):
    # Preserve the frozen archive-identity check even though geometry values are
    # sourced from the earlier sealed label-free prelabel.
    frozen.req(frozen.sha(archive) == frozen.ARCHIVE_SHA, "archive hash drift")
    p = Path(os.environ[HIST_ENV])
    hist = json.loads(p.read_text())
    frozen.req(hist.get("target_information_access") is False, "historical target contamination")
    frozen.req(hist.get("shw_accessed") is False, "historical prelabel unexpectedly contains label access")
    events = hist["events"]
    counts = Counter(int(e["year"]) for e in events)
    frozen.req(dict(counts) == {2018: 4679, 2019: 4548}, f"historical event count drift {counts}")
    frozen.req(len(events) == 9227, "historical total event count drift")
    frozen.req(len({str(e["id"]) for e in events}) == len(events), "historical duplicate event IDs")
    frozen.req(all(not (frozen.BLIND[0] <= float(e["sol"]) <= frozen.BLIND[1]) for e in events), "protected ASFN event in historical geometry")
    return events


frozen.parse_events = exact_historical_events

if __name__ == "__main__":
    frozen.main()
