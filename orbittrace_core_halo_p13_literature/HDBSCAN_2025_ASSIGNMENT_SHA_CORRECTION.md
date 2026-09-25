# HDBSCAN 2025 assignment SHA provenance correction

Status: **technical/pretruth provenance correction only**. This does not change the comparator assignment bytes, row universe, clustering, scientific method, evaluator, sparse gates, or truth timing.

The frozen P13 matched-literature metadata and v3 launcher contain a one-character transcription error for the HDBSCAN 2025 `full_catalogue_assignments.jsonl.gz` member SHA256:

- stale text: `8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3`
- exact immutable member bytes: `8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3`

The correction was established before any P13 matched pretruth checkpoint or truth/competitor-value access. Technical recovery workflows `31322983205` and `31323275459` both stopped in assignment transport before strict ID manifest generation. Neither produced a benchmark checkpoint or scientific result.

Immutable provenance establishing the correction without parsing assignment contents:

- source workflow: `31071589912`
- source job: `92521152371`
- artifact ID: `8955917326`
- artifact name: `orbittrace-sonotaco-2025-hdbscan-catalogue`
- GitHub-recorded artifact ZIP digest: `sha256:82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89`
- exact member basename: `full_catalogue_assignments.jsonl.gz`
- exact member raw-byte SHA256: `8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3`
- expected matched row count remains `19658`; this correction does not derive from or alter row contents.

The artifact-creation job independently records successful upload of artifact `8955917326` with the exact ZIP digest above. The v5 recovery must download this artifact by exact ID, verify the ZIP digest, require exactly one member with the frozen basename, verify the corrected raw-byte member SHA, and then proceed to the already-frozen ID-only manifest stage. The inherited stale SHA string may be replaced exactly once in the generated technical launcher and nowhere else.

No assignment JSON value, competitor cluster value, known-shower truth, MAARSY value, target-region event, or OrbitTrace target information was used to make this correction. Solar longitude 20°–55° remains inaccessible.
