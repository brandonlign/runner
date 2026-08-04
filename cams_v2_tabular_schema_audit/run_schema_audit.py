#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, re, unicodedata, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import requests

SOURCES={
 "California":("https://www.astro.sk/~ne/IAUMDC/PhV2016/CAMS_California_v2.xlsx",29150990,"3b4daf3dd5d20f99d250c872490393e020cd29dd5a17741c5c88b1678ca83ba4"),
 "BeNeLux":("https://www.astro.sk/~ne/IAUMDC/PhV2016/CAMS_BeNeLux_v2.xlsx",287061,"e35725616b966ba7956d6e60b22a8e3648db6d2e5eb7ea1865396a3da495c1a9")}
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'

def local(tag): return tag.rsplit('}',1)[-1]
def norm(s): return re.sub(r'[^a-z0-9]+','',unicodedata.normalize('NFKC',s).strip().lower())
def sha(b): return hashlib.sha256(b).hexdigest()

def workbook_name(z):
 root=ET.fromstring(z.read('xl/workbook.xml')); sheets=root.find(f'{{{NS}}}sheets')
 names=[x.attrib.get('name','') for x in list(sheets or [])]
 if len(names)!=1 or not names[0]: raise RuntimeError(f'unexpected workbook sheet names {names}')
 return names[0]

def first_row(z):
 p=ET.XMLPullParser(events=('start','end')); bytes_read=0; row_started=False; row_done=False; cells=[]
 with z.open('xl/worksheets/sheet1.xml') as f:
  while not row_done:
   b=f.read(1)
   if not b: raise RuntimeError('EOF before closing worksheet row 1')
   bytes_read+=1; p.feed(b)
   for event,e in p.read_events():
    t=local(e.tag)
    if event=='start' and t=='row':
     if row_started: raise RuntimeError('second row started before first row closed')
     if e.attrib.get('r') not in (None,'1'): raise RuntimeError(f'first worksheet row is {e.attrib.get("r")}')
     row_started=True
    elif event=='end' and t=='c' and row_started:
     ref=e.attrib.get('r',''); ctype=e.attrib.get('t','n')
     if e.find(f'{{{NS}}}f') is not None: raise RuntimeError(f'formula in header cell {ref}')
     v=e.find(f'{{{NS}}}v'); inline=e.find(f'{{{NS}}}is')
     if ctype=='s':
      if v is None or v.text is None: raise RuntimeError(f'missing shared-string index in {ref}')
      cells.append({'ref':ref,'kind':'shared','index':int(v.text)})
     elif ctype=='inlineStr':
      text=''.join((x.text or '') for x in inline.iter(f'{{{NS}}}t')) if inline is not None else ''
      cells.append({'ref':ref,'kind':'inline','text':text})
     else: raise RuntimeError(f'nontext header cell {ref} type {ctype}')
    elif event=='end' and t=='row' and row_started:
     row_done=True; break
 if not cells: raise RuntimeError('empty worksheet row 1')
 return cells,bytes_read

def shared_prefix(z,max_index):
 p=ET.XMLPullParser(events=('end',)); values=[]; bytes_read=0
 with z.open('xl/sharedStrings.xml') as f:
  while len(values)<=max_index:
   b=f.read(1)
   if not b: raise RuntimeError('EOF before required shared strings')
   bytes_read+=1; p.feed(b)
   for _,e in p.read_events():
    if local(e.tag)=='si':
     values.append(''.join((x.text or '') for x in e.iter() if local(x.tag)=='t'))
     if len(values)>max_index: break
 return values,bytes_read

def audit_one(name,url,size,digest):
 r=requests.get(url,timeout=300); r.raise_for_status(); raw=r.content
 if len(raw)!=size or sha(raw)!=digest: raise RuntimeError(f'{name}: source mismatch')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if z.testzip() is not None: raise RuntimeError(f'{name}: ZIP CRC failure')
  names=z.namelist()
  if names.count('xl/worksheets/sheet1.xml')!=1 or names.count('xl/sharedStrings.xml')!=1: raise RuntimeError(f'{name}: unexpected worksheet/sharedStrings members')
  sheet=workbook_name(z); cells,worksheet_bytes=first_row(z)
  shared_indices=[c['index'] for c in cells if c['kind']=='shared']
  if shared_indices:
   unique=sorted(set(shared_indices)); expected=list(range(max(unique)+1))
   if unique!=expected: raise RuntimeError(f'{name}: header shared-string indices are not contiguous from zero: {unique}')
   strings,shared_bytes=shared_prefix(z,max(unique))
  else: strings=[]; shared_bytes=0
 headers=[]
 for c in cells:
  text=strings[c['index']] if c['kind']=='shared' else c['text']
  if not text.strip(): raise RuntimeError(f'{name}: blank header at {c["ref"]}')
  headers.append({'ref':c['ref'],'text':text,'normalized':norm(text)})
 return {'name':name,'url':url,'bytes':size,'sha256':digest,'sheet_name':sheet,'row_number':1,'headers':headers,'worksheet_bytes_read_through_row1':worksheet_bytes,'shared_strings_resolved':len(strings),'shared_strings_bytes_read_through_last_header':shared_bytes,'row2_requested':False,'unreferenced_shared_strings_read':False}

def matches(vals,allowed): return [v for v in vals if v in allowed]
def build():
 books=[audit_one(name,*src) for name,src in SOURCES.items()]
 schemas=[[h['normalized'] for h in b['headers']] for b in books]
 vals=schemas[0]
 families={
  'solar_phase':matches(vals,{'ls','solarlongitude'}),
  'radiant_ra':matches(vals,{'ra','rightascension','radiantrightascension'}),
  'radiant_dec':matches(vals,{'dec','declination','radiantdeclination'}),
  'geocentric_speed':matches(vals,{'vg','geocentricspeed','geocentricvelocity'}),
  'native_shower_label':matches(vals,{'sh','showernumber'})}
 gates={'exact_sources':True,'row1_only':all(not b['row2_requested'] for b in books),'contiguous_header_shared_strings':all(not b['unreferenced_shared_strings_read'] for b in books),'identical_normalized_headers':schemas[0]==schemas[1],'unique_required_fields':all(len(v)==1 for v in families.values()),'explicit_native_label_header':len(families['native_shower_label'])==1,'reserved_panels_untouched':True}
 verdict='PASS_HISTORICAL_CAMSV2_XLSX_SCHEMA' if all(gates.values()) else 'KILL_HISTORICAL_CAMSV2_XLSX_SCHEMA'
 return {'method':'Historical CAMS Database 2.0 XLSX schema-only audit','workbooks':books,'normalized_headers':vals,'field_matches':families,'worksheet_data_rows_read':0,'meteor_values_read':False,'label_values_read':False,'single_line_files_read':False,'formats_pdf_read':False,'later_california_rows_read':False,'benelux_meteor_rows_read':False,'sonotaco_2024_read':False,'camsv3_2016_values_read':False,'gates':gates,'verdict':verdict}

def main():
 a=argparse.ArgumentParser(); a.add_argument('--output',required=True); o=Path(a.parse_args().output); o.mkdir(parents=True,exist_ok=True)
 try:r=build()
 except Exception as e:r={'method':'Historical CAMS Database 2.0 XLSX schema-only audit','error':f'{type(e).__name__}: {e}','worksheet_data_rows_read':0,'meteor_values_read':False,'label_values_read':False,'single_line_files_read':False,'formats_pdf_read':False,'later_california_rows_read':False,'benelux_meteor_rows_read':False,'sonotaco_2024_read':False,'camsv3_2016_values_read':False,'gates':{'execution_completed':False},'verdict':'KILL_HISTORICAL_CAMSV2_XLSX_SCHEMA'}
 (o/'xlsx_schema_audit.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 lines=['# Historical CAMS Database 2.0 XLSX schema-only audit','',f"**Verdict:** `{r['verdict']}`",'',f"- normalized headers: `{r.get('normalized_headers')}`",f"- field matches: `{r.get('field_matches')}`",'','## Gates','']+[f'- {k}: {v}' for k,v in r.get('gates',{}).items()]
 if r.get('error'): lines += ['','## Error','',f"`{r['error']}`"]
 lines += ['','No worksheet data row, meteor value, or label value was read.']
 (o/'RESULT.md').write_text('\n'.join(lines)+'\n'); print(json.dumps({'verdict':r['verdict'],'headers':r.get('normalized_headers'),'field_matches':r.get('field_matches'),'gates':r.get('gates'),'error':r.get('error')},indent=2))
 if r['verdict']!='PASS_HISTORICAL_CAMSV2_XLSX_SCHEMA': raise SystemExit(1)
if __name__=='__main__':main()
