# Engineering repair 3 — legacy pandas / NumPy ABI compatibility

## Classification

**ENGINEERING NO-RESULT REPAIR ONLY.**

Workflow run `31972425846`, job `95226793366`, passed every frozen source assertion and then failed at Python import before the first monthly GMN request. `gmn-python-api==0.0.13` pulled pandas 1.3.5 together with current NumPy 2.2.6; importing pandas raised `ValueError: numpy.dtype size changed` due the NumPy 2.x binary-ABI break.

No monthly file was requested, `audit.py` did not enter `main()`, and no project `Num (stat)` value, mapping, histogram, subset statistic, or availability gate was produced.

## Exact repair

Preinstall `numpy==1.23.5` before the unchanged `gmn-python-api==0.0.13` installation. This satisfies the package's declared `numpy>1.20.3` requirement while remaining in the NumPy 1.x ABI generation used by the pinned pandas 1.3.5 wheel.

No change to any project source, GMN endpoint, parsed field, blind exclusion, event universe, completeness rule, conditional station-weight formula, graph, density, support, subset, comparator, metric, gate, or firewall.