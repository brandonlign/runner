from __future__ import annotations

import csv, hashlib, html, io, json, math, re, urllib.error, urllib.parse, urllib.request
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from statistics import median

BASE='https://ceresiaumdc.ta3.sk/'
MDC=urllib.parse.urljoin(BASE,'downloads/lists_shw_data/streamfulldata.json')
DETAIL=urllib.parse.urljoin(BASE,'shower/111')
FILENAME='0149NOP_004.csv'
UA='ghoststream-nop-solution004-audit/1.1'
FIXED=(FILENAME,f'downloads/{FILENAME}',f'download/{FILENAME}',f'lookup/{FILENAME}',f'lookups/{FILENAME}',f'lookup_table/{FILENAME}',f'lookup_tables/{FILENAME}',f'data/{FILENAME}',f'data/lookup_tables/{FILENAME}',f'downloads/lookup_tables/{FILENAME}',f'downloads/lookup_tables_data/{FILENAME}',f'downloads/lists_shw_data/{FILENAME}',f'static/{FILENAME}',f'static/data/{FILENAME}',f'media/{FILENAME}',f'files/{FILENAME}')
ALIASES={
 'sol':{'ls','los','sol','solarlongitude','lambda','lambdasun','sollon','sc'},
 'ra':{'ra','radiantalpha','rightascension','alphag','rag'},
 'dec':{'de','dec','declination','radiantdelta','deltag','deg'},
 'vg':{'vg','vgeo','geocentricspeed','velocity','geocentricvelocity'},
 'q':{'q','periheliondistance'},'e':{'e','eccentricity'},
 'inc':{'inc','i','inclination'},'peri':{'peri','argperi','argumentofperihelion','w'},
 'node':{'node','ascendingnode','longitudeofascendingnode','bigomega'},
}

def norm(s):
 s=html.unescape(str(s or '')).replace('Ω','bigomega').replace('ω','omega').replace('λ','lambda').replace('☉','sun').lower()
 return re.sub('[^a-z0-9]+','',s)
def num(x):
 try:
  v=float(str(x).strip().replace('−','-'))
  return v if math.isfinite(v) else None
 except Exception:return None
def cdelta(a,b):return (a-b+180)%360-180
def mednear(vals,ref):return median([ref+cdelta(v,ref) for v in vals])%360
def sep(ra1,de1,ra2,de2):
 a,d,b,e=map(math.radians,(ra1,de1,ra2,de2)); c=math.sin(d)*math.sin(e)+math.cos(d)*math.cos(e)*math.cos(a-b)
 return math.degrees(math.acos(max(-1,min(1,c))))
def dsh(a,b):
 q1,e1,i1,w1,o1=[a[k] for k in ('q','e','inc','peri','node')];q2,e2,i2,w2,o2=[b[k] for k in ('q','e','inc','peri','node')]
 i1,w1,o1,i2,w2,o2=map(math.radians,(i1,w1,o1,i2,w2,o2));do=math.atan2(math.sin(o1-o2),math.cos(o1-o2))
 I=math.acos(max(-1,min(1,math.cos(i1)*math.cos(i2)+math.sin(i1)*math.sin(i2)*math.cos(do))))
 P=w1-w2+2*math.asin(max(-1,min(1,math.cos((i1+i2)/2)*math.sin(do/2)/max(math.cos(I/2),1e-12))))
 return math.sqrt((e1-e2)**2+(q1-q2)**2+(2*math.sin(I/2))**2+(((e1+e2)/2)*2*math.sin(P/2))**2)

@dataclass
class Rec:
 url:str;status:int|None;final_url:str|None;content_type:str|None;bytes:int;sha256:str|None;error:str|None

def fetch(url,path=None):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'*/*'})
  with urllib.request.urlopen(req,timeout=90) as r:
   raw=r.read(64*1024*1024+1)
   if len(raw)>64*1024*1024:raise RuntimeError('response too large')
   rec=Rec(url,getattr(r,'status',200),r.geturl(),r.headers.get('Content-Type'),len(raw),hashlib.sha256(raw).hexdigest(),None)
   if path:Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(raw)
   return raw,rec
 except Exception as exc:
  return None,Rec(url,getattr(exc,'code',None),None,None,0,None,f'{type(exc).__name__}: {exc}')

class Links(HTMLParser):
 def __init__(self):super().__init__();self.items=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k.lower() in {'href','src','action','data-url','data-href','download'} and v:self.items.append({'tag':tag.lower(),'attribute':k.lower(),'value':v})

def table(raw):
 text=raw.decode('utf-8-sig','replace');low=text.lstrip().lower()
 if low.startswith('<!doctype') or low.startswith('<html') or '<body' in low[:2000]:raise ValueError('HTML response')
 lines=[x for x in text.splitlines() if x.strip() and not x.lstrip().startswith('#')]
 if len(lines)<2:raise ValueError('too few rows')
 sample='\n'.join(lines[:50]);delim=max((';',',','\t','|'),key=sample.count)
 if sample.count(delim)==0:raise ValueError('no delimiter')
 mat=[r for r in csv.reader(lines,delimiter=delim) if any(c.strip() for c in r)]
 hi=0
 for i,row in enumerate(mat[:10]):
  keys={norm(c) for c in row};hits=sum(any(k in a for a in ALIASES.values()) for k in keys)
  if hits>=3:hi=i;break
 hdr=[c.strip() or f'c{j}' for j,c in enumerate(mat[hi])];rows=[]
 for rr in mat[hi+1:]:
  rr=rr+['']*(len(hdr)-len(rr));rows.append({h:rr[j].strip() for j,h in enumerate(hdr)})
 cols={}
 for target,aliases in ALIASES.items():
  m=[h for h in hdr if norm(h) in aliases]
  if len(m)==1:cols[target]=m[0]
 return rows,{'delimiter':delim,'header_index':hi,'headers':hdr,'columns':cols}

def metrics(rows,meta,sol):
 cols=meta['columns'];unique=len({json.dumps(r,sort_keys=True) for r in rows});geo=[]
 for r in rows:
  p={k:num(r.get(cols.get(k,''))) for k in ('sol','ra','dec','vg')}
  if all(v is not None for v in p.values()):geo.append(p)
 out={'row_count':len(rows),'unique_row_count':unique,'geo_complete_rows':len(geo),'geo_complete_fraction':len(geo)/len(rows) if rows else 0,**meta}
 if geo:
  sm=mednear([r['sol'] for r in geo],sol['sol']);rm=mednear([r['ra'] for r in geo],sol['ra']);dm=median(r['dec'] for r in geo);vm=median(r['vg'] for r in geo)
  out.update(sol_median=sm,ra_median=rm,dec_median=dm,vg_median=vm,sol_delta_deg=abs(cdelta(sm,sol['sol'])),radiant_separation_deg=sep(rm,dm,sol['ra'],sol['dec']),speed_delta_km_s=abs(vm-sol['vg']))
 orb=[]
 for r in rows:
  p={k:num(r.get(cols.get(k,''))) for k in ('q','e','inc','peri','node')}
  if all(v is not None for v in p.values()):orb.append(p)
 out['orbit_complete_rows']=len(orb);out['orbit_complete_fraction']=len(orb)/len(rows) if rows else 0
 if orb:
  om={'q':median(r['q'] for r in orb),'e':median(r['e'] for r in orb),'inc':median(r['inc'] for r in orb),'peri':mednear([r['peri'] for r in orb],sol['peri']),'node':mednear([r['node'] for r in orb],sol['node'])}
  out['orbit_median']=om;out['orbit_median_d_sh_to_solution004']=dsh(om,{k:sol[k] for k in om})
 return out

def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--cache',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.cache.mkdir(parents=True,exist_ok=True);a.output.mkdir(parents=True,exist_ok=True)
 mraw,mrec=fetch(MDC,a.cache/'streamfulldata.json');payload=json.loads(mraw)
 shower=next(x for x in payload['data'] if int(x['IAUNo'])==149);rawsol=next(x for x in shower['solution'] if str(x['AdNo']).zfill(3)=='004')
 sol={'filename':rawsol.get('LT'),'N':num(rawsol.get('N')),'sol':num(rawsol.get('LoS')),'sol_begin':num(rawsol.get('LoSb')),'sol_end':num(rawsol.get('LoSe')),'ra':num(rawsol.get('Ra')),'dec':num(rawsol.get('De')),'vg':num(rawsol.get('Vg')),'a':num(rawsol.get('a')),'q':num(rawsol.get('q')),'e':num(rawsol.get('e')),'peri':num(rawsol.get('peri')),'node':num(rawsol.get('node')),'inc':num(rawsol.get('inc')),'group':rawsol.get('Group'),'references':rawsol.get('References')}
 draw,drec=fetch(DETAIL,a.cache/'nop_detail.html');draw=draw or b'';p=Links();p.feed(draw.decode('utf-8','replace'))
 scripts=[];srecs=[]
 for idx,item in enumerate([x for x in p.items if x['tag']=='script' and x['attribute']=='src'][:30]):
  u=urllib.parse.urljoin(DETAIL,item['value'])
  if urllib.parse.urlparse(u).netloc!=urllib.parse.urlparse(BASE).netloc:continue
  r,rec=fetch(u,a.cache/'scripts'/f'{idx:02d}.js');srecs.append(asdict(rec));
  if r:scripts.append((u,r))
 inv=list(p.items)
 for u,r in scripts:
  for m in re.finditer(r'(?:https?://[^\"\'\s<>]+|[^\"\'\s<>]+\.csv(?:\?[^\"\'\s<>]*)?)',r.decode('utf-8','replace'),re.I):inv.append({'tag':'script-text','attribute':'regex','value':m.group(0)})
 candidates=set();dirs={BASE,DETAIL}
 for x in inv:
  u=urllib.parse.urljoin(DETAIL,html.unescape(x['value']).strip());z=urllib.parse.urlparse(u)
  if z.netloc==urllib.parse.urlparse(BASE).netloc:
   dirs.add(urllib.parse.urlunparse((z.scheme,z.netloc,z.path.rsplit('/',1)[0]+'','','','')))
   if FILENAME.lower() in x['value'].lower() or z.path.lower().endswith('.csv'):candidates.add(u)
 for d in dirs:candidates.add(urllib.parse.urljoin(d,FILENAME))
 for x in FIXED:candidates.add(urllib.parse.urljoin(BASE,x))
 attempts=[];selected=None;selected_raw=None
 for u in sorted(candidates):
  r,rec=fetch(u);entry=asdict(rec)
  if r:
   try:
    rows,meta=table(r);met=metrics(rows,meta,sol);entry['table']=met
    if met['unique_row_count']>=500 and met['geo_complete_fraction']>=.95:selected={'url':u,'fetch':entry,'metrics':met};selected_raw=r;attempts.append(entry);break
   except Exception as exc:entry['parse_error']=f'{type(exc).__name__}: {exc}'
  attempts.append(entry)
 if selected_raw:(a.output/FILENAME).write_bytes(selected_raw)
 (a.output/'detail_link_inventory.json').write_text(json.dumps(inv,indent=2));(a.output/'fetch_attempts.json').write_text(json.dumps(attempts,indent=2))
 met=selected['metrics'] if selected else {}
 pg={'current_mdc_solution004_found':True,'lookup_filename_exact':sol['filename']==FILENAME,'detail_page_accessible':drec.status==200 and drec.bytes>0,'official_lookup_accessible':selected is not None,'at_least_500_unique_rows':met.get('unique_row_count',0)>=500,'geo_complete_fraction_at_least_0_95':met.get('geo_complete_fraction',0)>=.95,'solar_longitude_reproduces_solution_within_3deg':met.get('sol_delta_deg',999)<=3,'radiant_reproduces_solution_within_3deg':met.get('radiant_separation_deg',999)<=3,'speed_reproduces_solution_within_2kms':met.get('speed_delta_km_s',999)<=2}
 og={'orbit_columns_present':all(k in met.get('columns',{}) for k in ('q','e','inc','peri','node')),'orbit_complete_fraction_at_least_0_90':met.get('orbit_complete_fraction',0)>=.9,'orbit_median_reproduces_solution_d_sh_at_most_0_08':met.get('orbit_median_d_sh_to_solution004',999)<=.08}
 obs=all(pg.values());verdict='PROCEED_TO_EXACT_SOLUTION004_DYNAMICS' if obs and all(og.values()) else ('SOLUTION004_OBSERVATIONALLY_COHERENT_BUT_NO_ORBIT_CLONES' if obs else 'KILL_SOLUTION004_COMPARISON_PROVENANCE')
 out={'verdict':verdict,'mdc_version':payload.get('version'),'mdc_fetch':asdict(mrec),'detail_fetch':asdict(drec),'script_fetches':srecs,'solution004':sol,'raw_solution004':rawsol,'candidate_url_count':len(candidates),'selected_lookup':selected,'provenance_gates':pg,'orbit_gates':og}
 (a.output/'solution004_audit.json').write_text(json.dumps(out,indent=2))
 lines=['# NOP solution 004 provenance and coherence audit','',f'- MDC version: **{payload.get("version")}**',f'- detail page status: **{drec.status}**',f'- attempted URLs: **{len(attempts)}**']
 if selected:lines += [f'- selected URL: `{selected["url"]}`',f'- unique rows: **{met["unique_row_count"]}**',f'- geocentric completeness: **{met["geo_complete_fraction"]:.4f}**',f'- solar-longitude delta: **{met.get("sol_delta_deg",math.nan):.4f}°**',f'- radiant separation: **{met.get("radiant_separation_deg",math.nan):.4f}°**',f'- speed delta: **{met.get("speed_delta_km_s",math.nan):.4f} km/s**',f'- orbit completeness: **{met.get("orbit_complete_fraction",0):.4f}**']
 lines += ['','## Observation/provenance gates','']+[f'- {"PASS" if v else "FAIL"} — `{k}`' for k,v in pg.items()]+['','## Orbit-clone gates','']+[f'- {"PASS" if v else "FAIL"} — `{k}`' for k,v in og.items()]+['',f'Verdict: **{verdict}**','']
 (a.output/'SOLUTION004_AUDIT_REPORT.md').write_text('\n'.join(lines));print('\n'.join(lines))
if __name__=='__main__':main()
