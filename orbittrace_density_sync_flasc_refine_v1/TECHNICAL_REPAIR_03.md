# Density-sync FLASC refinement v1 — technical repair 03

## Status

**TECHNICAL INTERFACE REPAIR ONLY. FROZEN BEFORE ANY TECHNICALLY VALID FLASC SCIENTIFIC RESULT.**

The frozen scientific protocol, `run_development.py`, FLASC settings, candidate-selection logic, known-shower evaluator, firewall, and gates are unchanged.

## Prior no-results

The existing attempts do not contain a scientific FLASC verdict:

- original branch run `31921945971` stopped while reconstructing the prerequisite density-sync parent (`2076 != 2094`) before FLASC branch detection;
- Repair 1 run `31922286016` stopped at Python startup from a circular import before catalogue parsing;
- Repair 2 run `31922398511` fixed module resolution and parsed the complete target-excluded GMN runtime, but stopped during the prerequisite parent HDBSCAN fit because the Repair-1 subclass `_ExactParentHDBSCAN(self, *args, branch_detection_data=False, **kwargs)` violated scikit-learn estimator constructor introspection. It failed before exact-parent reconstruction completed, before FLASC branch detection, before prelabel/result serialization, and before the frozen gate contract could be enforced.

A later retrigger of the unchanged Repair-2 bytes is execution-only and cannot supersede that deterministic technical diagnosis.

## Cause

Repair 1 needed to suppress HDBSCAN's `branch_detection_data=True` convenience cache during the prerequisite parent fit, while reconstructing the exact branch-support objects only after the frozen density-sync parent labels were known.

It implemented that interception by subclassing `hdbscan.HDBSCAN` with a variadic constructor. During `.fit()`, HDBSCAN invokes scikit-learn `get_params()`, which inspects the estimator class constructor and rejects variadic `*args/**kwargs` signatures.

This is an adapter incompatibility, not a scientific-method outcome.

## Sole authorized repair

Replace only the estimator subclass used by the technical wrapper with a constructor factory:

1. retain the exact original `hdbscan.HDBSCAN` class as `_OriginalHDBSCAN`;
2. define a plain Python factory accepting the frozen runner's constructor call;
3. construct and return `_OriginalHDBSCAN(..., branch_detection_data=False, ...)` with every other positional/keyword argument passed through unchanged;
4. attach only `_repair_branch_detection_requested = bool(branch_detection_data)` to the returned base estimator instance;
5. keep the existing post-fit `_repair_detect_branches(...)` support reconstruction unchanged except that it validates the marker attribute rather than requiring the removed subclass type;
6. launch the repair wrapper as a module, preserving Repair 2's import-resolution fix.

Because the returned object is the real upstream `hdbscan.HDBSCAN`, scikit-learn introspection sees the upstream constructor rather than a repair subclass.

## Scientific invariants / mandatory proof before FLASC

The frozen runner already requires, before calling FLASC:

- reconstructed parent candidate count exactly `2094`;
- ordered parent membership SHA exactly `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`;
- unordered parent membership multiset identical to the sealed density-sync winner;
- the complete target-excluded event universe exactly `738682`;
- the protected inclusive solar-longitude interval `[20,55]` absent.

Those checks remain unchanged. Therefore Repair 3 is not permitted to reach FLASC if the constructor factory changes the prerequisite scientific parent in any way.

No package-version change, HDBSCAN parameter change, branch parameter change, membership rule change, ranking change, gate change, or data access is authorized.

## Binding rule

The first later run that passes the exact-parent reconstruction, completes the frozen FLASC endpoint, serializes both frozen output files, and reaches the existing gate-enforcement step is the first technically valid scientific result and is binding.
