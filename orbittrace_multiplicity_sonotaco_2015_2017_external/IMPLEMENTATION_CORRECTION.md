# Fresh SonotaCo external-validation pre-data implementation correction

## Frozen predecessor execution

Workflow run `31199873243`, job `92937021020`, stopped in the prerequisite-artifact step before the first SonotaCo 2015/2017 archive request. The protocol/source guards passed. The scientific validation step was skipped.

No SonotaCo 2015 or 2017 archive was downloaded or requested by that run, so the fresh panel remained unaccessed.

## Exact cause

The workflow requested mapping-audit artifact name `gmn-mapping-audit-20260804` from authoritative run `30855193522`. The actual artifact name on that run is:

`real-shower-meta-data-audit`

Artifact `8872243828` contains `audit.json`. Independent inspection of that file gives SHA-256:

`f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`

which is exactly the mapping-audit SHA preregistered in the external-validation protocol and embedded in the validated SonotaCo parser.

## Allowed correction

The retry changes only the GitHub Actions artifact **name used to retrieve the already-frozen mapping-audit bytes**:

`gmn-mapping-audit-20260804 -> real-shower-meta-data-audit`.

The protocol, external-validation Python source, candidate method, parser sources, mapping-audit bytes/hash, survey years, archive URLs/members, fixed4 geometry/calibration, multiplicity ranking, scaled endpoint, validity gates, scientific pass gates, blindness boundary, and target-access rule remain unchanged.

The retry must again execute all pre-data source/freshness/parser/hash guards before the first SonotaCo archive request.
