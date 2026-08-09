#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('p14_direct_v1',HERE/'generate_matched_pretruth_direct.py')
if spec is None or spec.loader is None:
    raise RuntimeError('cannot load P14 direct generator v1')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def replace_between_consume(text:str,start:str,end:str,repl:str,label:str)->str:
    i=text.find(start); j=text.find(end,i+len(start)) if i>=0 else -1
    if i<0 or j<0: raise RuntimeError(f'P14 direct v2 span missing {label}')
    if text.find(start,i+1)>=0: raise RuntimeError(f'P14 direct v2 span nonunique {label}')
    j+=len(end)
    return text[:i]+repl+text[j:]

m.replace_between=replace_between_consume

if __name__=='__main__':
    raise SystemExit(m.main())
