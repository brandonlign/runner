#!/usr/bin/env python3
"""Resilient prefetch for the three frozen non-R3 PUNCH control FITS files.

This is transport-only infrastructure. It imports the prospectively frozen
2025-09-21 file selector and writes the exact same files to the existing control
output directory so downstream scientific code is unchanged.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import punch_kh_real_background_controls_v2 as bg


def main() -> int:
    bg.OUT.mkdir(parents=True, exist_ok=True)
    selected = bg.choose_files()
    for _, name in selected:
        dest = bg.OUT / name
        url = bg.ROOT + name
        # curl's --continue-at - resumes a partial transfer when the server
        # supports byte ranges. --retry-all-errors also retries transient read
        # timeouts/connection resets that requests previously treated as fatal.
        cmd = [
            "curl", "--fail", "--location", "--show-error",
            "--retry", "12", "--retry-delay", "5", "--retry-max-time", "900",
            "--retry-all-errors", "--connect-timeout", "30",
            "--speed-time", "120", "--speed-limit", "1024",
            "--continue-at", "-", "--output", str(dest), url,
        ]
        print("PREFETCH", name, flush=True)
        subprocess.run(cmd, check=True)
        if not dest.exists() or dest.stat().st_size < 2880:
            raise RuntimeError(f"prefetch produced invalid-sized file: {dest}")
        print("READY", name, dest.stat().st_size, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
