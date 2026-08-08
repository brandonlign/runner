# MAARSY RCS Stage 0G — first HDF5 schema-only audit

Frozen after Stage-0F bounded header run `31232266982` / artifact `9014203079` (artifact ZIP SHA-256 `8a9f1851c228d75265ceec40baab51b51e86d3b414744574b2f1c2e452e5a59f`) and before opening any HDF5 object or interpreting any meteor value.

Stage 0F transported only compressed bytes `0–1048575`, materialized at most 65,536 uncompressed bytes, and stopped at the first non-empty tar member without reading its payload. The exact first member header is now frozen as:

- name: `data/2016/03/kep_collect.h5`;
- tar member size: `139028822` bytes;
- type: regular file (`0`);
- header offset: 1024 uncompressed bytes.

No payload byte from that member was interpreted in Stage 0F.

## Purpose

Determine whether the public RCS release structurally contains the timestamp, geocentric-trajectory/vector, geocentric-speed, and stable-identity fields required to define a v8 parser **before any dataset value is read**.

## Authorized access

Stage 0G may:

1. request only a fixed initial compressed range `bytes=0-268435455` from the exact Zenodo file frozen in Stage 0E;
2. stream-decompress from the start only until the complete exact first tar member `data/2016/03/kep_collect.h5` has been materialized;
3. require the same tar header name and size as Stage 0F before writing any member byte;
4. stop decompression immediately after the exact 139,028,822-byte first member is complete; do not continue to the next tar header;
5. open that HDF5 file with `h5py==3.11.0` in read-only mode;
6. enumerate only structural metadata:
   - group and dataset paths;
   - object type;
   - dataset shape and rank;
   - dataset dtype string;
   - chunk shape;
   - compression/filter names where exposed structurally;
   - attribute **names only**, never attribute values;
7. reject any code path that indexes, slices, converts, iterates, computes on, summarizes, prints, hashes, or otherwise reads a dataset value;
8. never call `dataset[...]`, `dataset[()]`, `read_direct`, `asstr`, NumPy conversion on a dataset, or any equivalent value-reading operation;
9. never retrieve an HDF5 attribute value; only `attrs.keys()` may be used;
10. delete the HDF5 payload and compressed range before artifact upload.

The workflow source itself is the frozen parser for this schema-only stage. A later scientific parser may not be written from observed MAARSY values; it may use only this structural schema plus separately frozen public documentation/conventions.

## Interpretation boundary

Dataset names/shapes/dtypes and attribute names are interface metadata, not meteor scientific values. Nevertheless this is the first access to bytes inside a scientific member, so the boundary must be explicit:

- scientific member payload transported/materialized: true;
- HDF5 structural metadata inspected: true;
- HDF5 dataset value read: false;
- HDF5 attribute value read: false;
- event/scientific value interpreted: false;
- v8 scientific evaluation performed: false;
- OrbitTrace target information access: false;
- GMN Stage A/Stage B access: false.

If structural names do not establish a plausible route to all required v8 inputs, stop as interface-incompatible. If they do, freeze exact coordinate/frame/unit semantics from public documentation before any event-value access.

No v8 parameter, external power floor, ranking rule, target boundary, or reveal rule may change.