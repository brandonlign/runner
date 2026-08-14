# ASFN header-repaired retry 31850281138 — technical no-result

Run `31850281138`, job `94924640455`, execution commit `dca3e86940c27c7e82e92a3817e8bf4e76855311` is **not a scientific ASFN result**.

All frozen scientific-source checks passed. The binding zero-data hash-header repair audit was downloaded and verified exactly before ASFN access.

The workflow then failed in the archive-acquisition step before the frozen ASFN scientific runner was invoked. `curl` transferred exactly zero bytes and exited with code 28 after the HTTPS connection to the already-frozen NASA URL timed out:

`Failed to connect to fireballs.ndc.nasa.gov port 443 ... Connection timed out`

Therefore:

- the ASFN archive was not acquired in this run;
- no archive hash comparison was reached on received bytes;
- the header-repaired scientific runner was skipped;
- no HDBSCAN fitting occurred;
- no candidate/prelabel payload was generated;
- no `shw` value was opened;
- no scientific metric or PASS/FAIL endpoint exists.

Preserved artifact: `9237297280`, digest `sha256:dd1eed6658db510409102c5250dbce31ff80b89bdfcb7ce5ae0dd018ec456566`.

The original scientific protocol/runner, promoted recurrent-EOM method, hash-header repair, years, blind interval, features, HDBSCAN settings, ranking, label boundary, evaluator, and gate remain unchanged.

Only a separately frozen **transport-only** retry using the same NASA URL and requiring the same exact archive SHA-256 may follow. It may add bounded connection retries/time allowance only. It may not use an alternate archive, mirror, dataset, year pair, transform, parser behavior, or scientific change.
