# MAARSY Stage 0C — opaque dataset-container listing

Frozen after successful metadata endpoint adjudication run `31231800637` / artifact `9014053985` (ZIP SHA-256 `2c82ce519796ca03d7080708b11012530aebedb2d4295d5900e636e86a7cfe15`) and before any dataset member content is opened.

The successful public metadata descriptions expose exactly one dataset distribution:

- content URL: `https://www.radar-service.eu/radar-backend/archives/yk29t2gu0h4jhkjg/versions/1/content`;
- media type: `application/x-tar`;
- declared size: `10686464` bytes;
- landing-page archive MD5: `a064c43c1b82dae8a5a214a4a1faa271`.

Neither RADAR XML nor Schema.org metadata exposes internal filenames or variable schemas; advertised Ro-Crate is unavailable (HTTP 404). Therefore a parser cannot yet be frozen from metadata alone.

## Authorized action

Stage 0C may:

1. establish the public anonymous RADAR landing-page session;
2. download the exact frozen dataset URL as opaque archive bytes;
3. require exact byte size `10686464` and MD5 `a064c43c1b82dae8a5a214a4a1faa271`;
4. compute and record SHA-256 of the archive;
5. open only the tar container headers and record each member's name, type, byte size, mode, and link target;
6. **never call `extract`, `extractall`, `extractfile`, `read` on a tar member, or otherwise access any member payload**;
7. delete the archive before artifact upload so no dataset content is copied into GitHub Actions artifacts.

The member list may be used only to identify clearly documentary/schema/source-code resources for a separately frozen Stage 0D. No data-like member may be opened until a parser/input mapping is frozen from documentation alone.

## Scientific firewall

Downloading opaque bytes and reading tar headers is transport/structure access, not scientific-value access. This stage must record:

- dataset archive downloaded: true;
- archive member payload opened: false;
- event row/value access: false;
- v8 scientific evaluation performed: false;
- OrbitTrace target information access: false;
- GMN Stage A/Stage B access: false.

No detector parameter, v8 rule, external power floor, or target boundary may change here.