#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, re
from pathlib import Path
import requests
from pypdf import PdfReader

URL='https://www.astro.sk/~ne/IAUMDC/PhV2016/formats.pdf'
SIZE=62530
SHA='2cb0f754a81fe62c41f2b106c1e82750a38f38725a459591111d084f210e1924'

def build():
 r=requests.get(URL,timeout=300); r.raise_for_status(); raw=r.content; digest=hashlib.sha256(raw).hexdigest()
 if len(raw)!=SIZE or digest!=SHA: raise RuntimeError(f'source mismatch bytes={len(raw)} sha256={digest}')
 reader=PdfReader(io.BytesIO(raw)); text='\n'.join((p.extract_text() or '') for p in reader.pages)
 start=text.lower().find('reduced data: meteor in a single line')
 if start<0: raise RuntimeError('reduced-data heading not found')
 end=text.lower().find('old iau mdc format',start+1)
 if end<0: raise RuntimeError('next section heading not found')
 section=text[start:end]
 codes=[]
 for code in ('IC','yr','mn','day','q','e','i','arg','nod','RA','DEC','Vg','Vh'):
  if re.search(rf'(?<![A-Za-z0-9]){re.escape(code)}(?![A-Za-z0-9])',section,re.I): codes.append(code)
 required={
  'LS':bool(re.search(r'(?<![A-Za-z0-9])LS(?![A-Za-z0-9])|solar\s+longitude',section,re.I)),
  'RA':bool(re.search(r'(?<![A-Za-z0-9])RA(?![A-Za-z0-9])|right\s+ascension',section,re.I)),
  'DEC':bool(re.search(r'(?<![A-Za-z0-9])DEC(?![A-Za-z0-9])|declination',section,re.I)),
  'Vg':bool(re.search(r'(?<![A-Za-z0-9])Vg(?![A-Za-z0-9])|geocentric\s+velocity',section,re.I)),
  'Sh':bool(re.search(r'(?<![A-Za-z0-9])Sh(?![A-Za-z0-9])|shower\s+number',section,re.I))}
 gates={'exact_document':True,'reduced_section_identified':True,'required_fields_all_explicit':all(required.values()),'no_data_resource_requested':True,'reserved_panels_untouched':True}
 verdict='PASS_HISTORICAL_CAMSV2_SINGLE_LINE_SCHEMA' if all(gates.values()) else 'KILL_HISTORICAL_CAMSV2_SINGLE_LINE_SCHEMA'
 return {'method':'Historical CAMS Database 2.0 single-line schema audit','source':{'url':URL,'bytes':len(raw),'sha256':digest,'pages':len(reader.pages)},'reduced_parameter_codes':codes,'required_field_presence':required,'single_line_records_read':0,'meteor_values_read':False,'label_values_read':False,'later_california_records_read':False,'benelux_data_requested':False,'sonotaco_2024_read':False,'camsv3_2016_values_read':False,'gates':gates,'verdict':verdict}

def main():
 a=argparse.ArgumentParser(); a.add_argument('--output',required=True); o=Path(a.parse_args().output); o.mkdir(parents=True,exist_ok=True)
 try:r=build()
 except Exception as e:r={'method':'Historical CAMS Database 2.0 single-line schema audit','error':f'{type(e).__name__}: {e}','single_line_records_read':0,'meteor_values_read':False,'label_values_read':False,'later_california_records_read':False,'benelux_data_requested':False,'sonotaco_2024_read':False,'camsv3_2016_values_read':False,'gates':{'execution_completed':False},'verdict':'KILL_HISTORICAL_CAMSV2_SINGLE_LINE_SCHEMA'}
 (o/'single_line_schema_audit.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 (o/'RESULT.md').write_text('# Historical CAMS Database 2.0 single-line schema audit\n\n'+f"**Verdict:** `{r['verdict']}`\n\n- reduced codes: `{r.get('reduced_parameter_codes')}`\n- required fields: `{r.get('required_field_presence')}`\n\n## Gates\n\n"+'\n'.join(f'- {k}: {v}' for k,v in r.get('gates',{}).items())+'\n\nNo `.1l` meteor record was requested or read.\n')
 print(json.dumps({'verdict':r['verdict'],'codes':r.get('reduced_parameter_codes'),'required':r.get('required_field_presence'),'gates':r.get('gates'),'error':r.get('error')},indent=2))
 if r['verdict']!='PASS_HISTORICAL_CAMSV2_SINGLE_LINE_SCHEMA': raise SystemExit(1)
if __name__=='__main__':main()
