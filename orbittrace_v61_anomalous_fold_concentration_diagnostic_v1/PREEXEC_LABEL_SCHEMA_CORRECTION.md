# Pre-execution #1046 label-schema correction

The frozen v61 protocol permits every authoritative #1046 annual shower-group row and defines fold assignment as

`deterministic_fold('SHOWER/' + label)`.

Before any v61 workflow was created or executed, audit of the initial implementation found an extra source-only assertion requiring `label.startswith('MDC_GROUP:')`. That assertion is not in the protocol and is incompatible with authoritative #1046, which legitimately contains frozen labels such as `MDC_GROUP:...`, `PARENT:...`, and `SHOWER:...`.

No v61 result existed when this was found. No fold fraction, surfaced/missed statistic, or PASS/FAIL result had been computed.

The repaired executable changes only that schema assertion: the frozen label must be nonempty, then fold assignment remains exactly

`deterministic_fold('SHOWER/' + label)`.

The anomalous fold remains preselected as integer `4`; the sole statistic remains the fold-4 fraction in fixed #1046 MISSED vs SURFACED recoverable groups; PASS still requires the missed fraction to be strictly greater in both 2013 and 2014. No alternate fold, fold subset, threshold, representative, order, successor, or parameter is evaluated.
