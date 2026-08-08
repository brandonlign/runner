# MAARSY RCS Stage 0G source-guard correction

Frozen before any Stage-0G execution and before any HDF5 member payload is opened.

The first Stage-0G workflow draft contained a self-referential shell audit: it searched the workflow file for forbidden HDF5 value-reading method names, while the grep commands themselves necessarily contained those literal names. That implementation would fail before data transport even though the inspection code contained no such value read.

This correction does not alter the authorized HDF5 access boundary, dataset selection, compressed-range bound, structural outputs, or any scientific rule. The original workflow is left inert by retaining its original trigger path. A v2 workflow uses a distinct trigger `RUN_MAARSY_RCS_STAGE0G_V2.md`, omits the self-referential grep, and additionally tightens decompression so exactly the two directory headers, the first HDF5 header, and exactly 139,028,822 payload bytes are emitted—no tar padding or next-member header is decompressed.

No MAARSY HDF5 payload, event value, OrbitTrace target information, or GMN Stage A/Stage B data was accessed before this correction.