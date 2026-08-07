#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

PAGE='https://ceres.ta3.sk/iaumdcdb/home/catalog/radio'
DOC='https://ceres.ta3.sk/iaumdcdb/public/docs/HISSAR_documentation.pdf'
PARAMS=('DB','IC','Yr','Mn','Day','LS','RA','DEC','Vg','q','e','i','arg','nod')

class Forms(HTMLParser):
    def __init__(self): super().__init__(); self.forms=[]; self.cur=None; self.select=None; self.option=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='form': self.cur={'method':a.get('method','get').lower(),'action':a.get('action',''),'controls':[]}; self.forms.append(self.cur)
        elif self.cur is not None and tag in ('input','button'):
            self.cur['controls'].append({'tag':tag,'name':a.get('name'),'type':a.get('type'),'value':a.get('value')})
        elif self.cur is not None and tag=='select':
            self.select={'tag':'select','name':a.get('name'),'options':[]}; self.cur['controls'].append(self.select)
        elif self.select is not None and tag=='option': self.option={'value':a.get('value'),'text':''}; self.select['options'].append(self.option)
    def handle_data(self,data):
        if self.option is not None: self.option['text'] += data.strip()
    def handle_endtag(self,tag):
        if tag=='option': self.option=None
        elif tag=='select': self.select=None
        elif tag=='form': self.cur=None

def get(url,path):
    req=urllib.request.Request(url,headers={'User-Agent':'OrbitTrace-Hissar-structure-audit/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r: path.write_bytes(r.read())

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--freshness-json',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    f=json.loads(a.freshness_json.read_text()); assert f['verdict']=='PASS_HISSAR_1968_1969_ZERO_DATA_FRESHNESS_ADJUDICATION'; assert f['scientific_record_access'] is False
    htmlp=a.output/'radio.html'; pdfp=a.output/'HISSAR_documentation.pdf'; txtp=a.output/'HISSAR_documentation.txt'
    get(PAGE,htmlp); get(DOC,pdfp)
    html=htmlp.read_text(errors='replace'); parser=Forms(); parser.feed(html)
    subprocess.run(['pdftotext','-layout',str(pdfp),str(txtp)],check=True); doc=txtp.read_text(errors='replace')
    doc_gates={
      'record_count_8916': bool(re.search(r'8916\s+radio-meteor records',doc,re.I)),
      'period_1968_1969': 'December 1968 to October 1969 and in December 1969' in doc,
      'equinox_2000': bool(re.search(r'positional parameters\s+are referred to the equinox 2000\.0',doc,re.I)),
      'ls_solar_longitude': bool(re.search(r'LS\s*:.*solar longitude',doc,re.I)),
      'ra_geocentric': bool(re.search(r'RA\s*:.*right ascension of geocentric radiant',doc,re.I)),
      'dec_geocentric': bool(re.search(r'DEC\s*:.*declination of geocentric radiant',doc,re.I)),
      'vg_geocentric': bool(re.search(r'Vg\s*:.*geocentric velocity',doc,re.I)),
      'orbit_fields': all(x in doc for x in ('q :','e :','i :','arg:','nod:')),
      'ic_unique': 'unique identification code' in doc.lower(),
      'single_line_format': 'meteor in a single line' in doc.lower(),
    }
    page_gates={'hissar_present':'Hissar' in html,'time_extent_present':'1968' in html and '1969' in html,'parameters_present':all(re.search(r'(?<![A-Za-z0-9_])'+re.escape(p)+r'(?![A-Za-z0-9_])',html) for p in PARAMS),'form_present':len(parser.forms)>=1}
    schemas=[]
    for form in parser.forms:
        schemas.append({'method':form['method'],'action':urljoin(PAGE,form['action'] or PAGE),'controls':form['controls']})
    deterministic=any(x['method'] in ('get','post') and bool(x['action']) for x in schemas); page_gates['deterministic_form_schema']=deterministic
    passed=all(doc_gates.values()) and all(page_gates.values())
    result={'verdict':'PASS_HISSAR_1968_1969_STRUCTURE_AUDIT' if passed else 'FAIL_HISSAR_1968_1969_STRUCTURE_AUDIT','page_sha256':sha(htmlp),'documentation_sha256':sha(pdfp),'documentation_gates':doc_gates,'page_gates':page_gates,'forms':schemas,'allowed_get_urls':[PAGE,DOC],'form_submitted':False,'result_endpoint_contacted':False,'scientific_record_access':False,'scientific_values_inspected':False,'source_labels_inspected':False,'orbittrace_target_information_access':False,'claim_boundary':'Public page/form structure and official Hissar documentation only; no form submission or meteor row access.'}
    (a.output/'hissar_1968_1969_structure_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    htmlp.unlink(); pdfp.unlink(); txtp.unlink(); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())
