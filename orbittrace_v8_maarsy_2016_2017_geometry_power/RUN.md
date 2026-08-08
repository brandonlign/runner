# Execute frozen MAARSY 2016/2017 geometry-power stage

Execution-only trigger for PR #441.

The parent protocol/source is frozen before any MAARSY HDF5 dataset value was read. This child changes no scientific source. The run may read solar longitude first, exclude 20°–55°, then read only retained rows' `slat/slon/vels`; all orbit fields, labels, OrbitTrace target information, and final GMN Stage A/Stage B data remain forbidden.
