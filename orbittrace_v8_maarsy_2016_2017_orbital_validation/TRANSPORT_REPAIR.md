# MAARSY 2016/2017 orbital-validation transport repair

Failed run `31234879491` stopped before the orbital runner because the downloaded GitHub Actions ZIP container did not match the preregistered transport-container SHA-256. No `kepler` dataset value was read and no Q/scientific endpoint was evaluated.

The exact artifact remains GitHub Actions artifact `9014840161` from geometry-only run `31233762587`, named `orbittrace-v8-maarsy-2016-2017-geometry-power-v4`, size 69,387 bytes. GitHub's current artifact metadata reports digest `sha256:1016bb4bb8767d4f826ec97c31083f51fed29856f9ce8f8618b070e153fda342`. An independent connector download of that exact artifact reproduced the same 69,387-byte ZIP and the same SHA-256.

More importantly, the two scientific payloads inside that container exactly reproduce the already-frozen inner hashes:

- `v8_maarsy_2016_2017_geometry_power.json`: `12705afe1d499f8c0a5acbbae37d7119e4c369015b1cd1cfc18f2c3b63086351`;
- `maarsy_v8_geometry_rankings.json`: `fe8905d4c681a62f0b3f3b574465793d157f378d5c8321910f8d0bc6875e7279`.

The canonical ranking payload remains `a23696dc09896696d8b3c210181b9f0f93446dde73329f1ac5c53a4cf288c05b`, N remains 107, and the geometry artifact records zero orbit and zero target-information access.

Therefore the sole permitted repair is to replace the stale ZIP transport checksum with the current GitHub artifact digest. The exact artifact ID, exact source run, both inner scientific-file hashes, canonical ranking hash, orbital runner source, D_SH comparator, public orbit-semantics source pins, Q>=30 floor, and every scientific gate remain unchanged.

This is an implementation/transport correction only. It does not authorize reranking, method modification, threshold changes, alternative orbit interpretation, or target access.