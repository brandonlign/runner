#!/usr/bin/env python3
"""Read the official GravPot16 data-model page; schema only, no source rows."""
from pathlib import Path
import html,json,re,urllib.request
OUT=Path('results/sdss_dr20_gravpot16_datamodel_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
URL='https://data.sdss.org/datamodel/files/MWM_ORBITS/GravPot16.html'
out={'success':False,'status':'SCHEMA_ONLY','source_rows_accessed':False,'url':URL}
try:
 req=urllib.request.Request(URL,headers={'User-Agent':'ISEF-DR20-GravPot16-Datamodel/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r:raw=r.read().decode('utf-8','replace')
 text=html.unescape(re.sub(r'<[^>]+>',' ',raw));text=' '.join(text.split())
 out['text']=text[:100000]
 terms=['unbound','bound','escape','energy','jacobi','etot','e_tot','eccentric','apogal','perigal','velocity','probability']
 out['term_snippets']={}
 low=text.lower()
 for term in terms:
  starts=[];p=0
  while True:
   i=low.find(term,p)
   if i<0 or len(starts)>=12:break
   starts.append(text[max(0,i-180):min(len(text),i+420)]);p=i+len(term)
  out['term_snippets'][term]=starts
 # Extract obvious FITS column-ish tokens from table markup/text.
 toks=sorted(set(re.findall(r'\b[A-Za-z][A-Za-z0-9_]{2,40}\b',text)))
 out['candidate_schema_tokens']=[x for x in toks if any(k in x.lower() for k in ['ener','jac','apo','peri','ecc','vel','prob','bound','esc','sdss','gaia'])][:500]
 out['success']=True;out['decision']='GRAVPOT16_OFFICIAL_DATAMODEL_READ'
except Exception as e:
 out['error_type']=type(e).__name__;out['error']=str(e)[:1000]
OUT.write_text(json.dumps(out,indent=2,sort_keys=True));print(OUT.read_text())
