#!/usr/bin/env python3
import hashlib,sys
from pathlib import Path
EXPECTED={
 'quality':'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990',
 'v8':'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b',
 'p19':'276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'}
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    q,v,p=sys.argv[1:4]
    assert h(q)==EXPECTED['quality']; assert h(v)==EXPECTED['v8']; assert h(p)==EXPECTED['p19']
    print('PASS_GMN_V31_UNCERTAINTY_PACKAGE_INPUT_GUARD')
if __name__=='__main__': main()
