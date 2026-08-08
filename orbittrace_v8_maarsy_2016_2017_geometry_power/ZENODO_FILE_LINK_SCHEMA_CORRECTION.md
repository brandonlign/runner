# MAARSY 2016/2017 geometry-power Zenodo file-link schema correction

Frozen after execution run `31233509369` and before any corrected execution.

That run passed every pre-data source/AST/target guard and invoked the frozen scientific runner. The runner then stopped inside `verify_zenodo_metadata()` before requesting the MAARSY archive and before opening or reading any HDF5 dataset value:

`RuntimeError: Zenodo content URL changed: ''`

The exact Zenodo record JSON had already been retrieved and frozen during pre-access Stage 0E, run `31232122463`, artifact `9014157024`, ZIP SHA-256 `9e65634b640ff3919ee1e64d696cdbd012f6f46995d8e21c0b9ebaaabdaa9e00`. In that immutable record, the sole file object is:

- key `silseth_thesis_data.tar.gz`;
- size `21485785089`;
- checksum `md5:01820c6a90ea1415b011bb013a4d9213`;
- `links.self = https://zenodo.org/api/records/15553437/files/silseth_thesis_data.tar.gz/content`;
- no `links.content` key is present.

The correction is metadata-schema-only. Starting from the exact frozen runner Git blob `2c04a1be4134ee07162b60e3168c6f1684299cf3`, replace exactly one expression:

`(f.get("links") or {}).get("content", "")`

with:

`((f.get("links") or {}).get("content") or (f.get("links") or {}).get("self") or "")`

The resulting URL is still required to equal the exact pre-frozen `CONTENT_URL`. The file key, byte size, MD5, years, field mapping, blind order, density cap, fixed4/v6/v8 method, rankings, N/Q floors, no-orbit boundary, and OrbitTrace/GMN firewall are unchanged.

No MAARSY archive byte, HDF5 dataset value, OrbitTrace target information, or final GMN Stage A/Stage B data was accessed by run `31233509369`.