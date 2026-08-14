# NASA ASFN archive readme-only preaccess v1 — result

**Classification: POSITIVE. Scientific data member remains unopened.**

Binding run: `31834608514`  
Artifact: `9231986592`  
Artifact digest: `sha256:bf8e75a39cf1bbd1fba988181c7fc77824cc50f8165b6b7a2617fac00ac1fa34`

Exact downloaded archive:

- SHA-256 `c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4`
- 4,326,351 bytes

Central directory contains exactly the expected scientific and documentation members:

- `nasfn_2013-2019_readme.txt`: 2,997 bytes, SHA-256 `74bacb50b225032461ba8b200eec0d5274799ef3c2700cb9a3465b4d5c02a2bf`
- `nasfn_2013-2019_data.txt`: 11,275,430 uncompressed bytes / 4,324,489 compressed bytes

Only the readme member was opened. The data member was not extracted, streamed, sampled, grepped, counted, or inspected.

The readme independently documents recurrent-EOM's required fields and units:

- `slon`: solar longitude, degrees;
- `lam_g`: geocentric ecliptic longitude of radiant, degrees;
- `bet_g`: geocentric ecliptic latitude, degrees;
- `v_g`: geocentric speed, km/s;
- `time`: UT event time in `YYYYMMDD-hh:mm:ss` format;
- `shw`: shower-association code, text field.

Verdict: `PASS_NASA_ASFN_README_RECURRENT_EOM_PREACCESS`.

This authorizes freezing a complete ASFN scientific evaluation protocol before the first data-row inspection. No result-informed quality cuts are authorized.

Firewall: `asfn_archive_download=true`, `asfn_data_member_extracted=false`, `asfn_data_member_opened=false`, `asfn_event_value_access=false`, `target_information_access=false`, `target_region_events_accessed=false`, `maarsy_scientific_access=false`, `dms_scientific_access=false`.
