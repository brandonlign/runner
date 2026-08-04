#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, re, zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlparse
import requests

PAGES={"v2016":"https://www.astro.sk/~ne/IAUMDC/PhV2016/video.html","v2020":"https://www.astro.sk/~ne/IAUMDC/PhVR2020/video.html"}
NAMES=("CAMS_California_v2.xlsx","CAMS_BeNeLux_v2.xlsx","CAMS_California_v2.1l","CAMS_BeNeLux_v2.1l","CAMS_by_date_v2.1l","formats.pdf")
HREF=re.compile(r'href\s*=\s*(["\'])(.*?)\1',re.I|re.S)

def sha(b): return hashlib.sha256(b).hexdigest()
def safe(n):
 p=PurePosixPath(n); return not p.is_absolute() and '..' not in p.parts and not n.startswith(('/', '\\'))
def fetch(s,u):
 r=s.get(u,timeout=300,allow_redirects=True); r.raise_for_status(); return r.content,r.url,r.headers.get('content-type')
def links(raw,base):
 out={n:[] for n in NAMES}
 for _,h in HREF.findall(raw.decode('latin-1')):
  h=h.strip(); n=PurePosixPath(unquote(urlparse(h).path)).name
  if n in out: out[n].append(urljoin(base,h))
 return out
def xlsx(raw):
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  bad=z.testzip(); infos=z.infolist()
  members=[{"name":i.filename,"bytes":i.file_size,"compressed_bytes":i.compress_size,"is_directory":i.is_dir()} for i in infos]
 names={m['name'] for m in members}; sheets=sorted(n for n in names if re.fullmatch(r'xl/worksheets/sheet[0-9]+\.xml',n))
 gates={"zip_crc":bad is None,"safe_paths":all(safe(m['name']) for m in members),"content_types":"[Content_Types].xml" in names,"workbook":"xl/workbook.xml" in names,"worksheet":bool(sheets)}
 return {"members":members,"worksheet_member_names":sheets,"member_content_opened":False,"gates":gates}

def build():
 s=requests.Session(); pages={}; resources={}
 for key,url in PAGES.items():
  raw,final,ct=fetch(s,url); found=links(raw,final)
  pages[key]={"requested_url":url,"final_url":final,"bytes":len(raw),"sha256":sha(raw),"href_match_counts":{n:len(found[n]) for n in NAMES}}
  resources[key]={}
  for n in NAMES:
   if len(found[n])!=1: raise RuntimeError(f'{key}: expected one href for {n}, found {found[n]}')
   b,u,t=fetch(s,found[n][0]); item={"basename":n,"resolved_url":found[n][0],"final_url":u,"bytes":len(b),"sha256":sha(b),"content_type":t}
   if n.endswith('.xlsx'): item['xlsx']=xlsx(b)
   elif n.endswith('.1l'): item['single_line']={"nonempty":bool(b),"decoded":False,"records_read":False}
   else: item['pdf']={"magic_ok":b.startswith(b'%PDF-'),"parsed":False,"pages_read":False}
   resources[key][n]=item
 identity={n:resources['v2016'][n]['sha256']==resources['v2020'][n]['sha256'] for n in NAMES}
 gates={
  "both_pages":len(pages)==2,
  "exact_hrefs":all(all(v==1 for v in p['href_match_counts'].values()) for p in pages.values()),
  "cross_version_identity":all(identity.values()),
  "xlsx_structure":all(all(resources[k][n]['xlsx']['gates'].values()) for k in PAGES for n in NAMES if n.endswith('.xlsx')),
  "one_line_nonempty":all(resources[k][n]['single_line']['nonempty'] for k in PAGES for n in NAMES if n.endswith('.1l')),
  "pdf_magic":all(resources[k]['formats.pdf']['pdf']['magic_ok'] for k in PAGES),
  "no_content_decoded":True,"reserved_panels_untouched":True}
 verdict='PASS_HISTORICAL_CAMSV2_TABULAR_STRUCTURAL_FEASIBILITY_V2' if all(gates.values()) else 'KILL_HISTORICAL_CAMSV2_TABULAR_STRUCTURAL_FEASIBILITY_V2'
 return {"method":"Historical CAMS Database 2.0 tabular structural feasibility v2","pages":pages,"resources":resources,"cross_version_resource_identity":identity,"workbook_member_content_opened":False,"single_line_text_decoded":False,"single_line_records_read":False,"documentation_pdf_parsed":False,"meteor_values_read":False,"label_values_read":False,"later_california_records_read":False,"benelux_meteor_values_read":False,"sonotaco_2024_read":False,"camsv3_2016_values_read":False,"gates":gates,"verdict":verdict}

def main():
 a=argparse.ArgumentParser(); a.add_argument('--output',required=True); o=Path(a.parse_args().output); o.mkdir(parents=True,exist_ok=True)
 try: r=build()
 except Exception as e: r={"method":"Historical CAMS Database 2.0 tabular structural feasibility v2","error":f'{type(e).__name__}: {e}',"workbook_member_content_opened":False,"single_line_text_decoded":False,"single_line_records_read":False,"documentation_pdf_parsed":False,"meteor_values_read":False,"label_values_read":False,"later_california_records_read":False,"benelux_meteor_values_read":False,"sonotaco_2024_read":False,"camsv3_2016_values_read":False,"gates":{"execution_completed":False},"verdict":"KILL_HISTORICAL_CAMSV2_TABULAR_STRUCTURAL_FEASIBILITY_V2"}
 (o/'tabular_structural_feasibility_v2.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 lines=['# Historical CAMS Database 2.0 tabular structural feasibility v2','',f"**Verdict:** `{r['verdict']}`",'']
 for n in NAMES:
  if 'resources' in r:
   x=r['resources']['v2016'][n]; lines += [f'## {n}','',f"- bytes: {x['bytes']}",f"- SHA-256: `{x['sha256']}`",f"- identical: {r['cross_version_resource_identity'][n]}",'']
 if r.get('error'): lines += ['## Error','',f"`{r['error']}`",'']
 lines += ['## Gates','']+[f'- {k}: {v}' for k,v in r.get('gates',{}).items()]+['','No worksheet XML, cell, single-line record, PDF page, meteor value, or label value was decoded.']
 (o/'RESULT.md').write_text('\n'.join(lines)+'\n'); print(json.dumps({"verdict":r['verdict'],"gates":r.get('gates'),"error":r.get('error')},indent=2))
 if r['verdict']!='PASS_HISTORICAL_CAMSV2_TABULAR_STRUCTURAL_FEASIBILITY_V2': raise SystemExit(1)
if __name__=='__main__': main()
