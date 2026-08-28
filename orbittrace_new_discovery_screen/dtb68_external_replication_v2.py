#!/usr/bin/env python3
"""Implementation-only repair for the frozen DTb68 independent replication.

The frozen scientific thresholds/template are unchanged. The original runner
read SonotaCo CSV headers literally; those archives contain leading spaces on
most column names. This wrapper normalizes header whitespace before delegating
to the frozen runner.
"""
from __future__ import annotations

from orbittrace_new_discovery_screen import dtb68_external_replication as base

_original_read_zip_csv = base.read_zip_csv


def read_zip_csv_stripped(url: str):
    frame, member, nbytes = _original_read_zip_csv(url)
    frame.columns = [str(column).strip() for column in frame.columns]
    return frame, member, nbytes


base.read_zip_csv = read_zip_csv_stripped


if __name__ == "__main__":
    raise SystemExit(base.main())
