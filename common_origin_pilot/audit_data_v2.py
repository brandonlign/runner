#!/usr/bin/env python3
from __future__ import annotations

import audit_data

# CAMS and SonotaCo use the compact column name `sh` for shower association.
# The first audit intentionally searched semantic column names and therefore
# missed this exact schema convention. Keep the rest of the audit unchanged.
audit_data.COLUMN_TERMS = tuple(audit_data.COLUMN_TERMS) + ("sh",)

if __name__ == "__main__":
    audit_data.main()
