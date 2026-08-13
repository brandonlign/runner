#!/usr/bin/env python3
import argparse,ast,base64,gzip,hashlib,json
from pathlib import Path
P=('70b431705fc4fd67f45a86b254a3d81dad35955de4d24af459f142cf13146e19','800bacef71c7ab7f7e35c7c52bcd4b1afef8056aa7e0317c91049201b913b894','b78cab4c6605b1bb94b4ed9656a37266b23fe0be6a4d3261aad289d17b70ab2c')
def main():
 p=argparse.ArgumentParser();p.add_argument('--parts',type=Path,required=True);a=p.parse_args();z=[]
 for i,h in enumerate(P):
  q=a.parts/f'part{i:02d}.b64';assert hashlib.sha256(q.read_bytes()).hexdigest()==h;z.append(''.join(q.read_text().split()))
 raw=gzip.decompress(base64.b64decode(''.join(z),validate=True));assert hashlib.sha256(raw).hexdigest()=='5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb';s=raw.decode();t=ast.parse(s);want={'_positive_gaussian','_reflect_declination','stable_seed'};out={}
 for n in t.body:
  if isinstance(n,ast.FunctionDef) and n.name in want: out[n.name]=ast.get_source_segment(s,n)
 assert set(out)==want;Path('output').mkdir(exist_ok=True);Path('output/SUGAR_CLONE_HELPERS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
