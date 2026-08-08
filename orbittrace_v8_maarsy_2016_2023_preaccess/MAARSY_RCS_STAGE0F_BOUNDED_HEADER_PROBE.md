# MAARSY RCS Stage 0F — bounded gzip/tar header probe

Frozen after Zenodo metadata-only run `31232122463` / artifact `9014157024` (artifact ZIP SHA-256 `9e65634b640ff3919ee1e64d696cdbd012f6f46995d8e21c0b9ebaaabdaa9e00`) and before any Zenodo file-content request.

Exact file metadata:

- record `15553437`;
- file `silseth_thesis_data.tar.gz`;
- exact size `21485785089` bytes;
- exact Zenodo checksum `md5:01820c6a90ea1415b011bb013a4d9213`;
- content URL `https://zenodo.org/api/records/15553437/files/silseth_thesis_data.tar.gz/content`.

## Authorized bounded probe

Stage 0F may request **only the first 1,048,576 compressed bytes** (`Range: bytes=0-1048575`) from the exact content URL. It must reject a response that attempts to deliver an unbounded/full file.

The downloaded range may be passed to a gzip decompressor with a hard maximum of **65,536 uncompressed output bytes**. The code may parse only 512-byte tar headers in that output.

Header traversal rule:

1. record zero-size directory/header entries at the beginning of the archive;
2. stop immediately at the first tar member with `size > 0`;
3. record only that member's header metadata (name, type, size, mode/link metadata);
4. **do not read, decode, hash, summarize, or otherwise inspect any byte of that member's payload**;
5. do not skip through a non-empty member to find later headers.

If the first non-empty member is clearly documentary/source/schema by filename, opening it requires a separately frozen Stage 0G. If it is scientific/data-like, this probe stops there and no payload access is authorized.

## Firewall

This stage records that a bounded compressed byte range was transported, but no member payload or scientific value was interpreted. It must keep:

- event row/value access: false;
- scientific-value access: false;
- v8 evaluation: false;
- OrbitTrace target access: false;
- GMN Stage A/Stage B access: false.

No v8 parameter, scientific gate, external power floor, or target boundary changes.