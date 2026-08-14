# Adelaide radar zero-data scientific-freshness audit v1 — binding result

**Classification: NEGATIVE freshness for pristine-validation use; no Adelaide scientific/event row was opened.**

Binding run: `31832702369`  
Artifact: `9231289541`  
Artifact digest: `sha256:b47caac347ea4dc39ad3f69c5216e3071885512ce094aafa008326c686e2e6ea`

Verdict: `FAIL_ADELAIDE_ZERO_DATA_REPO_FRESHNESS_AUDIT`.

## Exact history finding

The full reachable-history scan had:

- `ade6061`: zero hits;
- `ade6869`: zero hits;
- `ade6061.tab`: zero hits;
- `ade6869.tab`: zero hits;
- `Adelaide radar`: zero hits;
- `Adelaide Meteor`: zero hits;
- branch/ref-name hits: zero;
- generic `Adelaide`: exactly one historical hit.

That sole hit is commit `933970f812f157eb7e48d36a698823ee74cbf584`, file `orbittrace_v8_obninsk_1967_1968_preaccess/PROTOCOL.md`.

The historical text is metadata-level, not event-level. It states that the Obninsk candidate was selected from public NASA/PDS metadata as the largest newly identified multi-year survey, and explicitly says:

> `Adelaide and Mogadisho are smaller. No event-level value from any candidate was inspected to make this choice.`

Thus there is no evidence that an Adelaide meteor row was opened historically. However, the prior exposure concerns the **same Adelaide/PDS candidate family** and was used in a survey-selection decision. The frozen Adelaide audit protocol required no fixed Adelaide indicator anywhere in prior reachable history and specified that a FAIL closes Adelaide as a pristine external-validation route unless the prior exposure can be independently shown to concern a disjoint dataset.

That disjoint-dataset exception is not satisfied here. The prior text is explicitly about the PDS Adelaide candidate under consideration.

## Binding consequence

Do **not** reinterpret the failed audit as a PASS merely because the historical exposure was metadata-only.

For recurrent-EOM v1:

`CLOSE_ADELAIDE_AS_PRISTINE_EXTERNAL_VALIDATION_PRIOR_METADATA_SELECTION_EXPOSURE`

- Adelaide scientific/event values remain unopened by this audit.
- No Adelaide PDS `.tab` file is authorized under this pristine-validation route.
- Do not weaken the history pattern list or rerun freshness without the generic `Adelaide` term.
- Do not claim wholly pristine survey selection for Adelaide.

This is a **freshness/governance failure**, not evidence that recurrent-EOM performs poorly on Adelaide.

## Firewall

- `network_access=false`
- `adelaide_catalogue_access=false`
- `adelaide_label_access=false`
- `adelaide_event_value_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
