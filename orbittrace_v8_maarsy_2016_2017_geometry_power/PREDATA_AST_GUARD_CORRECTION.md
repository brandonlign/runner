# MAARSY 2016/2017 geometry-power pre-data AST guard correction

Frozen after failed execution run `31233371065` and before any corrected execution.

The run completed environment setup, exact v8/source audit, promoted-v8 artifact verification, and public author-source semantic verification. It then stopped in the AST firewall with `AssertionError: 2` before the scientific runner was invoked and before any MAARSY HDF5 dataset value was read.

The frozen runner contains exactly two dynamic `h[name]` subscriptions, both inside the structural loop over the constant tuple:

`REQUIRED_GEOMETRY_DATASETS = ("sun_lon", "slat", "slon", "vels")`

One checks that the named object is an HDF5 dataset and the other binds the same required dataset to validate its shape/dtype. No forbidden/orbital field is dynamically selected; literal HDF5 subscriptions remain restricted to the same four geometry datasets.

The correction is source-guard only: change the AST assertion from `dynamic_h_subscripts <= 1` to `dynamic_h_subscripts == 2`. The scientific runner Git blob remains exactly `2c04a1be4134ee07162b60e3168c6f1684299cf3`; the frozen years, field semantics, blind order, density cap, v8 method, N/Q power floors, rankings, target firewall, and no-orbit rule are unchanged.

No MAARSY scientific value, OrbitTrace target information, or GMN Stage A/Stage B data was accessed by the failed run.