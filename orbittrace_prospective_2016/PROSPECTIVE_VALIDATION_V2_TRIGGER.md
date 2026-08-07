# Prospective validation v2 transport repair trigger

This file triggers the source-audited v2 workflow after the transport-only builder repair.

Scientific method, selected offset `+0.50`, empirical calibration, prospective input universe, reporting alpha, and all acceptance gates are unchanged from `PROSPECTIVE_VALIDATION_PROTOCOL.md`.

The v2 change is infrastructure-only: the 2016 runner builder now matches the exact validated 2023 benchmark's constant/gate syntax rather than assuming parser-specific historical literals. The one-shot science job remains blocked behind a no-2016-data source audit and executes only the exact source bundle emitted by that audit.
