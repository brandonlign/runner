# CAMSv3 independent-survey structural feasibility gate

Status: frozen before this branch downloads any CAMS archive.

## Purpose

Determine whether the official IAU MDC CAMSv3 annual archives can support a third-survey, survey-native development screen of the unchanged PR #38 coverage-normalized Mondrian four-clique method after the SonotaCo 2025 near-miss.

This is a data-interface gate only. It reads no GhostStream value, performs no detector scoring, forms no calibration window, and reads no shower-label value. SonotaCo 2024 remains untouched.

## Frozen corpus

Use every nonempty annual CAMSv3 archive in the already documented contiguous release interval 2011–2016. The exact URLs, archive hashes, member names, and row counts were independently recorded by runner PR #4 before this gate:

| Year | Archive SHA-256 | Member | Rows |
|---|---|---|---:|
| 2011 | `de2af15ccdee9836912c1efb9fba9bdcf47e3b9d2fa7374244dc6ac69f82c118` | `iaumdcCAMSv3_2011.csv` | 44,998 |
| 2012 | `040b853d6fbcd5dfc9ef3f76be553624a9893ab9b1aac709ccebcc2498c73cb3` | `iaumdcCAMSv3_2012.csv` | 53,401 |
| 2013 | `895f58c985f730976ef6e3ca3c89cd947bd248b419101eba163eef77e951e56a` | `iaumdcCAMSv3_2013.csv` | 76,213 |
| 2014 | `0d9ba75256577e9b008786054ea13c4fa6b755d42ae65031f311bae8a0b3a928` | `iaumdcCAMSv3_2014.csv` | 83,336 |
| 2015 | `aa9a04b206e1927d7a8cb401ef22baae20061c9827dec0133e42b11790fcf61d` | `iaumdcCAMSv3_2015.csv` | 100,700 |
| 2016 | `40e901fa8c8e017e5fe6bf9e9739a2c840d7e0d259e59b57ccf374d7d9700f30` | `iaumdcCAMSv3_2016.csv` | 110,352 |

## Frozen parser and gates

For each archive:

1. require HTTP success, exact archive SHA-256, valid ZIP CRC, and safe member paths;
2. require exactly the pinned CSV member;
3. parse UTF-8-SIG with semicolon delimiter;
4. require the pinned row count and a unique nonempty header;
5. require exact geometry fields `Yr`, `Mn`, `Dayy`, `LS`, `RA`, `DECL`, and `Vg`;
6. require an identical header across all six years;
7. record the complete header names and normalized header names, but read no data-column value.

Every gate must pass. A pass authorizes only a separately frozen aggregate-only label-interface audit. That later audit must predeclare its candidate label fields and universal mapping rules from this structural result before reading any label token or frequency. It may then remove solar longitude 20°–55° before every aggregate.

A failure kills CAMSv3 as the next external-validation route under this parser. No archive, year, hash, delimiter, member, row count, or field requirement will be changed after execution.
