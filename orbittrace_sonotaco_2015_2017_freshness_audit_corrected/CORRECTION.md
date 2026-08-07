# SonotaCo 2015/2017 freshness-audit implementation correction

## Frozen predecessor result

The first exposure-aware history audit ran as GitHub Actions run `31198105470` and returned `FAIL_SONOTACO_2015_2017_REPO_FRESHNESS_AUDIT` without downloading any SonotaCo archive or computing any scientific score.

That result is preserved. Its 2015 classification was clean and its spent-2016 positive control was correctly detected. The 2017 failure was caused by the audit matching its own provenance machinery: commit `d638126c051ba73a7eb043c5eca2984a5c9db6c9` contains the literal regex string `SNMv3/017` in `orbittrace_sonotaco_2017_2019_freshness_audit/audit_history.py`. That string describes what the earlier freshness audit should search for; it is not evidence that the 2017 archive was accessed.

## Implementation-only correction

The corrected audit keeps the same candidate years (2015, 2017), the same spent positive control (2016), and the same exact access markers. It changes only provenance classification:

- paths whose purpose is repository freshness/provenance auditing (`freshness_audit` or `freshness-audit` in the path) are excluded from **actual-data-access** classification;
- exact marker hits in those paths are still collected and serialized separately as `ignored_provenance_audit_hits` so they remain visible;
- real parser, workflow, result, archive, event-id, and non-audit SonotaCo+year branch hits remain exposure evidence;
- reservation-only prose remains descriptive and is not counted as data access.

The known spent SonotaCo 2016 year must still be detected as exposed. If the positive control fails, the corrected audit fails regardless of 2015/2017.

No SonotaCo archive may be downloaded by this correction or its workflow. No shower labels, detector scores, excluded target interval, or OrbitTrace target information may be accessed.
