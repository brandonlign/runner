#!/usr/bin/env python3
"""Fast standard-library HPSC1 control probe through VizieR ASU-TSV.
Known published controls only. HPSC2 is never queried.
"""
from pathlib import Path
import urllib.parse,urllib.request,csv,io,json,math
OUT=Path('results/hetdex_xmpg_vizier_fast_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
C=[('O3ELG1',31.0511,-0.2286,.0780),('O3ELG2',8.2826,-.1793,.0780),('O3ELG3',6.0817,-.0720,.0840),('O3ELG4a',9.8204,-.0121,.0820),('O3ELG5',9.7674,.0360,.0830),('O3ELG6',13.4199,.0403,.0700),('O3ELG7',32.9842,.0585,.0960),('O3ELG8',31.8456,.1995,.0630),('O3ELG9',203.8739,51.0155,.0620),('O3ELG10',197.6288,51.0607,.0330),('O3ELG11',176.0732,51.1047,.0840),('O3ELG12a',200.1701,51.1910,.0730),('O3ELG12b',200.1696,51.1921,.0730),('O3ELG13',172.8717,51.2003,.0650),('O3ELG14',176.4366,51.2577,.0900),('O3ELG15',212.7970,51.2664,.0270),('O3ELG16',168.1299,51.8901,.0710)]
REST={'oii':3727.,'hgamma':4340.47,'oiii4363':4363.21,'hbeta':4861.33,'oiii4959':4958.91,'oiii5007':5006.84}
ROOTS=['https://vizier.cfa.harvard.edu/viz-bin/asu-tsv','https://vizier.cds.unistra.fr/viz-bin/asu-tsv']
def query(cat,ra,dec):
 params={'-source':cat,'-c':f'{ra} {dec}','-c.rs':'3','-out.all':'','-out.max':'200'}
 last=None
 for root in ROOTS:
  try:
   url=root+'?'+urllib.parse.urlencode(params)
   req=urllib.request.Request(url,headers={'User-Agent':'ISEF-HETDEX-XMPG/1.0'})
   with urllib.request.urlopen(req,timeout=45) as r: txt=r.read().decode('utf-8','replace')
   lines=[x for x in txt.splitlines() if x and not x.startswith('#')]
   # ASU TSV has header, units, dashes then data.
   if not lines:return []
   hdr=lines[0].split('\t');data=[]
   for line in lines[1:]:
    vals=line.split('\t')
    if len(vals)!=len(hdr):continue
    if all(set(v.strip())<=set('- ') for v in vals):continue
    # skip unit row heuristically
    if any(v.startswith('[') or v in ('deg','arcsec','Angstrom') for v in vals):continue
    data.append(dict(zip(hdr,vals)))
   return data
  except Exception as e:last=e
 raise last
def f(row,names):
 for n in names:
  for k,v in row.items():
   if k.lower().replace('_','').replace('-','')==n.lower().replace('_','').replace('-',''):return v
 return None
def num(x):
 try:return float(x)
 except:return None
def main():
 out={'status':'DEVELOPMENT_ONLY','hpsc2_new_opened':False,'success':False,'controls':[]}
 try:
  for lab,ra,dec,zpub in C:
   src=query('J/ApJ/943/177/sources',ra,dec);det=query('J/ApJ/943/177/detinfo',ra,dec)
   rec={'label':lab,'published_z':zpub,'inside_primary_z':.005<=zpub<=.085,'source_rows':len(src),'det_rows':len(det)}
   z=zpub
   if src:
    zz=num(f(src[0],['zHETDEX','z_hetdex']));z=zz if zz is not None else z
    rec['catalog_z']=zz;rec['source_type']=f(src[0],['Type','source_type']);rec['source_id']=f(src[0],['SourceID','source_id'])
   rec['expected_lines']={}
   for name,rw in REST.items():
    want=rw*(1+z);cand=[]
    for r in det:
     w=num(f(r,['Wave','wave','wavelength']))
     if w is not None and abs(w-want)<=8:
      cand.append((abs(w-want),{'wave':w,'sn':num(f(r,['S/N','SNR','sn'])),'flux':num(f(r,['Flux','flux'])),'line_id':f(r,['Line','line_id','lineID'])}))
    rec['expected_lines'][name]=min(cand,key=lambda x:x[0])[1] if cand else None
   out['controls'].append(rec)
  out['n_controls_with_source_rows']=sum(r['source_rows']>0 for r in out['controls']);out['n_controls_with_det_rows']=sum(r['det_rows']>0 for r in out['controls']);out['n_catalog_4363']=sum(r['expected_lines']['oiii4363'] is not None for r in out['controls']);out['n_primary_catalog_4363']=sum(r['inside_primary_z'] and r['expected_lines']['oiii4363'] is not None for r in out['controls']);out['success']=True
 except Exception as e:out['error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
