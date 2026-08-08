# MAARSY RCS Stage 0G materializer scope correction

Frozen after failed execution run `31232467940` and before any corrected Stage-0G execution.

That run passed the protocol guard, installed the frozen HDF5 reader, and transported the bounded 256 MiB compressed range. It then failed at Python compilation of the materializer with:

`SyntaxError: no binding for nonlocal 'ci' found`

The failure occurred before the materializer executed, before `kep_collect.h5` was created, before h5py opened any scientific member, and before any HDF5 structural metadata or dataset/attribute value was read.

The correction is implementation-only: replace module-scope scalar closure state (`ci`, `pending`, `emitted`) plus invalid `nonlocal` declarations with one module-scope mutable dictionary accessed by the helper function. Decompression bounds, exact tar headers, exact first-member name/size, output-byte boundary, HDF5 structural fields, no-value-read rule, v8 method, power gates, target firewall, and GMN Stage A/Stage B block are unchanged.

A v3 workflow uses a distinct execution trigger so the failed v2 source remains preserved.