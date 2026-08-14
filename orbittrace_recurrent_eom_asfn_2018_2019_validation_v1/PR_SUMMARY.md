# ASFN pristine validation result summary

**NEGATIVE binding external result.** Recurrent-EOM HDBSCAN v1 failed the pre-frozen NASA ASFN 2018/2019 pristine cross-survey gate against vanilla HDBSCAN EOM.

Binding run `31850437866`, artifact `9237338312`, digest `sha256:cebe8abd80899c5cfb27758f373f11882a309e501f2c22775881df0184fa83b6`.

The exact frozen archive and method ran successfully after two preserved technical no-results and independently audited parser/transport repairs. The valid endpoint used 4,679 retained 2018 events and 4,548 retained 2019 events.

Vanilla and recurrent-EOM each produced 34 candidates and the recurrent selected-node set was identical (`mechanism_active=false`). Recovery was identical at every reported budget (2018: 13; 2019: 11), while recurrent-EOM MRR was slightly lower in both years. No strict @100 gain occurred. Exact verdict: `FAIL_RECURRENT_EOM_HDBSCAN_V1_ASFN_2018_2019_PRISTINE_VALIDATION`.

This is genuine pristine cross-survey negative evidence and permanently forbids ASFN-specific rescue. Recurrent-EOM remains the promoted development parent because no successor has replaced it, but it cannot currently be claimed as cross-survey externally validated.
