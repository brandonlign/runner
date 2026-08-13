#!/usr/bin/env python3
from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
EXPECTED='5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb'
TOKENS=('clone','uncert','feature','radiant','eclip','vector')
def main():
    p=Path('/tmp/sugar_uncertainty_catalogue.py'); raw=p.read_bytes(); h=hashlib.sha256(raw).hexdigest(); assert h==EXPECTED
    text=raw.decode(); tree=ast.parse(text); constants={}; funcs={}
    for node in tree.body:
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            if len(targets)==1 and isinstance(targets[0],ast.Name):
                try: constants[targets[0].id]=ast.literal_eval(node.value)
                except Exception: pass
        elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            sig=ast.unparse(node.args); rec={'signature':sig,'lineno':node.lineno,'end_lineno':node.end_lineno}
            if any(t in node.name.lower() for t in TOKENS): rec['source']=ast.get_source_segment(text,node)
            funcs[node.name]=rec
    out={'verdict':'PASS_SUGAR_CLONE_SOURCE_INTERFACE_AUDIT_V1','source_sha256':h,'source_bytes':len(raw),'literal_constants':constants,'functions':funcs,'scientific_values_computed':0,'catalogue_rows_read':0,'labels_read':False,'target_information_access':False,'sonotaco_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    Path('output').mkdir(exist_ok=True); Path('output/SUGAR_CLONE_INTERFACE_AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n'); print(json.dumps({'verdict':out['verdict'],'functions':sorted(funcs),'constants':constants},indent=2,default=str))
if __name__=='__main__': main()
