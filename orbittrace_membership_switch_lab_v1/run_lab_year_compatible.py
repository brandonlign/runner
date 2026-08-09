#!/usr/bin/env python3
"""Technical wrapper: reproduce the exact promoted-v8 2022/2023 temporal substitution before running the membership lab."""
from orbittrace_membership_switch_lab_v1 import run_lab as lab

lab.mult.YEARS = lab.YEARS
lab.mult.MONTH_KEYS = lab.MONTH_KEYS
lab.mult.TOP_K = 100

if __name__ == "__main__":
    raise SystemExit(lab.main())
