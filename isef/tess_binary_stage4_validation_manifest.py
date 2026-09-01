#!/usr/bin/env python3
"""Build the Stage-4 external validation control panel using metadata only.

No TSSYS .lc light curve is requested. The 57 positive object numbers are read
from the already-frozen metadata inventory produced before Stage-4 development;
they are not redefined from a live webpage. Four unique controls are matched to
each frozen positive by sector, TESS magnitude, and cadence count, while
excluding current confirmed/probable, possible-reported, contact-binary, all
frozen positives, and all Stage-3 consumed objects.
"""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUT=Path('results/tess_binary_stage4_validation_manifest'); OUT.mkdir(parents=True,exist_ok=True)
MERGE='https://archive.konkoly.hu/pub/tssys/dr1/release.merge'
CONFIRMED='https://www.johnstonsarchive.net/astro/asteroidmoons.html'
POSSIBLE='https://www.johnstonsarchive.net/astro/asteroidmoonsq.html'
CONTACT='https://www.johnstonsarchive.net/astro/contactbinast.html'
CONTROL_OLD=Path(__file__).with_name('tess_binary_stage3_null_controls.txt')
POSITIVE_FILE=Path(__file__).with_name('tess_binary_stage4_positive_manifest.txt')
CONSUMED_POS={1803,6764}
ANCHOR_RE=re.compile(r'^\s*\(([0-9]{1,7})\)\s+(.+?)\s*$')
ANY_NUM_RE=re.compile(r'\(([0-9]{1,7})\)')
N_CONTROL_PER_POSITIVE=4
MIN_N_GOOD=200
FROZEN_POSITIVE_SOURCE_HASHES={
  'tssys_release_merge_sha256':'c2bca0b63d8210392ff1c6ace8a2e7af7c322ee675a26313093511855652dab4',
  'johnston_page_sha256':'4f7320c10bca5289f7820d78a66c436373de2ca4614b53b83fd0168e3b4e0173',
  'inventory_artifact_zip_sha256':'1c7b2e48fff1a49bf9460a65240d6af769d831331d97e7ffec2b2a5f3379c9c2',
  'inventory_artifact_id':'9780515232',
  'inventory_run':'33453273610'
}


def get(url):
    r=requests.get(url,timeout=120,headers={'User-Agent':'ISEF-stage4-metadata-manifest/1.1'}); r.raise_for_status(); return r.text


def parse_merge(text):
    rows=[]
    for raw in text.splitlines():
        p=raw.split()
        if len(p)<12 or not p[0].isdigit(): continue
        try:
            rows.append({'number':int(p[0]),'frequency_cpd':float(p[1]),'lc_type':p[2],'period_h':float(p[3]),
              'amplitude_mag':float(p[4]),'n_good':int(p[5]),'sector':int(p[6]),'camera':int(p[7]),'ccd':int(p[8]),
              'median_tess_mag':float(p[9]),'expected_tess_mag':float(p[10]),'H':float(p[11])})
        except Exception: pass
    return rows


def confirmed_numbers(html):
    soup=BeautifulSoup(html,'html.parser'); out=set()
    for a in soup.find_all('a'):
        text=' '.join(a.get_text(' ',strip=True).split()); m=ANCHOR_RE.match(text)
        if m: out.add(int(m.group(1)))
    return out


def all_number_mentions(html):
    text=BeautifulSoup(html,'html.parser').get_text(' ',strip=True)
    return {int(x) for x in ANY_NUM_RE.findall(text)}


def cost(p,c):
    dm=abs(float(c['median_tess_mag'])-float(p['median_tess_mag']))
    dn=abs(math.log(max(c['n_good'],1)/max(p['n_good'],1)))
    return (dm + 0.75*dn, dm, dn, int(c['number']))


def main():
    frozen_positive_numbers=[int(x) for x in POSITIVE_FILE.read_text().split()]
    if len(frozen_positive_numbers)!=57 or len(set(frozen_positive_numbers))!=57:
        raise RuntimeError('frozen positive manifest is not exactly 57 unique objects')
    merge=get(MERGE); conf=get(CONFIRMED); poss=get(POSSIBLE); contact=get(CONTACT)
    rows=parse_merge(merge); by={z['number']:z for z in rows}
    missing=[n for n in frozen_positive_numbers if n not in by]
    if missing: raise RuntimeError(f'frozen positives missing from current TSSYS metadata: {missing}')
    positives=[dict(by[n]) for n in frozen_positive_numbers]
    confirmed=confirmed_numbers(conf)
    old_controls={int(x) for x in CONTROL_OLD.read_text().split()}
    consumed=old_controls|CONSUMED_POS
    excluded_binaryish=(confirmed|all_number_mentions(poss)|all_number_mentions(contact)|consumed|set(frozen_positive_numbers))
    pool=[z for z in rows if z['number'] not in excluded_binaryish and z['n_good']>=MIN_N_GOOD]
    used=set(); matches=[]
    for p in positives:
        same=[c for c in pool if c['sector']==p['sector'] and c['number'] not in used]
        same.sort(key=lambda c:cost(p,c))
        chosen=same[:N_CONTROL_PER_POSITIVE]
        if len(chosen)!=N_CONTROL_PER_POSITIVE:
            raise RuntimeError(f'insufficient same-sector controls for positive {p["number"]}')
        for c in chosen: used.add(c['number'])
        matches.append({'positive':p,'controls':[dict(c) for c in chosen],'costs':[cost(p,c) for c in chosen]})
    controls=[c for m in matches for c in m['controls']]
    if len(controls)!=57*N_CONTROL_PER_POSITIVE or len({c['number'] for c in controls})!=len(controls):
        raise RuntimeError('control matching cardinality/uniqueness failure')
    (OUT/'positives.txt').write_text('\n'.join(str(z['number']) for z in positives)+'\n')
    (OUT/'controls.txt').write_text('\n'.join(str(z['number']) for z in controls)+'\n')
    rep={'role':'Stage-4 metadata-only frozen external-validation manifest','lightcurve_values_opened':False,
         'positive_n':len(positives),'control_n':len(controls),'controls_per_positive':N_CONTROL_PER_POSITIVE,
         'positive_definition':'exact 57-object list frozen by metadata-only inventory artifact 9780515232; live page drift cannot change membership',
         'frozen_positive_source_hashes':FROZEN_POSITIVE_SOURCE_HASHES,
         'matching':'unique same-sector nearest neighbors on |median TESS mag difference| + 0.75*|log(n_good ratio)|; no period/amplitude/lc-type matching',
         'control_exclusions':'all numbers mentioned on current Johnston confirmed/probable, possible-report, or contact-binary pages; all frozen positives; all Stage-3 consumed objects',
         'sources':{'merge':MERGE,'confirmed':CONFIRMED,'possible':POSSIBLE,'contact':CONTACT},
         'current_source_sha256':{'merge':hashlib.sha256(merge.encode()).hexdigest(),'confirmed':hashlib.sha256(conf.encode()).hexdigest(),
                          'possible':hashlib.sha256(poss.encode()).hexdigest(),'contact':hashlib.sha256(contact.encode()).hexdigest()},
         'positives':positives,'controls':controls,'matches':matches}
    (OUT/'manifest.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'positive_n':len(positives),'control_n':len(controls),'positive_numbers':[z['number'] for z in positives],
      'control_numbers':[z['number'] for z in controls],'current_source_sha256':rep['current_source_sha256']},indent=2))

if __name__=='__main__': main()
