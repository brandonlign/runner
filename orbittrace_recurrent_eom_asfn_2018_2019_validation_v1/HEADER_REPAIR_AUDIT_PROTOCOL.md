# ASFN hash-header repair semantic audit — frozen protocol

## Role

Engineering-only audit after binding ASFN validation attempt `31834974219` stopped before HDBSCAN, candidate generation, prelabel freeze, `shw` access, or any metric/result because physical line 1 was interpreted as a data record.

The separately frozen framing audit `31835297539` established without reporting scientific field values that the exact pinned data member begins with one hash-prefixed 45-token header followed by 44-token whitespace-delimited records. The scientific ASFN validation protocol, years, representation, blind interval, HDBSCAN settings, recurrent-EOM definition, ranking, evaluator, and gate remain unchanged.

This audit is frozen before evaluating the proposed wrapper semantics. It authorizes **no NASA network/archive/event access**.

## Frozen sources

- scientific validation runner Git blob: `8f5699326758dd11cc46f9a209049a8ed61dee3a`;
- proposed wrapper Git blob: `0e5fce5b04959ec45c42bb22ed477e48bdc31bde`;
- original framing-audit protocol Git blob: `960db109be82c8222f851be8a60f73969eaa4a80`;
- exact archive identity remains `c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4`, but this audit must not download or open it.

## Exact semantic claim to prove

The wrapper may modify only `header_or_record` at runtime. It must recognize an exact hash-prefixed header

`["#"] + list(FIELDS)`

as a header while preserving the frozen runner's behavior for all preregistered non-target cases.

Binding synthetic fixtures:

1. exact ordinary header `list(FIELDS)`: original=True, repaired=True;
2. exact hash-prefixed header `["#"] + list(FIELDS)`: original=False, repaired=True;
3. hash-prefixed header with one field changed: repaired call must raise `RuntimeError`;
4. hash-prefixed header shorter than `FIELDS`: repaired call must raise `RuntimeError`;
5. representative 44-token data-like row whose first token begins with a four-digit year: original=False, repaired=False;
6. blank token list: original=False, repaired=False;
7. arbitrary non-header text: original=False, repaired=False.

The audit must also prove that installing the wrapper does not alter the frozen module's `FIELDS`, `IDX`, `YEARS`, `BLIND`, `ARCHIVE_SHA`, `README_SHA`, `MIN_CLUSTER_SIZE`, or `MIN_SAMPLES` objects/values, and that the wrapper source contains no network/archive reads and no HDBSCAN/evaluator/scientific parameter reassignment.

## Binding verdict

PASS only if every requirement above holds exactly:

`PASS_ASFN_HASH_HEADER_REPAIR_SEMANTIC_AUDIT`

Otherwise:

`FAIL_ASFN_HASH_HEADER_REPAIR_SEMANTIC_AUDIT`

A FAIL forbids using this wrapper for a scientific retry. A PASS authorizes only a separately frozen retry wrapper/workflow using the byte-identical scientific runner and wrapper. It authorizes no scientific alteration.

## Firewall

Every output must assert:

- `network_access=false`;
- `asfn_archive_access=false`;
- `asfn_event_value_access=false`;
- `asfn_shw_access=false`;
- `scientific_endpoint=false`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`.
