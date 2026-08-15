# Runtime path repair after pre-data import stop

Workflow run `31898305031` is a pre-data engineering no-result. The repaired zero-truth whitening audit passed completely, then the workflow stopped while importing the already-frozen GMN runtime utility with `ModuleNotFoundError: orbittrace_unified_recurrent_catalogue_lab_v1`.

The GMN catalogue parser had not run, no GMN event geometry was opened, no whitening transform was fit to GMN, no HDBSCAN fit occurred, no prelabel was written, and no hidden shower truth was opened.

The missing module already exists in the checked-out repository root. The sole repair is to add the repository root `.` to `PYTHONPATH` for the scientific execution step. No source, data, statistic, covariance rule, HDBSCAN setting, density-synchronous objective, promotion gate, or firewall rule changes.

The first technically valid scientific outcome remains unconsumed and binding.