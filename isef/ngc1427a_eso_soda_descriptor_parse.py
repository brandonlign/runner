#!/usr/bin/env python3
"""Metadata-only parser for the ESO SODA descriptor advertised for NGC1427A."""
import json,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
DP='ADP.2026-06-24T16:04:14.194'; ID='ivo://eso.org/ID?'+DP
URL='https://archive.eso.org/datalink/links?'+urllib.parse.urlencode({'ID':ID})
OUT=Path('results/ngc1427a_eso_soda_descriptor_parse.json');OUT.parent.mkdir(exist_ok=True)
o={'status':'METADATA_ONLY_DESCRIPTOR','science_data_accessed':False,'success':False,'id':ID}
try:
 req=urllib.request.Request(URL,headers={'User-Agent':'ISEF-NGC1427A-SODA-descriptor/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r: raw=r.read()
 root=ET.fromstring(raw); ns={'v':'http://www.ivoa.net/xml/VOTable/v1.3'}
 target=None
 for res in root.findall('.//v:RESOURCE',ns):
  if res.attrib.get('ID')==DP+'_soda': target=res;break
 if target is None: raise RuntimeError('SODA resource not found')
 params=[]
 for p in target.findall('.//v:PARAM',ns):
  rec={'name':p.attrib.get('name'),'value':p.attrib.get('value'),'datatype':p.attrib.get('datatype'),'unit':p.attrib.get('unit'),'xtype':p.attrib.get('xtype'),'arraysize':p.attrib.get('arraysize')}
  vals=p.find('v:VALUES',ns)
  if vals is not None:
   mn=vals.find('v:MIN',ns);mx=vals.find('v:MAX',ns)
   if mn is not None: rec['min']=mn.attrib.get('value')
   if mx is not None: rec['max']=mx.attrib.get('value')
   opts=[x.attrib.get('value') for x in vals.findall('v:OPTION',ns)];
   if opts: rec['options']=opts
  desc=p.find('v:DESCRIPTION',ns)
  if desc is not None and desc.text: rec['description']=' '.join(desc.text.split())
  params.append(rec)
 o['params']=params
 o['access_url']=next((p['value'] for p in params if p['name']=='accessURL'),None)
 o['standard_id']=next((p['value'] for p in params if p['name']=='standardID'),None)
 o['success']=True
except Exception as e:o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
