# Execute frozen Harvard 1968/1969 label-only structure audit

Execution-only child of PR #357.

The job may download the PDS4 bundle as opaque bytes and read only ZIP central-directory metadata plus official `har6869` label metadata. It must never open/decompress `har6869.tab`, inspect event values or source labels, run v8, or access OrbitTrace target information. The downloaded scientific bundle must be deleted before artifact upload.
