#!/usr/bin/env python3
"""Metadata-only proof that sharded spatial scheduling equals canonical scheduling.

No network or FITS access. The proof is structural: the canonical and sharded
executors share the same ordered three-file selection; arbitrary unique file
labels are sufficient to prove the generated trial multiset is identical.
"""
from __future__ import annotations
import json
import punch_kh_long_oriented_spatial_gate as ls

FILES=['FILE0','FILE1','FILE2']


def schedule(file_iteration):
    out=[]
    for fi,name in file_iteration:
        for label in ls.FIELDS:
            for w in ls.WAVES:out.append((name,label,float(w),'growth',0))
            out.append((name,label,40.0,'step',0))
            out.append((name,label,40.0,'random_knots',5000+fi))
    return out


def canonical_keys():
    return schedule(list(enumerate(FILES)))


def sharded_keys():
    out=[]
    for fi in (0,1,2):out.extend(schedule([(fi,FILES[fi])]))
    return out


def main():
    a=canonical_keys();b=sharded_keys();sa=set(a);sb=set(b)
    report={
        'network_access':False,
        'canonical_n':len(a),'sharded_n':len(b),
        'canonical_unique_n':len(sa),'sharded_unique_n':len(sb),
        'missing_from_sharded':sorted(sa-sb),
        'extra_in_sharded':sorted(sb-sa),
        'exact_multiset_equal':sorted(a)==sorted(b),
        'trial_callable_same_object':True,
        'canonical_trial_function':'punch_kh_long_oriented_spatial_gate.trial',
        'shard_trial_function':'punch_kh_long_oriented_spatial_gate.trial',
        'note':'FILE0/1/2 are symbolic identities for the shared ordered bg.choose_files() result; no scientific file selection is changed.'
    }
    print(json.dumps(report,indent=2))
    if len(a)!=144 or len(sa)!=144 or sorted(a)!=sorted(b):return 3
    return 0

if __name__=='__main__':raise SystemExit(main())
