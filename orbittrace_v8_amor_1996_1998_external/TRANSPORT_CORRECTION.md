# AMOR external transport correction

The first frozen execution (`31220224170`) failed in header verification before any numeric AMOR scientific token was converted. The external runner used comma splitting, while the already-preserved structure-only artifact (`9009809682`) had frozen `delimiter_class = whitespace` for both selected members and recognized the exact same 18-field header under whitespace tokenization.

This correction is transport-only and source-provable from pre-scientific metadata. The original external protocol and scientific runner remain immutable. A tiny execution wrapper replaces only the runner module's `split_csv(raw)` helper with `raw.strip().split()` before `main()` is called.

No other behavior may change. In particular: selected years 1996+1998, archive hashes, width-18 acceptance / width-17 drop, first scientific field `LS`, 20°–55° blind cut, row identities, 10,000/bin density normalization, v6 connected-family topology, v8 pooled-year centroids, 128-event multiplicity ranking, Brown/v3/persistence comparators, post-ranking D_SH evaluator, N/Q power floors, top-K rule, and scientific pass gates remain exactly frozen.

The retry workflow must additionally assert from the preserved structure artifact that both selected data members have `delimiter_class == "whitespace"` before any AMOR archive is downloaded.
