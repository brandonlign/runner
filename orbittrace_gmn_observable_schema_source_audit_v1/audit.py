#!/usr/bin/env python3
from __future__ import annotations
import ast, base64, gzip, hashlib, json
from pathlib import Path

parts=sorted(Path('orbittrace_fixed4_support_wrapper_development/source_parts').glob('part*.b64'))
if len(parts)!=4: raise RuntimeError('expected 4 source parts')
source=gzip.decompress(base64.b64decode(''.join(p.read_text().strip() for p in parts))).decode()
ast.parse(source); lines=source.splitlines()
needles=('bin_strength','anchor_count','exact_anchor_distances','quartet_score','calibration','MondrianWindowFactory','retained')
hits=[]
for i,line in enumerate(lines,1):
    if any(n.lower() in line.lower() for n in needles):
        lo=max(1,i-10); hi=min(len(lines),i+16)
        hits.append({'hit_line':i,'context':[{'line':j,'text':lines[j-1]} for j in range(lo,hi+1)]})
out={'verdict':'PASS_FROZEN_GMN_BIN_STRENGTH_SOURCE_AUDIT_V1','scientific_data_accessed':False,'decoded_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'hits':hits}
Path('output').mkdir(exist_ok=True); Path('output/GMN_BIN_STRENGTH_SOURCE_AUDIT_V1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
