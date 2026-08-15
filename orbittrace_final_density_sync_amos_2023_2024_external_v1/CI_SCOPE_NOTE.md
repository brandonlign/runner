# CI scope note

This branch triggers many unrelated historical path-insensitive workflows on every push in `brandonlign/runner`. Their failures are not scientific endpoints for this package.

The authoritative workflows for this final AMOS pre-data package are only:

1. `orbittrace_final_density_sync_amos_predata_audit_v1.yml` — binding run `31864904536`, PASS;
2. `orbittrace_final_density_sync_amos_comparator_isolation_audit_v1.yml` — binding run `31865012724`, PASS;
3. `orbittrace_final_density_sync_amos_transport_reuse_audit_v1.yml` — binding run `31865140271`, PASS;
4. `orbittrace_final_density_sync_amos_execution_freeze_audit_v1.yml` — binding run `31865241958`, PASS.

All four are zero-scientific-data workflows and are sealed by exact run/artifact/result identities. Unrelated legacy workflow failures caused by broad repository triggers must not be interpreted as failures of these four audits or as authorization to rerun/change the scientific package.