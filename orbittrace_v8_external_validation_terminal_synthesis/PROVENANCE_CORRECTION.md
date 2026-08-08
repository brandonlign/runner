# Terminal synthesis provenance correction

Frozen after failed terminal-synthesis run `31229105304` and **before any corrected synthesis execution**.

The failed run stopped while downloading the second historical result artifact and never executed `synthesize.py`. It performed no external catalogue/web access and produced no scientific verdict.

Inspection of the authoritative completed GitHub Actions runs shows that the terminal workflow contained stale bookkeeping copied from an intermediate summary, not from the final uploaded artifacts:

## SAAMER 2020/2021

Authoritative run: `31210007928`, job `92970302753`.

Actual uploaded result artifact:
- artifact id `9006709213`;
- artifact name `orbittrace-label-free-v6-saamer-2020-2021-external`;
- ZIP SHA-256 `e96e262ac448bed6490b01dd98ceae752c7f3cdb3c87abffad5ee2693eb90dda`;
- exact result file `saamer_external_validation.json`.

Actual frozen outcome:
- verdict `INCONCLUSIVE_LABEL_FREE_V6_SAAMER_EXTERNAL_POWER`;
- recurrent families `N=69`;
- orbitally corroborated families `Q=29`.

The previous terminal draft incorrectly stated `N=19, Q=19` and referenced non-result artifact id `9006672467`. This correction is provenance-only. The scientific interpretation is unchanged: the panel is power-inconclusive under the unchanged external floors because `N<100` and `Q<30`.

## SAAMER 2022/2023

Authoritative run `31212256679` is unchanged:
- artifact `9007437717`;
- ZIP SHA-256 `0e4482d750d8dea93ef56205180b4d456aaedc4adb6dc04d9239a35ab32cab50`;
- `N=66`, `Q=33`;
- verdict `INCONCLUSIVE_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_POWER`.

## AMOR 1996/1998 direct v8

Authoritative run: `31221745373`, job `93007620441`.

Actual uploaded final corrected result artifact:
- artifact id `9010704319`;
- artifact name `orbittrace-v8-amor-1996-1998-external-validation-numeric-corrected`;
- ZIP SHA-256 `474cbd33dab03b7866da1e0b4c5640824347655e2d1ad336076a752291146763`;
- exact result file `v8_amor_1996_1998_external_validation.json`;
- verdict `INCONCLUSIVE_V8_AMOR_EXTERNAL_POWER`;
- `N=19`, `Q=19`.

The previous terminal workflow referenced stale artifact id `9010756922` and SHA `c264...`; this correction changes only provenance transport.

## Scientific boundary

No method parameter, external power floor, panel, result, pass/fail rule, or target boundary is changed. The corrected synthesis must still conclude only from already-frozen result artifacts, must not contact any external catalogue/web service, must not inspect new scientific values, and must keep OrbitTrace blinded.
