# Local first valid result note

The scientific protocol in `PROTOCOL.md` was frozen before the first SonotaCo score of the internal-mass ordering. After the zero-label pretruth support artifact was produced, the exact direct accumulator now stored as `internal_mass_exact.cpp` was validated against brute-force enumeration on deterministic small zero-label candidates before the full truth score was opened locally.

That first technically valid local execution produced `PASS_INTERNAL_MASS_SONOTACO_DEVELOPMENT_V1` with mean AUC macro-F1 `0.35364538749003405`, mean K40 macro-F1 `0.5012446318461822`, total recovered@40 `58`, and mean native macro-F1 `0.7266723655790133`.

The GitHub Actions binding run is therefore a provenance/reproducibility reproduction of an already-observed post-freeze development result, not a claim that truth remained unopened until CI. No method, score, gate, candidate membership, or ranking rule may be changed based on the local result.
