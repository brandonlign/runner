#!/usr/bin/env python3
"""Repository-history scientific-freshness audit for EDMOND 2009/2010."""
from __future__ import annotations
import json,re,subprocess
from pathlib import Path
OUT=Path('output'); OUT.mkdir(exist_ok=True)
TARGETS=(2009,2010)
SELF=('orbittrace_multiplicity_edmond_2009_2010_freshness_audit/','.github/workflows/orbittrace-multiplicity-edmond-2009-2010-freshness-audit')

def cmd(*a): return subprocess.check_output(a,text=True,stderr=subprocess.DEVNULL)
def refs(): return [x for x in cmd('git','for-each-ref','--format=%(refname)','refs/remotes/origin').splitlines() if x and not x.endswith('/HEAD')]
def grep(ref,pat):
 p=subprocess.run(['git','grep','-n','-I','-E',pat,ref,'--'],text=True,capture_output=True)
 if p.returncode not in (0,1): raise RuntimeError(p.stderr)
 out=[]; pref=ref+':'
 for line in p.stdout.splitlines():
  if not line.startswith(pref): continue
  parts=line[len(pref):].split(':',2)
  if len(parts)!=3: continue
  path,ln,text=parts
  if path.startswith(SELF): continue
  out.append({'ref':ref,'path':path,'line':int(ln),'text':text[:800]})
 return out
def dedup(xs):
 seen=set(); out=[]
 for x in xs:
  k=(x['path'],x['line'],x['text'])
  if k not in seen: seen.add(k); out.append(x)
 return out
def years_in_range(t):
 s=set()
 for m in re.finditer(r'range\(\s*(\d{4})\s*,\s*(\d{4})\s*\)',t):
  a,b=map(int,m.groups()); s.update(range(a,b))
 return s
def classify(h,y):
 p=h['path'].lower(); t=h['text'].lower(); yrs=years_in_range(h['text'])
 if 'range(' in h['text'] and y not in yrs: return 'range_excludes_target'
 if any(k in t for k in ('untouched','reserved','must not access','must not download','not downloaded','no edmond','no scientific','unread')): return 'reservation_only'
 if 'edmond2017_external' in p and str(y) not in t: return 'unrelated_2017_protocol'
 if 'edmond' not in p and 'edmond' not in t: return 'unrelated_year'
 return 'potential_exposure'
def hits_for(rs,y):
 pats=[rf'iaumdcedmond{y}',rf'EDMOND[^\n]{{0,140}}{y}|{y}[^\n]{{0,140}}EDMOND',r'EDMOND[^\n]{0,160}range\([^\n]{0,80}\)|range\([^\n]{0,80}\)[^\n]{0,160}EDMOND']
 xs=[]
 for r in rs:
  for pat in pats: xs += grep(r,pat)
 xs=dedup(xs)
 for h in xs: h['classification']=classify(h,y); h['dynamic_range_years']=sorted(years_in_range(h['text']))
 return xs
def main():
 rs=refs(); targets={}
 for y in TARGETS:
  hs=hits_for(rs,y); targets[str(y)]={'hits':hs,'potential_exposure_hits':[h for h in hs if h['classification']=='potential_exposure']}
 # 2017 is a positive control: explicit external-confirmation source/protocol must be found.
 pc=[]
 for r in rs:
  pc += grep(r,r'(iaumdcedmond2017|EDMOND[^\n]{0,140}2017|2017[^\n]{0,140}EDMOND)')
 pc=dedup(pc)
 pc_actual=any('edmond2017_external/' in h['path'] for h in pc)
 clean=all(not targets[str(y)]['potential_exposure_hits'] for y in TARGETS)
 verdict='PASS_EDMOND_2009_2010_REPO_SCIENTIFIC_FRESHNESS_AUDIT' if clean and pc_actual else 'FAIL_EDMOND_2009_2010_REPO_SCIENTIFIC_FRESHNESS_AUDIT'
 result={'verdict':verdict,'refs_scanned':len(rs),'catalogue_access_this_audit':False,'scientific_value_access_this_audit':False,'label_access_this_audit':False,'target_information_access':False,'targets':targets,'positive_control_2017_spent_detected':pc_actual,'positive_control_2017_hit_count':len(pc),'claim_boundary':'History-only audit; a pass authorizes only a separate structure-only archive audit before any EDMOND 2009/2010 scientific value or stream-label access.'}
 (OUT/'edmond_2009_2010_repo_freshness_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps(result,indent=2,sort_keys=True))
 if verdict.startswith('FAIL_'): raise SystemExit(1)
if __name__=='__main__': main()
