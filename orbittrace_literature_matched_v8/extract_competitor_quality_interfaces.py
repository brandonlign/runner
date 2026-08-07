#!/usr/bin/env python3
from __future__ import annotations
import ast, json
from pathlib import Path

TARGETS = {
    'hdbscan_2025.py': ['load_quality_sidecars','quality_pass','prepare_records','feature_matrix','run_hdbscan'],
    'hdbscan_2023.py': ['load_records','feature_matrix','run_hdbscan','hungarian_f1','size_strata'],
    'sugar_2025.py': ['load_sidecars','prepare_records','arrays_from_records','score_iteration'],
    'sugar_2023.py': ['load_sidecars','prepare_records','arrays_from_records','score_iteration'],
    'sugar_core.py': ['clone_feature_matrix','dbscan_clusters','hard_assignment'],
}

def functions(path: Path, names: list[str]) -> dict[str,str]:
    text=path.read_text()
    tree=ast.parse(text)
    out={}
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
            src=ast.get_source_segment(text,node)
            if src is None: raise RuntimeError(f'cannot extract {node.name}')
            out[node.name]=src
    missing=set(names)-set(out)
    # HDBSCAN 2023 has a transported monolithic loader; keep available functions and record misses.
    out['_missing_requested']=sorted(missing)
    return out

def main():
    root=Path('decoded_quality')
    result={name:functions(root/name,names) for name,names in TARGETS.items()}
    out=Path('output_quality_interface'); out.mkdir(parents=True,exist_ok=True)
    (out/'quality_interfaces.json').write_text(json.dumps(result,indent=2)+'\n')
    for name, funcs in result.items():
        print(f'=== {name} ===')
        for fn, src in funcs.items():
            print(f'--- {fn} ---')
            print(src if isinstance(src,str) else src)

if __name__=='__main__': main()
