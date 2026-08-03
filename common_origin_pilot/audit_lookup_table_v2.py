#!/usr/bin/env python3
from __future__ import annotations

import audit_lookup_table

# Current Digital Commons Data API separates anonymous public-file listing
# from the authenticated generic dataset endpoint.
audit_lookup_table.API_CANDIDATES = [
    f"https://api.data.mendeley.com/datasets/publics/{audit_lookup_table.DATASET_ID}/files?version={audit_lookup_table.VERSION}&$limit=100",
    f"https://api.data.mendeley.com/datasets/{audit_lookup_table.DATASET_ID}/files?version={audit_lookup_table.VERSION}&$limit=100",
]

if __name__ == "__main__":
    audit_lookup_table.main()
