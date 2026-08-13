#!/usr/bin/env python3
import hashlib,os
from pathlib import Path
import guarded_run
import orbittrace_v15_canonical_events_v1.canonical as canonical

COMMON_PINS=((guarded_run.core.application,'orbittrace_v15_canonical_application_v1/application.py','5b3244dfbcc7bc931925aea42866edc8205113a8'),(canonical,'orbittrace_v15_canonical_events_v1/canonical.py','674eaec2acd8bf908bde797243c9414f0fa9559d'))
def blob(path):
    raw=path.read_bytes(); return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def guard_common():
    root=Path(os.environ.get('ORBITTRACE_FROZEN_COMMON_ROOT','')).resolve(); guarded_run.core.need(root.is_dir(),'ORBITTRACE_FROZEN_COMMON_ROOT missing')
    for module,rel,want in COMMON_PINS:
        path=(root/rel).resolve(); guarded_run.core.need(Path(module.__file__).resolve()==path,f'import escaped frozen common root: {rel}'); guarded_run.core.need(blob(path)==want,f'frozen common source drift: {rel}')
def guard_all():
    guard_common(); guarded_run.guard_imports()
def main():
    guard_all(); guarded_run.main()
if __name__=='__main__': main()
