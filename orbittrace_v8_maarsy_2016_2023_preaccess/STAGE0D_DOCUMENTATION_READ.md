# MAARSY Stage 0D — documentation-only member access

Frozen after Stage-0C run `31231892957` / artifact `9014083904` (ZIP SHA-256 `1f0a2ac8240860ebf0587f611175f8584bb3bd3ddc4e2104e6f4c708dfa37b0e`) and before any nested dataset ZIP or scientific data member is opened.

Stage 0C verified the exact public tar (SHA-256 `64c18431aece658f0a0ebae5a3bdb58215b3a3abbadf114d1898c2768271d460`) and exposed only tar headers. The scientific dataset payload is isolated as:

`10.22000-yk29t2gu0h4jhkjg/data/dataset/HuyghebaertAMT2025.zip`

size `10669057` bytes.

The following members are frozen as documentary/packaging metadata by name and tiny size before payload access:

1. `10.22000-yk29t2gu0h4jhkjg/data/readme.txt` — 1689 bytes
2. `10.22000-yk29t2gu0h4jhkjg/data/technical-md/dataset.tech_md.xml` — 625 bytes
3. `10.22000-yk29t2gu0h4jhkjg/data/dataset/README_HuyghebaertAMT2025.txt` — 684 bytes
4. `10.22000-yk29t2gu0h4jhkjg/manifest-md5.txt` — 293 bytes
5. `10.22000-yk29t2gu0h4jhkjg/bag-info.txt` — 106 bytes

Stage 0D may download the exact outer tar, verify exact size/MD5/SHA-256, and open **only those five whitelisted documentary/packaging members**. It must reject any size/name change before opening a member.

It may not open, list, extract, hash separately, decompress, or otherwise inspect `HuyghebaertAMT2025.zip` or any other non-whitelisted payload. The nested ZIP remains scientifically unopened.

Purpose: determine from author-supplied documentation whether the nested release contains event-level meteor trajectories/velocities, its internal file types, and any published variable/schema definitions needed to freeze a parser before scientific-value access.

No v8 evaluation, meteor-row/value access, power calculation, target information access, or GMN Stage A/Stage B execution is authorized.