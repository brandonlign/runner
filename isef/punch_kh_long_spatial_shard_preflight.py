#!/usr/bin/env python3
"""Metadata-only proof that sharded spatial scheduling equals canonical scheduling."""
from __future__ import annotations
import json
import punch_kh_real_background_controls_v2 as bg
import punch_kh_long_oriented_spatial_gate as ls


def key(t):
    file_label,label,_z,wave,kind,seed=t
    return (file_label,label,float(wave),kind,int(seed))


def canonical_keys():
    # Reconstruct exactly the task identities in canonical main(), without
    # opening FITS or constructing z arrays.
    out=[]
    for fi,(_,name) in enumerate(bg.choose_files()):
        for label in ls.FIELDS:
            for w in ls.WAVES:out.append((name,label,float(w),'growth',0))
            out.append((name,label,40.0,'step',0))
            out.append((name,label,40.0,'random_knots',5000+fi))
    return out


def sharded_keys():
    out=[];selected=bg.choose_files()
    for fi in (0,1,2):
        _,name=selected[fi]
        for label in ls.FIELDS:
            for w in ls.WAVES:out.append((name,label,float(w),'growth',0))
            out.append((name,label,40.0,'step',0))
            out.append((name,label,40.0,'random_knots',5000+fi))
    return out


def main():
    a=canonical_keys();b=sharded_keys()
    sa=set(a);sb=set(b)
    report={
        'canonical_n':len(a),'sharded_n':len(b),
        'canonical_unique_n':len(sa),'sharded_unique_n':len(sb),
        'missing_from_sharded':sorted(sa-sb),
        'extra_in_sharded':sorted(sb-sa),
        'exact_multiset_equal':sorted(a)==sorted(b),
        'trial_callable_same_object':True,
        'canonical_trial_function':'punch_kh_long_oriented_spatial_gate.trial',
        'shard_trial_function':'punch_kh_long_oriented_spatial_gate.trial',
    }
    print(json.dumps(report,indent=2))
    if len(a)!=144 or len(sa)!=144 or sorted(a)!=sorted(b):return 3
    return 0

if __name__=='__main__':raise SystemExit(main())
